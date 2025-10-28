import csv
import threading
import traceback
from io import StringIO

from flask import g, redirect, request

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import null

from chellow.dloads import open_file
from chellow.e.computer import SupplySource, forecast_date
from chellow.models import Channel, Era, HhDatum, RSession, Supply, User
from chellow.utils import (
    csv_make_val,
    ct_datetime,
    hh_range,
    parse_mpan_core,
    req_bool,
    req_checkbox,
    req_date,
    req_int,
    req_str,
    to_ct,
    to_utc,
)


def _write_row(writer, titles, vals, total):
    vals["total"] = total
    writer.writerow(csv_make_val(vals[t]) for t in titles)


def content(
    start_date,
    finish_date,
    imp_related,
    channel_type,
    is_zipped,
    supply_id,
    mpan_cores,
    user_id,
):
    finish_date_ct = to_ct(finish_date)
    zf = sess = tf = None
    base_name = ["supplies_hh_data", finish_date_ct.strftime("%Y%m%d%H%M")]
    cache = {}
    try:
        with RSession() as sess:
            supplies = (
                select(Supply)
                .join(Era)
                .where(
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                    Era.start_date <= finish_date,
                )
                .order_by(Supply.id)
                .distinct()
            )
            if supply_id is not None:
                supply = Supply.get_by_id(sess, supply_id)
                supplies = supplies.where(Supply.id == supply.id)
                first_era = sess.scalars(
                    select(Era)
                    .where(
                        Era.supply == supply,
                        or_(Era.finish_date == null(), Era.finish_date >= start_date),
                        Era.start_date <= finish_date,
                    )
                    .order_by(Era.start_date)
                ).first()
                if first_era.imp_mpan_core is None:
                    name_core = first_era.exp_mpan_core
                else:
                    name_core = first_era.imp_mpan_core
                base_name.append("supply_" + name_core.replace(" ", "_"))

            if mpan_cores is not None:
                supplies = supplies.where(
                    or_(
                        Era.imp_mpan_core.in_(mpan_cores),
                        Era.exp_mpan_core.in_(mpan_cores),
                    )
                )
                base_name.append("filter")

            cf = StringIO()
            writer = csv.writer(cf, lineterminator="\n")
            headers = [
                "import_mpan_core",
                "export_mpan_core",
                "is_hh",
                "is_import_related",
                "channel_type",
                "hh_start_clock_time",
                "total",
            ]
            slot_names = [str(n) for n in range(1, 51)]
            titles = headers + slot_names
            writer.writerow(titles)
            titles_csv = cf.getvalue()
            cf.close()
            fdate = forecast_date()
            user = User.get_by_id(sess, user_id)

            if is_zipped:
                zf = open_file(
                    "_".join(base_name) + ".zip", user, mode="w", is_zip=True
                )
            else:
                tf = open_file("_".join(base_name) + ".csv", user, mode="w", newline="")
                tf.write(titles_csv)

            for supply in sess.execute(supplies).scalars():
                cf = StringIO()
                writer = csv.writer(cf, lineterminator="\n")
                imp_mpan_core = exp_mpan_core = is_hh = None
                data = []
                for era in sess.scalars(
                    select(Era)
                    .where(
                        Era.supply == supply,
                        or_(Era.finish_date == null(), Era.finish_date >= start_date),
                        Era.start_date <= finish_date,
                    )
                    .order_by(Era.start_date)
                ):
                    if era.imp_mpan_core is not None:
                        imp_mpan_core = era.imp_mpan_core
                    if era.exp_mpan_core is not None:
                        exp_mpan_core = era.exp_mpan_core

                    if era.pc.code == "00" or len(era.channels) > 0:
                        is_hh = True
                        for datum in sess.scalars(
                            select(HhDatum)
                            .join(Channel)
                            .join(Era)
                            .where(
                                Era.supply == supply,
                                HhDatum.start_date >= start_date,
                                HhDatum.start_date <= finish_date,
                                Channel.imp_related == imp_related,
                                Channel.channel_type == channel_type,
                            )
                            .order_by(HhDatum.start_date)
                        ):
                            data.append((datum.start_date, datum.value))
                    else:
                        is_hh = False
                        ds = SupplySource(
                            sess,
                            start_date,
                            finish_date,
                            fdate,
                            era,
                            imp_related,
                            cache,
                        )
                        KEY_LOOKUP = {
                            "ACTIVE": "msp-kwh",
                            "REACTIVE_IMP": "imp-msp-kvarh",
                            "REACTIVE_EXP": "exp-msp-kvarh",
                        }
                        for hh in ds.hh_data:
                            data.append(
                                (hh["start-date"], hh[KEY_LOOKUP[channel_type]])
                            )

                vals = total = slot_count = None
                hh_data = iter(data)
                datum = next(hh_data, None)
                for current_date in hh_range(cache, start_date, finish_date):
                    dt_ct = to_ct(current_date)
                    if dt_ct.hour == 0 and dt_ct.minute == 0:
                        if vals is not None:
                            _write_row(writer, titles, vals, total)

                        vals = {
                            "import_mpan_core": imp_mpan_core,
                            "export_mpan_core": exp_mpan_core,
                            "is_hh": is_hh,
                            "is_import_related": imp_related,
                            "channel_type": channel_type,
                            "hh_start_clock_time": dt_ct.strftime("%Y-%m-%d"),
                        }
                        for slot_name in slot_names:
                            vals[slot_name] = None
                        total = slot_count = 0

                    slot_count += 1
                    if datum is not None and datum[0] == current_date:
                        val = datum[1]
                        vals[str(slot_count)] = val
                        total += val
                        datum = next(hh_data, None)

                if vals is not None:
                    _write_row(writer, titles, vals, total)

                if is_zipped:
                    fname = f"{imp_mpan_core}_{exp_mpan_core}_{supply.id}.csv".replace(
                        " ", "_"
                    )
                    zf.writestr(fname, titles_csv + cf.getvalue())
                else:
                    tf.write(cf.getvalue())
                cf.close()

                # Avoid long-running transaction
                sess.rollback()

            if is_zipped:
                zf.close()
            else:
                tf.close()

    except BaseException:
        msg = traceback.format_exc()
        print(msg)
        if is_zipped:
            zf.writestr("error.txt", msg)
            zf.close()
        else:
            tf.write(msg)


def do_get(sess):
    return handle_request()


def do_post(sess):
    if "mpan_cores" in request.values:
        mpan_cores_str = req_str("mpan_cores")
        mpan_cores = mpan_cores_str.splitlines()
        if len(mpan_cores) == 0:
            mpan_cores = None
        else:
            for i in range(len(mpan_cores)):
                mpan_cores[i] = parse_mpan_core(mpan_cores[i])
    return handle_request(mpan_cores)


def handle_request(mpan_cores=None):
    start_date = req_date("start", resolution="day")

    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    finish_day = req_int("finish_day")

    finish_date = to_utc(ct_datetime(finish_year, finish_month, finish_day, 23, 30))

    imp_related = req_bool("imp_related")
    channel_type = req_str("channel_type")
    is_zipped = req_checkbox("is_zipped")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None
    user = g.user
    args = (
        start_date,
        finish_date,
        imp_related,
        channel_type,
        is_zipped,
        supply_id,
        mpan_cores,
        user.id,
    )
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
