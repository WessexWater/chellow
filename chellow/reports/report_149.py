import traceback
from datetime import datetime as Datetime
from sqlalchemy import or_, func, Float, cast
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
from chellow.models import (
    HhDatum, Channel, Era, Session, Supply, RegisterRead, Bill, BillType,
    ReadType, SiteEra, Mtc, Llfc)
from chellow.utils import (
    hh_min, hh_max, hh_format, HH, req_hh_date, req_int, to_utc)
import chellow.computer
import chellow.duos
import chellow.dloads
import os
import threading
from itertools import chain
from flask import request, g
from chellow.views import chellow_redirect
import csv
from werkzeug.exceptions import BadRequest


NORMAL_READ_TYPES = 'C', 'N', 'N3'


def mpan_bit(
        sess, supply, is_import, num_hh, eras, chunk_start, chunk_finish,
        forecast_date, caches):
    mpan_core_str = llfc_code = sc_str = supplier_contract_name = num_bad = ''
    gsp_kwh = msp_kwh = md = non_actual = 0
    date_at_md = kvarh_at_md = None

    for era in eras:
        mpan_core = era.imp_mpan_core if is_import else era.exp_mpan_core
        if mpan_core is None:
            continue
        if num_bad == '':
            num_bad = 0

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

        block_start = hh_max(era.start_date, chunk_start)
        block_finish = hh_min(era.finish_date, chunk_finish)

        supply_source = chellow.computer.SupplySource(
            sess, block_start, block_finish, forecast_date, era, is_import,
            caches)

        chellow.duos.duos_vb(supply_source)
        for hh in supply_source.hh_data:
            gsp_kwh += hh['gsp-kwh']
            hh_msp_kwh = hh['msp-kwh']
            msp_kwh += hh_msp_kwh
            if hh['status'] != 'A':
                num_bad += 1
                non_actual += hh_msp_kwh
            if hh_msp_kwh > md:
                md = hh_msp_kwh
                date_at_md = hh['start-date']

    if date_at_md is not None:
        kvarh_at_md = sess.query(
            cast(func.max(HhDatum.value), Float)).join(
            Channel).join(Era).filter(
            Era.supply == supply,
            Channel.imp_related == is_import,
            Channel.channel_type != 'ACTIVE',
            HhDatum.start_date == date_at_md).scalar()

    kw_at_md = md * 2

    if kvarh_at_md is None:
        kva_at_md = 'None'
    else:
        kva_at_md = (kw_at_md ** 2 + (kvarh_at_md * 2) ** 2) ** 0.5

    date_at_md_str = '' if date_at_md is None else hh_format(date_at_md)

    return [
        llfc_code, mpan_core_str, sc_str, supplier_contract_name, msp_kwh,
        non_actual, gsp_kwh, kw_at_md, date_at_md_str, kva_at_md, num_bad]


def content(supply_id, start_date, finish_date, user):
    forecast_date = to_utc(Datetime.max)
    caches = {}
    f = sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'supplies_duration.csv', user)
        f = open(running_name, mode='w', newline='')
        w = csv.writer(f, lineterminator='\n')
        w.writerow(
            (
                "Supply Id", "Supply Name", "Source", "Generator Type",
                "Site Code", "Site Name", "Associated Site Codes", "From",
                "To", "PC", "MTC", "CoP", "SSC", "Normal Reads", "Type",
                "Supply Start", "Supply Finish",
                "Import LLFC", "Import MPAN Core", "Import Supply Capacity",
                "Import Supplier", "Import Total MSP kWh",
                "Import Non-actual MSP kWh", "Import Total GSP kWh",
                "Import MD / kW", "Import MD Date", "Import MD / kVA",
                "Import Bad HHs", "Export LLFC", "Export MPAN Core",
                "Export Supply Capacity", "Export Supplier",
                "Export Total MSP kWh", "Export Non-actual MSP kWh",
                "Export GSP kWh", "Export MD / kW", "Export MD Date",
                "Export MD / kVA", "Export Bad HHs"))

        supplies = sess.query(Supply).join(Era).filter(
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            Era.start_date <= finish_date).order_by(Supply.id).distinct(). \
            options(
                joinedload(Supply.source), joinedload(Supply.generator_type))

        if supply_id is not None:
            supplies = supplies.filter(
                Supply.id == Supply.get_by_id(sess, supply_id).id)

        for supply in supplies:
            site_codes = set()
            site = None
            eras = sess.query(Era).filter(
                Era.supply == supply, Era.start_date <= finish_date,
                or_(
                    Era.finish_date == null(),
                    Era.finish_date >= start_date)).order_by(
                Era.start_date).options(
                    joinedload(Era.imp_llfc).joinedload(Llfc.voltage_level),
                    joinedload(Era.exp_llfc).joinedload(Llfc.voltage_level),
                    joinedload(Era.channels),
                    joinedload(Era.site_eras).joinedload(SiteEra.site),
                    joinedload(Era.pc), joinedload(Era.cop),
                    joinedload(Era.mtc).joinedload(Mtc.meter_type),
                    joinedload(Era.imp_supplier_contract),
                    joinedload(Era.exp_supplier_contract),
                    joinedload(Era.ssc)).all()

            era = eras[-1]
            for site_era in era.site_eras:
                if site_era.is_physical:
                    site = site_era.site
                else:
                    site_codes.add(site_era.site.code)

            sup_eras = sess.query(Era).filter(
                Era.supply == supply).order_by(Era.start_date).all()
            supply_start = sup_eras[0].start_date
            supply_finish = sup_eras[-1].finish_date

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
                    ReadType.code.in_(NORMAL_READ_TYPES)).options(
                        joinedload(RegisterRead.bill)),

                    sess.query(
                        RegisterRead, RegisterRead.present_date).join(
                        RegisterRead.present_type).join(Bill).join(
                        BillType).filter(
                    Bill.supply == supply, BillType.code != 'W',
                    RegisterRead.present_date >= start_date,
                    RegisterRead.present_date <= finish_date,
                    ReadType.code.in_(NORMAL_READ_TYPES)).options(
                        joinedload(RegisterRead.bill))):
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

            w.writerow(
                [
                    supply.id, supply.name, supply.source.code, generator_type,
                    site.code, site.name, '| '.join(sorted(site_codes)),
                    hh_format(start_date), hh_format(finish_date), era.pc.code,
                    era.mtc.code, era.cop.code, ssc_code, len(prime_reads),
                    supply_type, hh_format(supply_start),
                    hh_format(supply_finish, ongoing_str='')] + mpan_bit(
                    sess, supply, True, num_hh, eras, chunk_start,
                    chunk_finish, forecast_date, caches) + mpan_bit(
                    sess, supply, False, num_hh, eras, chunk_start,
                    chunk_finish, forecast_date, caches))

            # Avoid a long-running transaction
            sess.rollback()
    except BadRequest as e:
        f.write('Problem:' + e.description)
    except BaseException:
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
