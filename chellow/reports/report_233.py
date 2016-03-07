from datetime import datetime as Datetime
import datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy.sql.expression import true
import traceback
from chellow.models import (
    Contract, Snag, Channel, Era, Supply, Session, SiteEra, Site)
from chellow.utils import req_int, send_response


def content(contract_id, days_hidden):
    sess = None
    try:
        sess = Session()

        yield ','.join(
            (
                'Hidden Days', 'Chellow Id', 'Imp MPAN Core', 'Exp MPAN Core',
                'Site Code', 'Site Name', 'Snag Description',
                'Import Related?', 'Channel Type', 'Start Date', 'Finish Date',
                'Days Since Snag Finished', 'Duration Of Snag (Days)',
                'Is Ignored?')) + '\n'

        contract = Contract.get_hhdc_by_id(sess, contract_id)

        now = Datetime.now(pytz.utc)
        cutoff_date = now - relativedelta(days=days_hidden)

        for snag, channel, era, supply, site_era, site in sess.query(
                Snag, Channel, Era, Supply, SiteEra, Site).join(
                Channel, Era, Supply, SiteEra, Site).filter(
                SiteEra.is_physical == true(), Era.hhdc_contract == contract,
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

            yield ','.join('"' + str(val) + '"' for val in [
                days_hidden, snag.id, era.imp_mpan_core, era.exp_mpan_core,
                site.code, site.name, snag.description, channel.imp_related,
                channel.channel_type, snag_start.strftime("%Y-%m-%d %H:%M"),
                snag_finish_str,
                age_of_snag.days + float(age_of_snag.seconds) / (3600 * 24),
                duration.days + float(duration.seconds) / (3600 * 24),
                snag.is_ignored]) + '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()


def do_get(sess):
    contract_id = req_int('hhdc_contract_id')
    days_hidden = req_int('days_hidden')
    return send_response(
        content, args=(contract_id, days_hidden),
        file_name="channel_snags.csv")
