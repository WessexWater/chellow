import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import chellow.computer
from chellow.models import Contract, Era
from chellow.utils import hh_format, req_date, req_int, send_response


def content(start_date, finish_date, contract_id, sess):
    caches = {}
    try:
        contract = Contract.get_mop_by_id(sess, contract_id)

        forecast_date = chellow.computer.forecast_date()

        yield ','.join(
            (
                'Import MPAN Core', 'Export MPAN Core', 'Start Date',
                'Finish Date'))
        bill_titles = chellow.computer.contract_func(
            caches, contract, 'virtual_bill_titles', None)()
        for title in bill_titles:
            yield ',' + title
        yield '\n'

        for era in sess.query(Era).filter(
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                Era.mop_contract_id == contract.id).order_by(Era.supply_id):
            import_mpan_core = era.imp_mpan_core
            if import_mpan_core is None:
                import_mpan_core_str = ''
            else:
                mpan_core = import_mpan_core
                is_import = True
                import_mpan_core_str = mpan_core

            export_mpan_core = era.exp_mpan_core
            if export_mpan_core is None:
                export_mpan_core_str = ''
            else:
                is_import = False
                mpan_core = export_mpan_core
                export_mpan_core_str = mpan_core

            yield import_mpan_core_str + ',' + export_mpan_core_str + ',' + \
                hh_format(start_date) + ',' + hh_format(finish_date) + ','
            supply_source = chellow.computer.SupplySource(
                sess, start_date, finish_date, forecast_date, era, is_import,
                None, caches)
            chellow.computer.contract_func(
                caches, contract, 'virtual_bill', None)(supply_source)
            bill = supply_source.mop_bill
            for title in bill_titles:
                if title in bill:
                    yield '"' + str(bill[title]) + '",'
                    del bill[title]
                else:
                    yield ','
            for k in sorted(bill.keys()):
                yield ',"' + k + '","' + str(bill[k]) + '"'
            yield '\n'
    except:
        yield traceback.format_exc()


def do_get(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    contract_id = req_int('mop_contract_id')
    return send_response(
        content, args=(start_date, finish_date, contract_id, sess),
        file_name='output.csv')
