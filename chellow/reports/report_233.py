import csv
import sys
import threading
import traceback

from dateutil.relativedelta import relativedelta

from flask import g

from sqlalchemy.sql.expression import false, select, true

from chellow.dloads import open_file
from chellow.models import (
    Channel,
    Contract,
    Era,
    Session,
    Site,
    SiteEra,
    Snag,
    Supply,
    User,
)
from chellow.utils import csv_make_val, hh_before, req_bool, req_int, utc_datetime_now
from chellow.views import chellow_redirect


def content(contract_id, days_hidden, is_ignored, user_id):
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("channel_snags.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            titles = (
                "Hidden Days",
                "Chellow Id",
                "Imp MPAN Core",
                "Exp MPAN Core",
                "Site Code",
                "Site Name",
                "Snag Description",
                "Import Related?",
                "Channel Type",
                "Start Date",
                "Finish Date",
                "Is Ignored?",
                "Days Since Snag Finished",
                "Duration Of Snag (Days)",
            )
            writer.writerow(titles)

            contract = Contract.get_dc_by_id(sess, contract_id)

            now = utc_datetime_now()
            cutoff_date = now - relativedelta(days=days_hidden)
            q = (
                select(Snag, Channel, Era, Supply, SiteEra, Site)
                .join(Channel, Snag.channel_id == Channel.id)
                .join(Era, Channel.era_id == Era.id)
                .join(Supply, Era.supply_id == Supply.id)
                .join(SiteEra, Era.site_eras)
                .join(Site, SiteEra.site_id == Site.id)
                .where(
                    SiteEra.is_physical == true(),
                    Era.dc_contract == contract,
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
            )
            if not is_ignored:
                q = q.where(Snag.is_ignored == false())

            for snag, channel, era, supply, site_era, site in sess.execute(q):
                snag_start = snag.start_date
                snag_finish = snag.finish_date
                imp_mc = "" if era.imp_mpan_core is None else era.imp_mpan_core
                exp_mc = "" if era.exp_mpan_core is None else era.exp_mpan_core

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

                vals = {
                    "Hidden Days": days_hidden,
                    "Chellow Id": snag.id,
                    "Imp MPAN Core": imp_mc,
                    "Exp MPAN Core": exp_mc,
                    "Site Code": site.code,
                    "Site Name": site.name,
                    "Snag Description": snag.description,
                    "Import Related?": channel.imp_related,
                    "Channel Type": channel.channel_type,
                    "Start Date": snag_start,
                    "Finish Date": snag_finish,
                    "Is Ignored?": snag.is_ignored,
                    "Days Since Snag Finished": age_of_snag,
                    "Duration Of Snag (Days)": duration.days,
                }

                writer.writerow(csv_make_val(vals[t]) for t in titles)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    contract_id = req_int("dc_contract_id")
    days_hidden = req_int("days_hidden")
    is_ignored = req_bool("is_ignored")

    args = contract_id, days_hidden, is_ignored, g.user.id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
