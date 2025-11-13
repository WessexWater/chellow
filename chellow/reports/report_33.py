import csv
import sys
import threading
import traceback

from dateutil.relativedelta import relativedelta

from flask import g, redirect, request

from sqlalchemy import or_, text
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func, null

from werkzeug.exceptions import BadRequest

import chellow.e.duos
import chellow.e.tnuos
from chellow.dloads import open_file
from chellow.e.computer import SupplySource
from chellow.models import (
    Batch,
    Bill,
    Era,
    GeneratorType,
    MeasurementRequirement,
    MtcParticipant,
    RSession,
    ReadType,
    RegisterRead,
    SiteEra,
    Supply,
    User,
)
from chellow.utils import (
    CHANNEL_TYPES,
    HH,
    csv_make_val,
    hh_format,
    hh_min,
    parse_mpan_core,
    req_date,
    req_int,
    req_str,
)


def content(user_id, date, supply_id, mpan_cores):
    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("supplies_snapshot.csv", user, mode="w", newline="")
            _process(sess, f, date, supply_id, mpan_cores)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        f.write(msg)
    finally:
        if f is not None:
            f.close()


def _process_era(caches, sess, era_id, date, year_start):
    NORMAL_READ_TYPES = ("N", "C", "N3")

    era, supply, generator_type = (
        sess.query(Era, Supply, GeneratorType)
        .join(Supply, Era.supply_id == Supply.id)
        .outerjoin(GeneratorType, Supply.generator_type_id == GeneratorType.id)
        .filter(Era.id == era_id)
        .options(
            joinedload(Era.channels),
            joinedload(Era.cop),
            joinedload(Era.comm),
            joinedload(Era.dc_contract),
            joinedload(Era.exp_llfc),
            joinedload(Era.exp_supplier_contract),
            joinedload(Era.imp_llfc),
            joinedload(Era.imp_supplier_contract),
            joinedload(Era.mop_contract),
            joinedload(Era.mtc_participant).joinedload(MtcParticipant.mtc),
            joinedload(Era.mtc_participant).joinedload(MtcParticipant.meter_type),
            joinedload(Era.pc),
            joinedload(Era.site_eras).joinedload(SiteEra.site),
            joinedload(Era.ssc),
            joinedload(Era.energisation_status),
            joinedload(Era.supply).joinedload(Supply.source),
            joinedload(Era.supply).joinedload(Supply.gsp_group),
            joinedload(Era.supply).joinedload(Supply.dno),
        )
        .one()
    )

    site_codes = []
    site_names = []
    for site_era in era.site_eras:
        if site_era.is_physical:
            physical_site = site_era.site
        else:
            site = site_era.site
            site_codes.append(site.code)
            site_names.append(site.name)

    sup_eras = (
        sess.query(Era).filter(Era.supply == supply).order_by(Era.start_date).all()
    )
    supply_start_date = sup_eras[0].start_date
    supply_finish_date = sup_eras[-1].finish_date

    if era.imp_mpan_core is None:
        voltage_level_code = era.exp_llfc.voltage_level.code
        is_substation = era.exp_llfc.is_substation
    else:
        voltage_level_code = era.imp_llfc.voltage_level.code
        is_substation = era.imp_llfc.is_substation

    if generator_type is None:
        generator_type_str = ""
    else:
        generator_type_str = generator_type.code

    metering_type = era.meter_category

    if metering_type in ("nhh", "amr"):
        latest_prev_normal_read = (
            sess.query(RegisterRead)
            .join(Bill)
            .join(RegisterRead.previous_type)
            .filter(
                ReadType.code.in_(NORMAL_READ_TYPES),
                RegisterRead.previous_date <= date,
                Bill.supply_id == supply.id,
            )
            .order_by(RegisterRead.previous_date.desc())
            .options(joinedload(RegisterRead.previous_type))
            .first()
        )

        latest_pres_normal_read = (
            sess.query(RegisterRead)
            .join(Bill)
            .join(RegisterRead.present_type)
            .filter(
                ReadType.code.in_(NORMAL_READ_TYPES),
                RegisterRead.present_date <= date,
                Bill.supply == supply,
            )
            .order_by(RegisterRead.present_date.desc())
            .options(joinedload(RegisterRead.present_type))
            .first()
        )

        if latest_prev_normal_read is None and latest_pres_normal_read is None:
            latest_normal_read_date = None
            latest_normal_read_type = None
        elif latest_pres_normal_read is not None and latest_prev_normal_read is None:
            latest_normal_read_date = latest_pres_normal_read.present_date
            latest_normal_read_type = latest_pres_normal_read.present_type.code
        elif latest_pres_normal_read is None and latest_prev_normal_read is not None:
            latest_normal_read_date = latest_prev_normal_read.previous_date
            latest_normal_read_type = latest_prev_normal_read.previous_type.code
        elif (
            latest_pres_normal_read.present_date > latest_prev_normal_read.previous_date
        ):
            latest_normal_read_date = latest_pres_normal_read.present_date
            latest_normal_read_type = latest_pres_normal_read.present_type.code
        else:
            latest_normal_read_date = latest_prev_normal_read.previous_date
            latest_normal_read_type = latest_prev_normal_read.previous_type.code
        if latest_normal_read_date is not None:
            latest_normal_read_date = hh_format(latest_normal_read_date)

    else:
        latest_normal_read_date = metering_type
        latest_normal_read_type = None

    mop_contract = era.mop_contract
    mop_contract_name = mop_contract.name
    latest_mop_bill_date = (
        sess.query(Bill.finish_date)
        .join(Batch)
        .filter(
            Bill.start_date <= date,
            Bill.supply == supply,
            Batch.contract == mop_contract,
        )
        .order_by(Bill.finish_date.desc())
        .first()
    )

    if latest_mop_bill_date is not None:
        latest_mop_bill_date = hh_format(latest_mop_bill_date[0])

    dc_contract = era.dc_contract
    dc_contract_name = dc_contract.name
    latest_dc_bill_date = (
        sess.query(Bill.finish_date)
        .join(Batch)
        .filter(
            Bill.start_date <= date,
            Bill.supply == supply,
            Batch.contract == dc_contract,
        )
        .order_by(Bill.finish_date.desc())
        .first()
    )

    if latest_dc_bill_date is not None:
        latest_dc_bill_date = hh_format(latest_dc_bill_date[0])

    channel_values = []
    for imp_related in [True, False]:
        for channel_type in CHANNEL_TYPES:
            if era.find_channel(sess, imp_related, channel_type) is None:
                channel_values.append("false")
            else:
                channel_values.append("true")

    imp_avg_months = None
    exp_avg_months = None
    for is_import in [True, False]:
        if metering_type == "nhh":
            continue

        params = {
            "supply_id": supply.id,
            "year_start": year_start,
            "year_finish": date,
            "is_import": is_import,
        }
        month_mds = tuple(
            md[0] * 2
            for md in sess.execute(
                text(
                    """

select max(hh_datum.value) as md
from hh_datum join channel on (hh_datum.channel_id = channel.id)
join era on (channel.era_id = era.id)
where era.supply_id = :supply_id and hh_datum.start_date >= :year_start
and hh_datum.start_date <= :year_finish
and channel.channel_type = 'ACTIVE'
and channel.imp_related = :is_import
group by extract(month from (hh_datum.start_date at time zone 'utc'))
order by md desc
limit 3

"""
                ),
                params=params,
            )
        )

        avg_months = sum(month_mds)
        if len(month_mds) > 0:
            avg_months /= len(month_mds)
            if is_import:
                imp_avg_months = avg_months
            else:
                exp_avg_months = avg_months

    if (imp_avg_months is not None and imp_avg_months > 100) or (
        exp_avg_months is not None and exp_avg_months > 100
    ):
        mandatory_hh = "yes"
    else:
        mandatory_hh = "no"

    imp_latest_supplier_bill_date = None
    exp_latest_supplier_bill_date = None
    imp_tnuos_band = None
    for is_import in (True, False):
        for er in (
            sess.query(Era)
            .filter(Era.supply == era.supply, Era.start_date <= date)
            .order_by(Era.start_date.desc())
        ):
            if is_import:
                if er.imp_mpan_core is None:
                    break
                else:
                    supplier_contract = er.imp_supplier_contract
                    if era.energisation_status.code == "E":
                        imp_ss = SupplySource(
                            sess, date, date, date + HH, era, True, caches
                        )
                        chellow.e.duos.duos_vb(imp_ss)
                        hh = imp_ss.hh_data[0]
                        if hh["start-date"] >= chellow.e.tnuos.BANDED_START:
                            imp_tnuos_band = chellow.e.tnuos.BAND_LOOKUP[
                                hh["duos-description"]
                            ]
            else:
                if er.exp_mpan_core is None:
                    break
                else:
                    supplier_contract = er.exp_supplier_contract

            latest_bill_date = (
                sess.query(Bill.finish_date)
                .join(Batch)
                .filter(
                    Bill.finish_date >= er.start_date,
                    Bill.finish_date <= hh_min(er.finish_date, date),
                    Bill.supply == supply,
                    Batch.contract == supplier_contract,
                )
                .order_by(Bill.finish_date.desc())
                .first()
            )

            if latest_bill_date is not None:
                latest_bill_date = hh_format(latest_bill_date[0])

                if is_import:
                    imp_latest_supplier_bill_date = latest_bill_date
                else:
                    exp_latest_supplier_bill_date = latest_bill_date
                break

    meter_installation_date = (
        sess.query(func.min(Era.start_date))
        .filter(Era.supply == era.supply, Era.msn == era.msn)
        .one()[0]
    )

    ssc = era.ssc
    if ssc is None:
        ssc_code = ssc_description = num_registers = None
    else:
        ssc_code, ssc_description = ssc.code, ssc.description
        num_registers = (
            sess.query(MeasurementRequirement)
            .filter(MeasurementRequirement.ssc == ssc)
            .count()
        )

    return (
        [
            date,
            era.imp_mpan_core,
            era.exp_mpan_core,
            physical_site.code,
            physical_site.name,
            ", ".join(site_codes),
            ", ".join(site_names),
            supply.id,
            supply.source.code,
            generator_type_str,
            supply.gsp_group.code,
            supply.dno.dno_code,
            voltage_level_code,
            is_substation,
            metering_type,
            mandatory_hh,
            era.pc.code,
            era.mtc_participant.mtc.code,
            era.cop.code,
            era.comm.code,
            ssc_code,
            ssc_description,
            era.energisation_status.code,
            num_registers,
            mop_contract_name,
            dc_contract_name,
            era.msn,
            meter_installation_date,
            latest_normal_read_date,
            latest_normal_read_type,
            latest_dc_bill_date,
            latest_mop_bill_date,
            supply_start_date,
            supply_finish_date,
            None if era.dtc_meter_type is None else era.dtc_meter_type.code,
            imp_tnuos_band,
        ]
        + channel_values
        + [
            era.imp_sc,
            None if era.imp_llfc is None else era.imp_llfc.code,
            None if era.imp_llfc is None else era.imp_llfc.description,
            (
                None
                if era.imp_supplier_contract is None
                else era.imp_supplier_contract.name
            ),
            era.imp_supplier_account,
            imp_avg_months,
            imp_latest_supplier_bill_date,
        ]
        + [
            era.exp_sc,
            None if era.exp_llfc is None else era.exp_llfc.code,
            None if era.exp_llfc is None else era.exp_llfc.description,
            (
                None
                if era.exp_supplier_contract is None
                else era.exp_supplier_contract.name
            ),
            era.exp_supplier_account,
            exp_avg_months,
            exp_latest_supplier_bill_date,
        ]
    )


