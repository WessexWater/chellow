import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from chellow.utils import req_int, HH
from chellow.models import Era, HhDatum, Channel, Supply
from datetime import datetime as Datetime
from flask import render_template


def do_get(sess):
    supply_id = req_int('supply_id')
    months = req_int('months')
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    supply = Supply.get_by_id(sess, supply_id)

    finish_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) + \
        relativedelta(months=1) - HH
    start_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) - \
        relativedelta(months=months-1)

    era = sess.query(Era).filter(
        Era.supply == supply, Era.start_date <= finish_date,
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
            hh_line[keys[channel.imp_related][channel.channel_type]] = hh_datum
            hh_datum = next(hh_data, None)
        hh_date += HH
    return render_template(
        'report_17.html', supply=supply, era=era, hh_lines=hh_lines)
