from net.sf.chellow.monad import Monad
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
form_int, HH = utils.form_int, utils.HH
Era, HhDatum, Channel = db.Era, db.HhDatum, db.Channel
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        supply_id = form_int(inv, 'supply_id')
        months = form_int(inv, 'months')
        finish_year = inv.getInteger("finish_year")
        finish_month = inv.getInteger("finish_month")
        supply = db.Supply.get_by_id(sess, supply_id)

        finish_date = datetime(
            finish_year, finish_month, 1, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH
        start_date = datetime(
            finish_year, finish_month, 1, tzinfo=pytz.utc) - \
            relativedelta(months=months-1)

        era = sess.query(Era).filter(
            Era.supply_id == supply.id, Era.start_date <= finish_date,
            or_(
                Era.finish_date == null(),
                Era.finish_date >= start_date)).order_by(
            Era.start_date.desc()).first()

        keys = {
            True: {
                'ACTIVE': 'import_active',
                'REACTIVE_IMP': 'import_reactive_imp',
                'REACTIVE_EXP': 'import_reactive_exp'},
            False: {
                'ACTIVE': 'export_active',
                'REACTIVE_IMP': 'export_reactive_imp',
                'REACTIVE_EXP': 'export_reactive_exp'}}

        hh_data = iter(sess.query(HhDatum).join(Channel).join(Era).filter(
            Era.supply == supply, HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date).order_by(
            HhDatum.start_date))
        hh_lines = []

        hh_date = start_date
        hh_datum = next(hh_data, None)
        while hh_date <= finish_date:
            hh_line = {'timestamp': hh_date}
            hh_lines.append(hh_line)
            while hh_datum is not None and hh_datum.start_date == hh_date:
                channel = hh_datum.channel
                hh_line[keys[channel.imp_related][channel.channel_type]] = \
                    hh_datum
                hh_datum = next(hh_data, None)

            hh_date += HH
        render(
            inv, template, {
                'supply': supply, 'era': era, 'hh_lines': hh_lines})
finally:
    if sess is not None:
        sess.close()
