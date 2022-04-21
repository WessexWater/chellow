import csv
import os
import threading
import traceback
from datetime import datetime as Datetime
from itertools import chain

from flask import g, request

from sqlalchemy import null, or_, select
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

import chellow.computer
import chellow.dloads
import chellow.duos
from chellow.models import (
    Bill,
    BillType,
    Channel,
    Era,
    Llfc,
    MtcParticipant,
    ReadType,
    RegisterRead,
    Session,
    SiteEra,
    Supply,
)
from chellow.utils import (
    HH,
    csv_make_val,
    hh_max,
    hh_min,
    parse_mpan_core,
    req_hh_date,
    req_int,
    req_str,
    to_utc,
)
from chellow.views.home import chellow_redirect


NORMAL_READ_TYPES = "C", "N", "N3"


def mpan_bit(
    sess,
    supply,
    is_import,
    num_hh,
    era,
    chunk_start,
    chunk_finish,
    forecast_date,
    caches,
):

    active_channel = sess.execute(
        select(Channel).where(
            Channel.era == era,
            Channel.channel_type == "ACTIVE",
            Channel.imp_related == is_import,
        )
    ).scalar_one_or_none()

    md_kw_date = None
    md_kva_date = None

    supplier_contract = (
        era.imp_supplier_contract if is_import else era.exp_supplier_contract
    )
    if active_channel is None and supplier_contract is None:
        gsp_kwh = msp_kwh = md_kw = md_kva = non_actual_msp_kwh = num_bad = None
        avg_msp_kw = avg_kva = None
    else:
        gsp_kwh = msp_kwh = md_kw = md_kva = non_actual_msp_kwh = num_bad = kva = 0

        supply_source = chellow.computer.SupplySource(
            sess, chunk_start, chunk_finish, forecast_date, era, is_import, caches
        )

        chellow.duos.duos_vb(supply_source)
        for hh in supply_source.hh_data:
            gsp_kwh += hh["gsp-kwh"]
            hh_msp_kwh = hh["msp-kwh"]
            msp_kwh += hh_msp_kwh

            if hh["status"] != "A":
                num_bad += 1
                non_actual_msp_kwh += hh_msp_kwh

            hh_kw = 2 * hh_msp_kwh

            if hh_kw > md_kw:
                md_kw = hh_msp_kwh * 2
                md_kw_date = hh["start-date"]

            hh_kva = (
                hh["msp-kw"] ** 2 + max(hh["imp-msp-kvar"], hh["exp-msp-kvar"]) ** 2
            ) ** 0.5

            kva += hh_kva

            if hh_kva > md_kva:
                md_kva = hh_kva
                md_kva_date = hh["start-date"]

        avg_msp_kw = msp_kwh / num_hh * 2
        avg_kva = kva / num_hh

    pref = "import" if is_import else "export"
    return {
        f"{pref}_msp_kwh": msp_kwh,
        f"{pref}_non_actual_msp_kwh": non_actual_msp_kwh,
        f"{pref}_gsp_kwh": gsp_kwh,
        f"{pref}_avg_msp_kw": avg_msp_kw,
        f"{pref}_avg_kva": avg_kva,
        f"{pref}_md_kw": md_kw,
        f"{pref}_md_kw_date": md_kw_date,
        f"{pref}_md_kva": md_kva,
        f"{pref}_md_kva_date": md_kva_date,
        f"{pref}_bad_hhs": num_bad,
    }


