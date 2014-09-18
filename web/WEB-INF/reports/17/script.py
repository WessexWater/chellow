from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
import pytz
from dateutil.relativedelta import relativedelta
from java.lang import System

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Batch', 'Participant', 'set_read_write', 'session', 'Bill', 'Report', 'Supply', 'HhDatum', 'Era'], 
        'utils': ['UserException', 'form_date', 'HH'],
        'templater': ['render']})


sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        supply_id = inv.getLong('supply_id')
        months = inv.getInteger('months')
        finish_year = inv.getInteger("finish_year")
        finish_month = inv.getInteger("finish_month")
        supply = Supply.get_by_id(sess, supply_id)

        finish_date = datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) + relativedelta(months=1) - HH
        start_date = datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) - relativedelta(months=months-1)

        era = sess.query(Era).from_statement("select * from era where supply_id = :supply_id and start_date <= :finish_date and (finish_date is null or finish_date >= :start_date) order by start_date desc").params(supply_id=supply.id, start_date=start_date, finish_date=finish_date).first()

        keys = {True: {'ACTIVE': 'import_active', 'REACTIVE_IMP': 'import_reactive_imp', 'REACTIVE_EXP': 'import_reactive_exp'},
            False: {'ACTIVE': 'export_active', 'REACTIVE_IMP': 'export_reactive_imp', 'REACTIVE_EXP': 'export_reactive_exp'}}

        hh_data = sess.query(HhDatum).from_statement("select hh_datum.* from hh_datum, channel, era where hh_datum.channel_id = channel.id and channel.era_id = era.id and era.supply_id = :supply_id and hh_datum.start_date >= :start_date and hh_datum.start_date <= :finish_date order by hh_datum.start_date").params(supply_id=supply.id, start_date=start_date, finish_date=finish_date).__iter__()
        hh_lines = []

        hh_date = start_date
        try:
            hh_datum = hh_data.next()
        except StopIteration:
            hh_datum = None
        while hh_date <= finish_date:
            hh_line = {'timestamp': hh_date}
            hh_lines.append(hh_line)
            while hh_datum is not None and hh_datum.start_date == hh_date:
                channel = hh_datum.channel
                hh_line[keys[channel.imp_related][channel.channel_type]] = hh_datum
                try:
                    hh_datum = hh_data.next()
                except StopIteration:
                    hh_datum = None

            hh_date += HH
        render(inv, template, {'supply': supply, 'era': era, 'hh_lines': hh_lines})
finally:
    sess.close()