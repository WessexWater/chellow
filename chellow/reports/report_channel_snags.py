import csv
import sys
import threading
import traceback

from dateutil.relativedelta import relativedelta

from flask import g, redirect, render_template, request

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import false, select, true

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.models import (
    Channel,
    Contract,
    Era,
    Party,
    RSession,
    Site,
    SiteEra,
    Snag,
    Supply,
    User,
)
from chellow.utils import (
    csv_make_val,
    hh_before,
    req_checkbox,
    req_date,
    req_int,
    req_int_none,
    req_str,
    utc_datetime_now,
)


def _make_rows(
    sess,
    now,
    contract,
    days_hidden,
    is_ignored,
    show_settlement,
    only_ongoing,
    days_long_hidden,
    limit=None,
):
    cutoff_date = now - relativedelta(days=days_hidden)
    q = (
        select(Snag, Channel, Era, Supply, SiteEra, Site, Contract)
        .join(Channel, Snag.channel_id == Channel.id)
        .join(Era, Channel.era_id == Era.id)
        .join(Supply, Era.supply_id == Supply.id)
        .join(SiteEra, Era.site_eras)
        .join(Site, SiteEra.site_id == Site.id)
        .join(Contract, Era.dc_contract_id == Contract.id)
        .where(
            SiteEra.is_physical == true(),
            Snag.start_date < cutoff_date,
        )
        .order_by(
            Site.code,
            Supply.id,
            Channel.imp_related,
            Channel.channel_type,
            Snag.description,
            Snag.start_date,
            Snag.id,
        )
        .options(joinedload(Era.dc_contract))
    )
    if contract is not None:
        q = q.where(Era.dc_contract == contract)

    if not is_ignored:
        q = q.where(Snag.is_ignored == false())

    if show_settlement == "yes":
        q = q.join(Party, Supply.dno_id == Party.id).where(Party.dno_code != "99")
    elif show_settlement == "no":
        q = q.join(Party, Supply.dno_id == Party.id).where(Party.dno_code == "99")
    elif show_settlement == "both":
        pass
    else:
        raise BadRequest("show_settlement must be 'yes', 'no' or 'both'.")

    snag_groups = []
    prev_snag = None
    for snag, channel, era, supply, site_era, site, contract in sess.execute(q):
        snag_start = snag.start_date
        snag_finish = snag.finish_date

        if snag_finish is None:
            duration = now - snag_start
            age_of_snag = None
        else:
            duration = snag_finish - snag_start
            if hh_before(cutoff_date, snag_finish):
                age_of_snag = None
            else:
                delta = now - snag_finish
                age_of_snag = delta.days

        if only_ongoing and age_of_snag is not None:
            continue

        if days_long_hidden is not None and duration < days_long_hidden:
            continue

        if (
            prev_snag is None
            or channel.era != prev_snag.channel.era
            or snag.start_date != prev_snag.start_date
            or snag.finish_date != prev_snag.finish_date
            or snag.description != prev_snag.description
        ):
            if limit is not None and len(snag_groups) > limit:
                break

            snag_group = {
                "snags": [],
                "site": site,
                "era": era,
                "supply": supply,
                "description": snag.description,
                "start_date": snag.start_date,
                "finish_date": snag.finish_date,
                "contract": contract,
                "contract_name": contract.name,
                "hidden_days": days_hidden,
                "chellow_id": snag.id,
                "imp_mpan_core": era.imp_mpan_core,
                "exp_mpan_core": era.exp_mpan_core,
                "site_code": site.code,
                "site_name": site.name,
                "snag_description": snag.description,
                "channel_type": channel.channel_type,
                "is_ignored": snag.is_ignored,
                "days_since_finished": age_of_snag,
                "duration": duration.days,
            }
            snag_groups.append(snag_group)
        snag_group["snags"].append(snag)
        prev_snag = snag

    def make_key(item):
        return item["duration"]

    snag_groups.sort(key=make_key, reverse=True)
    return snag_groups


def content(
    contract_id,
    days_hidden,
    is_ignored,
    user_id,
    only_ongoing,
    show_settlement,
    days_long_hidden,
    now,
):
    f = writer = None
    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)
            if contract_id is None:
                contract = None
                namef = "all"
            else:
                contract = Contract.get_dc_by_id(sess, contract_id)
                namef = contract.name

            f = open_file(f"channel_snags_{namef}.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            titles = (
                "contract",
                "hidden_days",
                "chellow_ids",
                "imp_mpan_core",
                "exp_mpan_core",
                "site_code",
                "site_name",
                "snag_description",
                "channel_types",
                "start_date",
                "finish_date",
                "is_ignored",
                "days_since_finished",
                "duration",
            )
            writer.writerow(titles)

            for snag_group in _make_rows(
                sess,
                now,
                contract,
                days_hidden,
                is_ignored,
                show_settlement,
                only_ongoing,
                days_long_hidden,
            ):

                vals = {
                    "contract": snag_group["contract"].name,
                    "hidden_days": days_hidden,
                    "chellow_ids": [snag.id for snag in snag_group["snags"]],
                    "imp_mpan_core": snag_group["imp_mpan_core"],
                    "exp_mpan_core": snag_group["exp_mpan_core"],
                    "site": snag_group["site"],
                    "site_code": snag_group["site"].code,
                    "site_name": snag_group["site"].name,
                    "snag_description": snag_group["description"],
                    "channel_types": [
                        f"{s.channel.imp_related}_{s.channel.channel_type}"
                        for s in snag_group["snags"]
                    ],
                    "start_date": snag_group["start_date"],
                    "finish_date": snag_group["finish_date"],
                    "is_ignored": snag_group["is_ignored"],
                    "days_since_finished": snag_group["days_since_finished"],
                    "duration": snag_group["duration"],
                }

                writer.writerow(csv_make_val(vals[t]) for t in titles)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


LIMIT = 200


def do_get(sess):
    contract_id = req_int_none("dc_contract_id")
    days_hidden = req_int("days_hidden")
    is_ignored = req_checkbox("is_ignored")
    only_ongoing = req_checkbox("only_ongoing")
    show_settlement = req_str("show_settlement")
    as_csv = req_checkbox("as_csv")
    days_long_hidden = req_int_none("days_long_hidden")
    if "now_year" in request.values:
        now = req_date("now")
    else:
        now = utc_datetime_now()

    if as_csv:
        args = (
            contract_id,
            days_hidden,
            is_ignored,
            g.user.id,
            only_ongoing,
            show_settlement,
            days_long_hidden,
            now,
        )
        threading.Thread(target=content, args=args).start()
        return redirect("/downloads", 303)
    else:
        if contract_id is None:
            contract = None
        else:
            contract = Contract.get_dc_by_id(sess, contract_id)
        now = utc_datetime_now()
        snag_groups = _make_rows(
            sess,
            now,
            contract,
            days_hidden,
            is_ignored,
            show_settlement,
            only_ongoing,
            days_long_hidden,
            limit=LIMIT,
        )
        return render_template(
            "reports/channel_snags.html",
            contract=contract,
            limit=LIMIT,
            snag_groups=snag_groups,
            days_hidden=days_hidden,
            is_ignored=is_ignored,
            only_ongoing=only_ongoing,
            show_settlement=show_settlement,
            days_long_hidden="" if days_long_hidden is None else days_long_hidden,
        )