def _process(sess, caches, f, start_date, finish_date, supply_id, mpan_cores):
    forecast_date = to_utc(Datetime.max)

    w = csv.writer(f, lineterminator="\n")
    titles = [
        "era_start",
        "era_finish",
        "supply_id",
        "supply_name",
        "source",
        "generator_type",
        "site_code",
        "site_name",
        "associated_site_codes",
        "from",
        "to",
        "pc",
        "mtc",
        "cop",
        "ssc",
        "energisation_status",
        "properties",
        "mop_contract",
        "mop_account",
        "dc_contract",
        "dc_account",
        "normal_reads",
        "type",
        "supply_start",
        "supply_finish",
    ]

    for polarity in ("import", "export"):
        titles.append(f"{polarity}_llfc")
        titles.append(f"{polarity}_mpan_core")
        titles.append(f"{polarity}_supply_capacity")
        titles.append(f"{polarity}_supplier")
        titles.append(f"{polarity}_msp_kwh")
        titles.append(f"{polarity}_avg_msp_kw")
        titles.append(f"{polarity}_avg_kva")
        titles.append(f"{polarity}_non_actual_msp_kwh")
        titles.append(f"{polarity}_gsp_kwh")
        titles.append(f"{polarity}_md_kw")
        titles.append(f"{polarity}_md_kw_date")
        titles.append(f"{polarity}_md_kva")
        titles.append(f"{polarity}_md_kva_date")
        titles.append(f"{polarity}_bad_hhs")

    w.writerow(titles)

    eras = (
        sess.query(Era)
        .filter(
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            Era.start_date <= finish_date,
        )
        .order_by(Era.supply_id, Era.start_date)
        .options(
            joinedload(Era.supply),
            joinedload(Era.supply).joinedload(Supply.source),
            joinedload(Era.supply).joinedload(Supply.generator_type),
            joinedload(Era.imp_llfc).joinedload(Llfc.voltage_level),
            joinedload(Era.exp_llfc).joinedload(Llfc.voltage_level),
            joinedload(Era.imp_llfc),
            joinedload(Era.exp_llfc),
            joinedload(Era.mop_contract),
            joinedload(Era.dc_contract),
            joinedload(Era.channels),
            joinedload(Era.site_eras).joinedload(SiteEra.site),
            joinedload(Era.pc),
            joinedload(Era.cop),
            joinedload(Era.mtc_participant).joinedload(MtcParticipant.meter_type),
            joinedload(Era.imp_supplier_contract),
            joinedload(Era.exp_supplier_contract),
            joinedload(Era.ssc),
            joinedload(Era.energisation_status),
            joinedload(Era.site_eras),
        )
    )

    if supply_id is not None:
        eras = eras.where(Era.supply == Supply.get_by_id(sess, supply_id))

    if mpan_cores is not None:
        eras = eras.where(
            or_(Era.imp_mpan_core.in_(mpan_cores), Era.exp_mpan_core.in_(mpan_cores))
        )

    for era in eras:
        caches["era"] = era
        supply = era.supply
        site_codes = set()
        site = None
        for site_era in era.site_eras:
            if site_era.is_physical:
                site = site_era.site
            else:
                site_codes.add(site_era.site.code)

        sup_eras = (
            sess.query(Era).filter(Era.supply == supply).order_by(Era.start_date).all()
        )
        supply_start = sup_eras[0].start_date
        supply_finish = sup_eras[-1].finish_date

        prime_reads = set()
        for read, rdate in chain(
            sess.query(RegisterRead, RegisterRead.previous_date)
            .join(RegisterRead.previous_type)
            .join(Bill)
            .join(BillType)
            .filter(
                Bill.supply == supply,
                BillType.code != "W",
                RegisterRead.previous_date >= start_date,
                RegisterRead.previous_date <= finish_date,
                ReadType.code.in_(NORMAL_READ_TYPES),
            )
            .options(joinedload(RegisterRead.bill)),
            sess.query(RegisterRead, RegisterRead.present_date)
            .join(RegisterRead.present_type)
            .join(Bill)
            .join(BillType)
            .filter(
                Bill.supply == supply,
                BillType.code != "W",
                RegisterRead.present_date >= start_date,
                RegisterRead.present_date <= finish_date,
                ReadType.code.in_(NORMAL_READ_TYPES),
            )
            .options(joinedload(RegisterRead.bill)),
        ):
            prime_bill = (
                sess.query(Bill)
                .join(BillType)
                .filter(
                    Bill.supply == supply,
                    Bill.start_date <= read.bill.finish_date,
                    Bill.finish_date >= read.bill.start_date,
                    Bill.reads.any(),
                )
                .order_by(Bill.issue_date.desc(), BillType.code)
                .first()
            )
            if prime_bill.id == read.bill.id:
                prime_reads.add(f"{rdate}_{read.msn}")

        chunk_start = hh_max(era.start_date, start_date)
        chunk_finish = hh_min(era.finish_date, finish_date)
        num_hh = int((chunk_finish + HH - chunk_start).total_seconds() / (30 * 60))
        ssc = era.ssc
        generator_type = supply.generator_type
        imp_llfc = era.imp_llfc
        imp_supplier_contract = era.imp_supplier_contract
        exp_llfc = era.exp_llfc
        exp_supplier_contract = era.exp_supplier_contract

        values = {
            "era_start": era.start_date,
            "era_finish": era.finish_date,
            "supply_id": supply.id,
            "supply_name": supply.name,
            "source": supply.source.code,
            "generator_type": None if generator_type is None else generator_type.code,
            "site_code": site.code,
            "site_name": site.name,
            "associated_site_codes": site_codes,
            "from": start_date,
            "to": finish_date,
            "pc": era.pc.code,
            "mtc": era.mtc_participant.mtc.code,
            "cop": era.cop.code,
            "ssc": None if ssc is None else ssc.code,
            "energisation_status": era.energisation_status.code,
            "properties": era.properties,
            "mop_contract": era.mop_contract.name,
            "mop_account": era.mop_account,
            "dc_contract": era.dc_contract.name,
            "dc_account": era.dc_account,
            "normal_reads": len(prime_reads),
            "type": era.meter_category,
            "supply_start": supply_start,
            "supply_finish": supply_finish,
            "import_llfc": None if imp_llfc is None else imp_llfc.code,
            "import_mpan_core": era.imp_mpan_core,
            "import_supply_capacity": era.imp_sc,
            "import_supplier": None
            if imp_supplier_contract is None
            else imp_supplier_contract.name,
            "export_llfc": None if exp_llfc is None else exp_llfc.code,
            "export_mpan_core": era.exp_mpan_core,
            "export_supply_capacity": era.exp_sc,
            "export_supplier": None
            if exp_supplier_contract is None
            else exp_supplier_contract.name,
        }
        values.update(
            mpan_bit(
                sess,
                supply,
                True,
                num_hh,
                era,
                chunk_start,
                chunk_finish,
                forecast_date,
                caches,
            )
        )
        values.update(
            mpan_bit(
                sess,
                supply,
                False,
                num_hh,
                era,
                chunk_start,
                chunk_finish,
                forecast_date,
                caches,
            )
        )

        w.writerow(csv_make_val(values[t]) for t in titles)

        # Avoid a long-running transaction
        sess.rollback()


