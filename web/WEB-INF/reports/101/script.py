from net.sf.chellow.monad import Monad
import pytz
import datetime
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from dateutil.relativedelta import relativedelta
import db
import utils
import computer
import templater

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'computer', 'utils')
HH, hh_before = utils.HH, utils.hh_before
Supply, Era = db.Supply, db.Era
render = templater.render
inv, template = globals()['inv'], globals()['template']


sess = None
try:
    sess = db.session()

    supply_id = inv.getLong("supply_id")
    supply = Supply.get_by_id(sess, supply_id)

    start_date = utils.form_date(inv, 'start')
    finish_date = utils.form_date(inv, 'finish')
    forecast_date = computer.forecast_date()

    net_gbp = 0
    caches = {}
    meras = []
    debug = ''

    month_start = datetime.datetime(
        start_date.year, start_date.month, 1, tzinfo=pytz.utc)

    while not month_start > finish_date:
        month_finish = month_start + relativedelta(months=1) - HH

        chunk_start = start_date if start_date > month_start else month_start

        if finish_date < month_finish:
            chunk_finish = finish_date
        else:
            chunk_finish = month_finish

        for era in sess.query(Era).filter(
                Era.supply == supply, Era.imp_mpan_core != null(),
                Era.start_date <= chunk_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= chunk_start)):
            if era.start_date > chunk_start:
                block_start = era.start_date
            else:
                block_start = chunk_start

            debug += 'found an era'

            if hh_before(chunk_finish, era.finish_date):
                block_finish = chunk_finish
            else:
                block_finish = era.finish_date

            mpan_core = era.imp_mpan_core
            contract = era.imp_supplier_contract
            data_source = computer.SupplySource(
                sess, block_start, block_finish, forecast_date, era, True,
                None, caches)
            headings = [
                'id', 'supplier_contract', 'account', 'start date',
                'finish date']
            data = [
                data_source.id, contract.name, data_source.supplier_account,
                data_source.start_date, data_source.finish_date]
            mera = {'headings': headings, 'data': data, 'skip': False}

            meras.append(mera)
            computer.contract_func(
                caches, contract, 'virtual_bill', None)(data_source)
            bill = data_source.supplier_bill
            net_gbp += bill['net-gbp']

            for title in computer.contract_func(
                    caches, contract, 'virtual_bill_titles', None)():
                if title == 'consumption-info':
                    del bill[title]
                    continue
                headings.append(title)
                data.append(bill[title])
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                headings.append(k)
                data.append(bill[k])

            if len(meras) > 1 and meras[-2]['headings'] == mera['headings']:
                mera['skip'] = True

        month_start += relativedelta(months=1)

    render(
        inv, template, {
            'supply': supply, 'start_date': start_date,
            'finish_date': finish_date, 'meras': meras,
            'net_gbp': net_gbp})
finally:
    if sess is not None:
        sess.close()
