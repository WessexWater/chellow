import threading
import traceback
from datetime import datetime as Datetime

from flask import g, redirect, request

from sqlalchemy import null, or_, select, text, true

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.models import Era, Session, Site, SiteEra, Supply, User
from chellow.utils import (
    hh_format,
    hh_range,
    parse_mpan_core,
    req_bool,
    req_date,
    req_int,
    req_str,
    to_ct,
)


def csv_str(row):
    frow = []
    for cell in row:
        if cell is None:
            val = ""
        elif isinstance(cell, Datetime):
            val = hh_format(cell)
        else:
            val = str(cell)
        frow.append(val)

    return ",".join('"' + v + '"' for v in frow) + "\n"


def content(start_date, finish_date, supply_id, mpan_cores, is_zipped, user_id):
    file_extension = ".zip" if is_zipped else ".csv"

    base_name = (
        f'hh_data_row_{to_ct(start_date).strftime("%Y%m%d%H%M")}{file_extension}'
    )

    tls = ["Site Code", "Imp MPAN Core", "Exp Mpan Core", "HH Start Clock-Time"]
    for polarity in ("Import", "Export"):
        for suffix in (
            "ACTIVE kWh",
            "ACTIVE Status",
            "ACTIVE Modified",
            "REACTIVE_IMP kVArh",
            "REACTIVE_IMP Status",
            "REACTIVE_IMP Modified",
            "REACTIVE_EXP kVArh",
            "REACTIVE_EXP Status",
            "REACTIVE_EXP Modified",
        ):
            tls.append(polarity + " " + suffix)

    titles = csv_str(tls)
    tmp_file = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)

            if is_zipped:
                zf = open_file(base_name, user, mode="w", is_zip=True)
            else:
                tmp_file = open_file(base_name, user, mode="w")

            caches = {}
            supplies = (
                select(Supply)
                .join(Era)
                .where(
                    Era.start_date <= finish_date,
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                )
                .order_by(Supply.id)
                .distinct()
            )
            if supply_id is not None:
                sup = Supply.get_by_id(sess, supply_id)
                supplies = supplies.where(Era.supply == sup)

            if mpan_cores is not None:
                supplies = supplies.where(
                    or_(
                        Era.imp_mpan_core.in_(mpan_cores),
                        Era.exp_mpan_core.in_(mpan_cores),
                    )
                )

            if not is_zipped:
                tmp_file.write(titles)

            for supply in sess.scalars(supplies):
                site, era = (
                    sess.query(Site, Era)
                    .join(Era.site_eras)
                    .filter(
                        Era.supply == supply,
                        Era.start_date <= finish_date,
                        SiteEra.site_id == Site.id,
                        or_(Era.finish_date == null(), Era.finish_date >= start_date),
                        SiteEra.is_physical == true(),
                    )
                    .order_by(Era.id)
                    .first()
                )

                outs = []
                data = iter(
                    sess.execute(
                        text(
                            """
    select hh_base.start_date,
        max(imp_active.value), max(imp_active.status),
        max(imp_active.last_modified),
        max(imp_reactive_imp.value), max(imp_reactive_imp.status),
        max(imp_reactive_imp.last_modified),
        max(imp_reactive_exp.value), max(imp_reactive_exp.status),
        max(imp_reactive_exp.last_modified),
        max(exp_active.value), max(exp_active.status),
        max(exp_active.last_modified),
        max(exp_reactive_imp.value), max(imp_reactive_imp.status),
        max(exp_reactive_imp.last_modified),
        max(exp_reactive_exp.value), max(exp_reactive_exp.status),
        max(exp_reactive_exp.last_modified)
    from hh_datum hh_base
        join channel on hh_base.channel_id = channel.id
        join era on channel.era_id = era.id
        left join hh_datum imp_active
            on (imp_active.id = hh_base.id and channel.imp_related is true and
                channel.channel_type = 'ACTIVE')
        left join hh_datum imp_reactive_imp
            on (imp_reactive_imp.id = hh_base.id
                and channel.imp_related is true and
                channel.channel_type = 'REACTIVE_IMP')
        left join hh_datum imp_reactive_exp
            on (imp_reactive_exp.id = hh_base.id
                and channel.imp_related is true and
                channel.channel_type = 'REACTIVE_EXP')
        left join hh_datum exp_active
            on (exp_active.id = hh_base.id and channel.imp_related is false and
                channel.channel_type = 'ACTIVE')
        left join hh_datum exp_reactive_imp
                    on (exp_reactive_imp.id = hh_base.id
                        and channel.imp_related is
                    false and channel.channel_type = 'REACTIVE_IMP')
        left join hh_datum exp_reactive_exp
                    on (exp_reactive_exp.id = hh_base.id
                    and channel.imp_related is false
                    and channel.channel_type = 'REACTIVE_EXP')
    where supply_id = :supply_id
        and hh_base.start_date between :start_date and :finish_date
    group by hh_base.start_date
    order by hh_base.start_date
        """
                        ),
                        params={
                            "supply_id": supply.id,
                            "start_date": start_date,
                            "finish_date": finish_date,
                        },
                    )
                )
                datum = next(data, None)

                for dt in hh_range(caches, start_date, finish_date):
                    row = [site.code, era.imp_mpan_core, era.exp_mpan_core, dt]
                    if datum is not None:
                        (
                            hh_start_date,
                            imp_active,
                            imp_active_status,
                            imp_active_modified,
                            imp_reactive_imp,
                            imp_reactive_imp_status,
                            imp_reactive_imp_modified,
                            imp_reactive_exp,
                            imp_reactive_exp_status,
                            imp_reactive_exp_modified,
                            exp_active,
                            exp_active_status,
                            exp_active_modified,
                            exp_reactive_imp,
                            exp_reactive_imp_status,
                            exp_reactive_imp_modified,
                            exp_reactive_exp,
                            exp_reactive_exp_status,
                            exp_reactive_exp_modified,
                        ) = datum
                        if hh_start_date == dt:
                            datum = next(data, None)
                            row += [
                                imp_active,
                                imp_active_status,
                                imp_active_modified,
                                imp_reactive_imp,
                                imp_reactive_imp_status,
                                imp_reactive_imp_modified,
                                imp_reactive_exp,
                                imp_reactive_exp_status,
                                imp_reactive_exp_modified,
                                exp_active,
                                exp_active_status,
                                exp_active_modified,
                                exp_reactive_imp,
                                exp_reactive_imp_status,
                                exp_reactive_imp_modified,
                                exp_reactive_exp,
                                exp_reactive_exp_status,
                                exp_reactive_exp_modified,
                            ]

                    outs.append(csv_str(row))

                if is_zipped:
                    fnm = (
                        f"hh_data_row_{era.id}_{era.imp_mpan_core}_{era.exp_mpan_core}"
                    )
                    zf.writestr(fnm.replace(" ", "") + ".csv", titles + "".join(outs))
                else:
                    tmp_file.write("".join(outs))

                # Avoid a long-running transaction
                sess.rollback()
    except BaseException:
        msg = f"Problem {traceback.format_exc()}"
        print(msg)
        if is_zipped:
            zf.writestr("error.txt", msg)
        else:
            if tmp_file is not None:
                tmp_file.write(msg)
    finally:
        if is_zipped:
            zf.close()
        else:
            if tmp_file is not None:
                tmp_file.close()


def do_post(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None

    if "mpan_cores" in request.values:
        mpan_cores_str = req_str("mpan_cores")
        mpan_cores = mpan_cores_str.splitlines()
        if len(mpan_cores) == 0:
            mpan_cores = None
        else:
            for i in range(len(mpan_cores)):
                mpan_cores[i] = parse_mpan_core(mpan_cores[i])
    else:
        mpan_cores = None

    if finish_date < start_date:
        raise BadRequest("The finish date can't be before the start date.")

    is_zipped = req_bool("is_zipped")
    args = start_date, finish_date, supply_id, mpan_cores, is_zipped, g.user.id

    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