def _process(sess, f, date, supply_id, mpan_cores):
    writer = csv.writer(f, lineterminator="\n")
    titles = (
        "Date",
        "Import MPAN Core",
        "Export MPAN Core",
        "Physical Site Id",
        "Physical Site Name",
        "Other Site Ids",
        "Other Site Names",
        "Supply Id",
        "Source",
        "Generator Type",
        "GSP Group",
        "DNO Name",
        "Voltage Level",
        "Is Substations",
        "Metering Type",
        "Mandatory HH",
        "PC",
        "MTC",
        "CoP",
        "Comms Type",
        "SSC Code",
        "SSC Description",
        "Energisation Status",
        "Number Of Registers",
        "MOP Contract",
        "DC Contract",
        "Meter Serial Number",
        "Meter Installation Date",
        "Latest Normal Meter Read Date",
        "Latest Normal Meter Read Type",
        "Latest DC Bill Date",
        "Latest MOP Bill Date",
        "Supply Start Date",
        "Supply Finish Date",
        "DTC Meter Type",
        "tnuos_band",
        "Import ACTIVE?",
        "Import REACTIVE_IMPORT?",
        "Import REACTIVE_EXPORT?",
        "Export ACTIVE?",
        "Export REACTIVE_IMPORT?",
        "Export REACTIVE_EXPORT?",
        "Import Agreed Supply Capacity (kVA)",
        "Import LLFC Code",
        "Import LLFC Description",
        "Import Supplier Contract",
        "Import Supplier Account",
        "Import Mandatory kW",
        "Latest Import Supplier Bill Date",
        "Export Agreed Supply Capacity (kVA)",
        "Export LLFC Code",
        "Export LLFC Description",
        "Export Supplier Contract",
        "Export Supplier Account",
        "Export Mandatory kW",
        "Latest Export Supplier Bill Date",
    )
    writer.writerow(titles)

    year_start = date + HH - relativedelta(years=1)
    caches = {}

    era_ids = (
        sess.query(Era.id)
        .filter(
            Era.start_date <= date,
            or_(Era.finish_date == null(), Era.finish_date >= date),
        )
        .order_by(Era.supply_id)
    )

    if supply_id is not None:
        supply = Supply.get_by_id(sess, supply_id)

        era_ids = era_ids.filter(Era.supply == supply)

    if mpan_cores is not None:
        era_ids = era_ids.filter(
            or_(Era.imp_mpan_core.in_(mpan_cores), Era.exp_mpan_core.in_(mpan_cores))
        )

    for (era_id,) in era_ids:
        try:
            vals = _process_era(caches, sess, era_id, date, year_start)
        except BaseException as e:
            raise BadRequest(f"Problem with era {era_id}: {e}") from e
        except BadRequest as e:
            raise BadRequest(f"Problem with era {era_id}: {e.description}")
        writer.writerow([csv_make_val(v) for v in vals])

        # Avoid a long-running transaction
        sess.rollback()


def do_get(session):
    user = g.user
    date = req_date("date")
    if "supply_id" in request.values:
        supply_id = req_int("supply_id")
    else:
        supply_id = None

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

    args = user.id, date, supply_id, mpan_cores
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
