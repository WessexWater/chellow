import datetime
from dateutil.relativedelta import relativedelta
import pytz
import traceback
from sqlalchemy.sql.expression import true
from net.sf.chellow.monad import Monad
import db
import utils
import computer

Monad.getUtils()['impt'](globals(), 'utils', 'db', 'computer')
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
Supply, Site, SiteEra = db.Supply, db.Site, db.SiteEra
inv = globals()['inv']

start_year = inv.getInteger("start_year")
start_month = inv.getInteger("start_month")
start_day = inv.getInteger("start_day")

finish_year = inv.getInteger("finish_year")
finish_month = inv.getInteger("finish_month")
finish_day = inv.getInteger("finish_day")

is_import = inv.getBoolean('is_import')
supply_id = inv.getLong('supply_id')


def content():
    sess = None
    try:
        sess = db.session()

        start_date = datetime.datetime(
            start_year, start_month, start_day, tzinfo=pytz.utc)
        finish_date = datetime.datetime(
            finish_year, finish_month, finish_day, tzinfo=pytz.utc) + \
            relativedelta(months=1) - HH

        caches = {}
        supply = Supply.get_by_id(sess, supply_id)
        forecast_date = computer.forecast_date()
        day_start = start_date
        prev_bill_titles = []

        while not day_start > finish_date:
            day_finish = day_start + relativedelta(days=1) - HH

            for era in supply.find_eras(sess, day_start, day_finish):
                if era.start_date > day_start:
                    chunk_start = era.start_date
                else:
                    chunk_start = day_start

                if hh_after(era.finish_date, day_finish):
                    chunk_finish = day_finish
                else:
                    chunk_finish = era.finish_date

                ss = computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era,
                    is_import, None, caches)

                sup_con = ss.supplier_contract
                bill_titles = computer.contract_func(
                    caches, sup_con, 'virtual_bill_titles', None)()
                if bill_titles != prev_bill_titles:
                    yield ','.join(
                        [
                            'MPAN Core', 'Site Code', 'Site Name', 'Account',
                            'From', 'To'] + bill_titles) + '\n'
                    prev_bill_titles = bill_titles

                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.era == era, SiteEra.is_physical == true()).one()
                yield ','.join('"' + str(value) + '"' for value in [
                    ss.mpan_core, site.code, site.name, ss.supplier_account,
                    hh_format(ss.start_date), hh_format(ss.finish_date)])

                computer.contract_func(
                    caches, sup_con, 'virtual_bill', None)(ss)
                bill = ss.supplier_bill
                for title in bill_titles:
                    if title in bill:
                        val_raw = bill[title]
                        if isinstance(val_raw, datetime.datetime):
                            val = hh_format(val_raw)
                        else:
                            val = str(val_raw)

                        yield ',"' + val + '"'
                        del bill[title]
                    else:
                        yield ',""'

                for k in sorted(bill.keys()):
                    yield ',"' + k + '","' + str(bill[k]) + '"'
                yield '\n'
            day_start += relativedelta(days=1)
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='daily_supplier_virtual_bill.csv')
