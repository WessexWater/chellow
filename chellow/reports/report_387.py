import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
from chellow.models import Supply, Era, Site, SiteEra
from chellow.utils import hh_format, hh_range, req_int, req_date, send_response
import chellow.computer


def content(supply_id, start_date, finish_date, sess):
    caches = {}
    try:
        supply = Supply.get_by_id(sess, supply_id)

        forecast_date = chellow.computer.forecast_date()

        prev_titles = None

        for hh_start in hh_range(start_date, finish_date):
            era = sess.query(Era).filter(
                Era.supply == supply, Era.start_date <= hh_start,
                or_(
                    Era.finish_date == null(),
                    Era.finish_date >= hh_start)).one()

            site = sess.query(Site).join(SiteEra).filter(
                SiteEra.era == era, SiteEra.is_physical == true()).one()

            ds = chellow.computer.SupplySource(
                sess, hh_start, hh_start, forecast_date, era, True, caches)

            titles = [
                'MPAN Core', 'Site Code', 'Site Name', 'Account', 'HH Start',
                '']

            output_line = [
                ds.mpan_core, site.code, site.name, ds.supplier_account,
                hh_format(ds.start_date), '']

            mop_titles = ds.contract_func(
                era.mop_contract, 'virtual_bill_titles')()
            titles.extend(['mop-' + t for t in mop_titles])

            ds.contract_func(era.mop_contract, 'virtual_bill')(ds)
            bill = ds.mop_bill
            for title in mop_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]
            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]])

            output_line.append('')
            dc_titles = ds.contract_func(
                era.hhdc_contract, 'virtual_bill_titles')()
            titles.append('')
            titles.extend(['dc-' + t for t in dc_titles])

            ds.contract_func(era.hhdc_contract, 'virtual_bill')(ds)
            bill = ds.dc_bill
            for title in dc_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]
            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]])

            if era.imp_supplier_contract is not None:
                contract = era.imp_supplier_contract
                output_line.append('')
                supplier_titles = ds.contract_func(
                    contract, 'virtual_bill_titles')()
                titles.append('')
                titles.extend(['imp-supplier-' + t for t in supplier_titles])

                ds.contract_func(contract, 'virtual_bill')(ds)
                bill = ds.supplier_bill
                for title in supplier_titles:
                    output_line.append(bill.get(title, ''))
                    if title in bill:
                        del bill[title]

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]])

            if era.exp_supplier_contract is not None:
                contract = era.exp_supplier_contract
                ds = chellow.computer.SupplySource(
                    sess, hh_start, hh_start, forecast_date, era, False,
                    caches)
                output_line.append('')
                supplier_titles = ds.contract_func(
                    contract, 'virtual_bill_titles')()
                titles.append('')
                titles.extend(['exp-supplier-' + t for t in supplier_titles])

                ds.contract_func(contract, 'virtual_bill')(ds)
                bill = ds.supplier_bill
                for title in supplier_titles:
                    output_line.append(bill.get(title, ''))
                    if title in bill:
                        del bill[title]

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]])

            if titles != prev_titles:
                prev_titles = titles
                yield ','.join('"' + str(v) + '"' for v in titles) + '\n'
            yield ','.join('"' + str(v) + '"' for v in output_line) + '\n'
    except:
        yield traceback.format_exc()


def do_get(sess):
    supply_id = req_int('supply_id')
    start_date = req_date('start')
    finish_date = req_date('finish')
    file_name = 'supply_virtual_bills_hh_' + str(supply_id) + '.csv'
    return send_response(
        content, args=(supply_id, start_date, finish_date, sess),
        file_name=file_name)
