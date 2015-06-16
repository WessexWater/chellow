import traceback
from net.sf.chellow.monad import Monad
import datetime
from sqlalchemy import or_, func, Float, cast
from sqlalchemy.sql.expression import null
import pytz
import db
import utils
import computer
import duos
import dloads
import os
import threading
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'computer', 'duos', 'dloads')
inv = globals()['inv']
Supply, Era, RegisterRead, Bill = db.Supply, db.Era, db.RegisterRead, db.Bill
ReadType, HhDatum, Channel = db.ReadType, db.HhDatum, db.Channel
BillType = db.BillType

hh_before, HH, hh_format = utils.hh_before, utils.HH, utils.hh_format
form_int = utils.form_int

NORMAL_READ_TYPES = 'C', 'N', 'N3'
forecast_date = datetime.datetime.max.replace(tzinfo=pytz.utc)
start_date = utils.form_date(inv, 'start')
finish_date = utils.form_date(inv, 'finish')

if inv.hasParameter('supply_id'):
    supply_id = inv.getLong('supply_id')
else:
    supply_id = None

caches = {}


def mpan_bit(sess, supply, is_import, num_hh, eras, chunk_start, chunk_finish):
    mpan_core_str = ''
    llfc_code = ''
    sc_str = ''
    supplier_contract_name = ''
    gsp_kwh = ''
    for era in eras:
        mpan_core = era.imp_mpan_core if is_import else era.exp_mpan_core
        if mpan_core is None:
            continue
        mpan_core_str = mpan_core
        if is_import:
            supplier_contract_name = era.imp_supplier_contract.name
            llfc = era.imp_llfc
            sc = era.imp_sc
        else:
            supplier_contract_name = era.exp_supplier_contract.name
            llfc = era.exp_llfc
            sc = era.exp_sc
        llfc_code = llfc.code
        sc_str = str(sc)
        if llfc.is_import and era.pc.code == '00' and \
                supply.source.code not in ('gen') and \
                supply.dno_contract.name != '99':
            if gsp_kwh == '':
                gsp_kwh = 0

            if chunk_start > era.start_date:
                block_start = chunk_start
            else:
                block_start = era.start_date

            if hh_before(chunk_finish, era.finish_date):
                block_finish = chunk_finish
            else:
                block_finish = era.finish_date

            supply_source = computer.SupplySource(
                sess, block_start, block_finish, forecast_date, era, is_import,
                None, caches)

            duos.duos_vb(supply_source)

            gsp_kwh += sum(
                [datum['gsp-kwh'] for datum in supply_source.hh_data])

    md = 0
    sum_kwh = 0
    non_actual = 0
    date_at_md = None
    kvarh_at_md = None
    num_na = 0

    for datum in sess.query(HhDatum).join(Channel).join(Era).filter(
            Era.supply_id == supply.id, Channel.imp_related == is_import,
            Channel.channel_type == 'ACTIVE',
            HhDatum.start_date >= chunk_start,
            HhDatum.start_date <= chunk_finish):
        hh_value = float(datum.value)
        hh_status = datum.status
        if hh_value > md:
            md = hh_value
            date_at_md = datum.start_date
            kvarh_at_md = sess.query(
                cast(func.max(HhDatum.value), Float)).join(
                Channel).join(Era).filter(
                Era.supply == supply,
                Channel.imp_related == is_import,
                Channel.channel_type != 'ACTIVE',
                HhDatum.start_date == date_at_md).one()[0]

        sum_kwh += hh_value
        if hh_status != 'A':
            non_actual = non_actual + hh_value
            num_na = num_na + 1

    kw_at_md = md * 2
    if kvarh_at_md is None:
        kva_at_md = 'None'
    else:
        kva_at_md = (kw_at_md ** 2 + (kvarh_at_md * 2) ** 2) ** 0.5

    num_bad = str(num_hh - sess.query(HhDatum).join(Channel).join(Era).filter(
        Era.supply_id == supply.id, Channel.imp_related == is_import,
        Channel.channel_type == 'ACTIVE', HhDatum.start_date >= chunk_start,
        HhDatum.start_date <= chunk_finish).count() + num_na)

    date_at_md_str = '' if date_at_md is None else hh_format(date_at_md)

    return ','.join(str(val) for val in [
        llfc_code, mpan_core_str, sc_str, supplier_contract_name, sum_kwh,
        non_actual, gsp_kwh, kw_at_md, date_at_md_str, kva_at_md, num_bad])


