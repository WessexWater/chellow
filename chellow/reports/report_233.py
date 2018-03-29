from datetime import datetime as Datetime
import datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy.sql.expression import true
import traceback
from chellow.models import (
    Contract, Snag, Channel, Era, Supply, SiteEra, Site, Session)
from chellow.utils import req_int
from chellow.views import chellow_redirect
import chellow.dloads
import csv
from flask import g
import threading
import sys
import os


def content(contract_id, days_hidden, user):
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'channel_snags.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                'Hidden Days', 'Chellow Id', 'Imp MPAN Core', 'Exp MPAN Core',
                'Site Code', 'Site Name', 'Snag Description',
                'Import Related?', 'Channel Type', 'Start Date', 'Finish Date',
                'Days Since Snag Finished', 'Duration Of Snag (Days)',
                'Is Ignored?'))

        contract = Contract.get_dc_by_id(sess, contract_id)

        now = Datetime.now(pytz.utc)
        cutoff_date = now - relativedelta(days=days_hidden)

        for snag, channel, era, supply, site_era, site in sess.query(
                Snag, Channel, Era, Supply, SiteEra, Site).join(
                Channel, Era, Supply, SiteEra, Site).filter(
                SiteEra.is_physical == true(), Era.dc_contract == contract,
                Snag.start_date < cutoff_date).order_by(
                Site.code, Supply.id, Channel.imp_related,
                Channel.channel_type, Snag.description,
                Snag.start_date, Snag.id):
            snag_start = snag.start_date
            snag_finish = snag.finish_date
            if snag_finish is None:
                snag_finish_str = ''
                duration = now - snag_start
                age_of_snag = datetime.timedelta(0)
            else:
                snag_finish_str = snag_finish.strftime("%Y-%m-%d %H:%M")
                duration = snag_finish - snag_start
                age_of_snag = now - snag_finish

            writer.writerow(
                (
                    str(days_hidden), str(snag.id),
                    '' if era.imp_mpan_core is None else era.imp_mpan_core,
                    '' if era.exp_mpan_core is None else era.exp_mpan_core,
                    site.code, site.name, snag.description,
                    str(channel.imp_related), channel.channel_type,
                    snag_start.strftime("%Y-%m-%d %H:%M"), snag_finish_str,
                    str(age_of_snag.days + age_of_snag.seconds / (3600 * 24)),
                    str(duration.days + duration.seconds / (3600 * 24)),
                    str(snag.is_ignored)))
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    contract_id = req_int('dc_contract_id')
    days_hidden = req_int('days_hidden')

    args = (contract_id, days_hidden, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