def content(supply_id, start_date, finish_date, user, mpan_cores):
    caches = {}
    f = sess = None
    try:
        sess = Session()
        filter_str = "" if mpan_cores is None else "_filter"
        running_name, finished_name = chellow.dloads.make_names(
            f"supplies_duration{filter_str}.csv", user
        )
        f = open(running_name, mode="w", newline="")
        _process(sess, caches, f, start_date, finish_date, supply_id, mpan_cores)
    except BadRequest as e:
        era = caches.get("era")
        if era is None:
            pref = "Problem: "
        else:
            pref = f"Problem with era {chellow.utils.url_root}e/eras/{era.id}/edit : "
        f.write(pref + e.description)
    except BaseException as e:
        era = caches.get("era")
        if era is None:
            pref = "Problem: "
        else:
            pref = f"Problem with era {era.id}: "
        if f is not None:
            f.write(pref + str(e))
            f.write(traceback.format_exc())
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    start_date = req_hh_date("start")
    finish_date = req_hh_date("finish")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None
    if "mpan_cores" in request.values:
        mpan_cores_str = req_str("mpan_cores")
        mpan_cores = mpan_cores_str.splitlines()
        if len(mpan_cores) == 0:
            mpan_cores = None
        else:
            for i in range(len(mpan_cores)):
                mpan_cores[i] = parse_mpan_core(mpan_cores[i])
    else:
        mpan_cores = None

    args = supply_id, start_date, finish_date, g.user, mpan_cores
    thread = threading.Thread(target=content, args=args)
    thread.start()
    return chellow_redirect("/downloads", 303)
