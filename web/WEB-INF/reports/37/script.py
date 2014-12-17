from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy.sql.expression import false
from itertools import islice
import templater
import utils
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
UserException, form_int = utils.UserException, utils.form_int
Contract, Snag, Channel, Era = db.Contract, db.Snag, db.Channel, db.Era
Site, SiteEra = db.Site, db.SiteEra
inv, template = globals()['inv'], globals()['template']

sess = None
rate_scripts = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        if inv.hasParameter('hhdc-contract-id'):
            contract_id = form_int(inv, 'hhdc-contract-id')
        else:
            contract_id = form_int(inv, 'hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        hidden_days = form_int(inv, 'hidden_days')

        total_snags = sess.query(Snag).join(Channel).join(Era).filter(
            Snag.is_ignored == false(), Era.hhdc_contract_id == contract.id,
            Snag.start_date < datetime.datetime.now(pytz.utc) -
            relativedelta(days=hidden_days)).count()
        snags = sess.query(Snag).join(Channel).join(Era).join(
            Era.site_eras).join(SiteEra.site).filter(
            Snag.is_ignored == false(), Era.hhdc_contract_id == contract.id,
            Snag.start_date < datetime.datetime.now(pytz.utc) -
            relativedelta(days=hidden_days)).order_by(
            Site.code, Era.id, Snag.start_date, Snag.finish_date,
            Snag.channel_id)
        snag_groups = []
        prev_snag = None
        for snag in islice(snags, 200):
            if prev_snag is None or \
                    snag.channel.era != prev_snag.channel.era or \
                    snag.start_date != prev_snag.start_date or \
                    snag.finish_date != prev_snag.finish_date or \
                    snag.description != prev_snag.description:
                era = snag.channel.era
                snag_group = {
                    'snags': [],
                    'sites': sess.query(Site).join(Site.site_eras).filter(
                        SiteEra.era == era).order_by(Site.code),
                    'era': era, 'description': snag.description,
                    'start_date': snag.start_date,
                    'finish_date': snag.finish_date}
                snag_groups.append(snag_group)
            snag_group['snags'].append(snag)
            prev_snag = snag

        render(
            inv, template, {
                'contract': contract, 'snags': snags,
                'total_snags': total_snags, 'snag_groups': snag_groups})
except UserException, e:
    if str(e).startswith("There isn't a contract"):
        inv.sendNotFound(str(e))
    else:
        render(
            inv, template, {'messages': [str(e)], 'contract': contract}, 400)
finally:
    if sess is not None:
        sess.close()