def content():
    sess = None
    f = None
    try:
        sess = db.session()

        running_name, finished_name = dloads.make_names('output.csv')
        f = open(running_name, "w")
        f.write(
            ','.join(
                (
                    "Supply Id", "Supply Name", "Source", "Generator Type",
                    "Site Ids", "Site Names", "From", "To", "PC", "MTC", "CoP",
                    "SSC", "Normal Reads", "Type", "Import LLFC",
                    "Import MPAN Core", "Import Supply Capacity",
                    "Import Supplier", "Import Total MSP kWh",
                    "Import Non-actual MSP kWh", "Import Total GSP kWh",
                    "Import MD / kW", "Import MD Date", "Import MD / kVA",
                    "Import Bad HHs", "Export LLFC", "Export MPAN Core",
                    "Export Supply Capacity", "Export Supplier",
                    "Export Total MSP kWh", "Export Non-actual MSP kWh",
                    "Export GSP kWh", "Export MD / kW", "Export MD Date",
                    "Export MD / kVA", "Export Bad HHs")))

        supplies = sess.query(Supply).join(Era).filter(
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            Era.start_date <= finish_date).order_by(Supply.id).distinct()

        if supply_id is not None:
            supplies = supplies.filter(
                Supply.id == Supply.get_by_id(sess, supply_id).id)

        for supply in supplies:
            site_codes = ''
            site_names = ''
            eras = supply.find_eras(sess, start_date, finish_date)

            era = eras[-1]
            for site_era in era.site_eras:
                site = site_era.site
                site_codes = site_codes + site.code + ', '
                site_names = site_names + site.name + ', '
            site_codes = site_codes[:-2]
            site_names = site_names[:-2]

            if supply.generator_type is None:
                generator_type = ''
            else:
                generator_type = supply.generator_type.code

            ssc = era.ssc
            ssc_code = '' if ssc is None else ssc.code

            prime_reads = set()
            for query in (sess.query(RegisterRead).join(Bill).join(
                    RegisterRead.previous_type).join(BillType).filter(
                    Bill.supply == supply,
                    BillType.code != 'W',
                    RegisterRead.previous_date >= start_date,
                    RegisterRead.previous_date <= finish_date,
                    ReadType.code.in_(NORMAL_READ_TYPES)),

                    sess.query(RegisterRead).join(Bill).join(
                    RegisterRead.present_type).join(BillType).filter(
                    Bill.supply == supply,
                    BillType.code != 'W',
                    RegisterRead.present_date >= start_date,
                    RegisterRead.present_date <= finish_date,
                    ReadType.code.in_(NORMAL_READ_TYPES))):

                for read in query:
                    prime_bill = sess.query(Bill).join(BillType).filter(
                        Bill.supply == supply,
                        Bill.start_date <= read.bill.finish_date,
                        Bill.finish_date >= read.bill.start_date,
                        Bill.reads.any()).order_by(
                        Bill.issue_date.desc(), BillType.code).first()
                    if prime_bill.id == read.bill_id:
                        prime_reads.add(
                            str(read.previous_date) + "_" + read.msn)

            supply_type = era.make_meter_category()

            if eras[0].start_date > start_date:
                chunk_start = eras[0].start_date
            else:
                chunk_start = start_date

            if hh_before(finish_date, era.finish_date):
                chunk_finish = finish_date
            else:
                chunk_finish = era.finish_date

            num_hh = utils.totalseconds(chunk_finish - (chunk_start - HH)) / \
                (30 * 60)

            f.write(
                '\n' + ','.join(
                    ('"' + str(value) + '"') for value in [
                        supply.id, supply.name, supply.source.code,
                        generator_type, site_codes, site_names,
                        hh_format(start_date), hh_format(finish_date),
                        era.pc.code, era.mtc.code, era.cop.code, ssc_code,
                        len(prime_reads), supply_type]) + ',')
            f.write(
                mpan_bit(
                    sess, supply, True, num_hh, eras, chunk_start,
                    chunk_finish) + "," +
                mpan_bit(
                    sess, supply, False, num_hh, eras, chunk_start,
                    chunk_finish))
    except:
        f.write(traceback.format_exc())
    finally:
        if sess is not None:
            sess.close()
        f.close()
        os.rename(running_name, finished_name)

threading.Thread(target=content).start()
inv.sendSeeOther("/reports/251/output/")
