import traceback
import datetime
from sqlalchemy import or_, func, Float, cast
from sqlalchemy.sql.expression import null
import pytz
from chellow.models import (
    HhDatum, Channel, Era, Session, Supply, RegisterRead, Bill, BillType,
    ReadType)
from chellow.utils import hh_min, hh_max, hh_format, HH, req_hh_date, req_int
import chellow.computer
import chellow.duos
import chellow.dloads
import os
import threading
from itertools import chain
from flask import request, g
from chellow.views import chellow_redirect

NORMAL_READ_TYPES = 'C', 'N', 'N3'


def mpan_bit(
        sess, supply, is_import, num_hh, eras, chunk_start, chunk_finish,
        forecast_date, caches):
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

            block_start = hh_max(era.start_date, chunk_start)
            block_finish = hh_min(era.finish_date, chunk_finish)

            supply_source = chellow.computer.SupplySource(
                sess, block_start, block_finish, forecast_date, era, is_import,
                caches)

            chellow.duos.duos_vb(supply_source)

            gsp_kwh += sum(datum['gsp-kwh'] for datum in supply_source.hh_data)

    md = 0
    sum_kwh = 0
    non_actual = 0
    date_at_md = None
    kvarh_at_md = None
    num_na = 0

    for datum in sess.query(HhDatum).join(Channel).join(Era).filter(
            Era.supply == supply, Channel.imp_related == is_import,
            Channel.channel_type == 'ACTIVE',
            HhDatum.start_date >= chunk_start,
            HhDatum.start_date <= chunk_finish).order_by(HhDatum.id):
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
            non_actual += hh_value
            num_na += 1

    kw_at_md = md * 2
    if kvarh_at_md is None:
        kva_at_md = 'None'
    else:
        kva_at_md = (kw_at_md ** 2 + (kvarh_at_md * 2) ** 2) ** 0.5

    num_bad = num_hh - sess.query(HhDatum).join(Channel).join(Era).filter(
        Era.supply == supply, Channel.imp_related == is_import,
        Channel.channel_type == 'ACTIVE', HhDatum.start_date >= chunk_start,
        HhDatum.start_date <= chunk_finish).count() + num_na

    date_at_md_str = '' if date_at_md is None else hh_format(date_at_md)

    return ','.join(str(val) for val in [
        llfc_code, mpan_core_str, sc_str, supplier_contract_name, sum_kwh,
        non_actual, gsp_kwh, kw_at_md, date_at_md_str, kva_at_md, num_bad])


def content(supply_id, start_date, finish_date, user):
    forecast_date = datetime.datetime.max.replace(tzinfo=pytz.utc)
    caches = {}
    f = sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'supplies_duration.csv', user)
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
            for read, rdate in chain(
                    sess.query(
                        RegisterRead, RegisterRead.previous_date).join(
                        RegisterRead.previous_type).join(Bill).join(
                        BillType).filter(
                    Bill.supply == supply, BillType.code != 'W',
                    RegisterRead.previous_date >= start_date,
                    RegisterRead.previous_date <= finish_date,
                    ReadType.code.in_(NORMAL_READ_TYPES)),

                    sess.query(
                        RegisterRead, RegisterRead.present_date).join(
                        RegisterRead.present_type).join(Bill).join(
                        BillType).filter(
                    Bill.supply == supply, BillType.code != 'W',
                    RegisterRead.present_date >= start_date,
                    RegisterRead.present_date <= finish_date,
                    ReadType.code.in_(NORMAL_READ_TYPES))):
                prime_bill = sess.query(Bill).join(BillType).filter(
                    Bill.supply == supply,
                    Bill.start_date <= read.bill.finish_date,
                    Bill.finish_date >= read.bill.start_date,
                    Bill.reads.any()).order_by(
                    Bill.issue_date.desc(), BillType.code).first()
                if prime_bill.id == read.bill.id:
                    prime_reads.add(
                        str(rdate) + "_" + read.msn)

            supply_type = era.make_meter_category()

            chunk_start = hh_max(eras[0].start_date, start_date)
            chunk_finish = hh_min(era.finish_date, finish_date)
            num_hh = int(
                (chunk_finish - (chunk_start - HH)).total_seconds() /
                (30 * 60))

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
                    chunk_finish, forecast_date, caches) + "," +
                mpan_bit(
                    sess, supply, False, num_hh, eras, chunk_start,
                    chunk_finish, forecast_date, caches))
    except:
        f.write(traceback.format_exc())
    finally:
        sess.close()
        f.close()
        os.rename(running_name, finished_name)


def do_get(sess):
    start_date = req_hh_date('start')
    finish_date = req_hh_date('finish')
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None
    thread = threading.Thread(
        target=content, args=(supply_id, start_date, finish_date, g.user))
    thread.start()
    return chellow_redirect("/downloads", 303)
