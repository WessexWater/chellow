from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from sqlalchemy.sql.expression import text, select
from sqlalchemy import and_
import datetime
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['HhDatum', 'Site', 'Supply', 'set_read_write', 'session', 'Contract', 'Snag', 'Channel', 'Era', 'SiteEra'], 
        'utils': ['UserException', 'HH', 'form_date'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    contract_id = inv.getLong('hhdc_contract_id')
    days_hidden = inv.getInteger('days_hidden')
    
    file_name = "channel_snags.csv"
    inv.getResponse().setContentType('text/csv')
    inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="' + file_name + '"')
    pw = inv.getResponse().getWriter()
    pw.println("Hidden Days, Chellow Id,Imp MPAN Core,Exp MPAN Core, Site Code,Site Name,Snag Description,Import Related?,Channel Type,Start Date,Finish Date,Days Since Snag Finished,Duration Of Snag (Days),Is Ignored?")
    pw.flush()

    contract = Contract.get_hhdc_by_id(sess, contract_id)

    MILLIS_IN_DAY = 1000 * 60 * 60 * 24

    now = datetime.datetime.now(pytz.utc)
    cutoff_date = now - relativedelta(days=days_hidden)

    for snag, channel, era, supply, site_era, site in sess.query(Snag, Channel, Era, Supply, SiteEra, Site).join(Channel, Era, Supply, SiteEra, Site).filter(SiteEra.is_physical==True, Era.hhdc_contract_id==contract.id, Snag.start_date < cutoff_date).order_by(Site.code, Supply.id, Channel.imp_related, Channel.channel_type, Snag.description, "snag.start_date", "snag.id"):
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

        pw.println(','.join('"' + str(val) + '"' for val in [days_hidden, snag.id, era.imp_mpan_core, era.exp_mpan_core, site.code, site.name, snag.description, channel.imp_related, channel.channel_type, snag_start.strftime("%Y-%m-%d %H:%M"), snag_finish_str, age_of_snag.days + float(age_of_snag.seconds) / (3600 * 24), duration.days + float(duration.seconds) / (3600 * 24), snag.is_ignored]))
        pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()