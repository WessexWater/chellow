import csv
import datetime
import threading
import traceback
from decimal import Decimal

from sqlalchemy import null, or_, select
from sqlalchemy.sql.expression import false

from werkzeug.exceptions import BadRequest

from zish import loads

from chellow.models import (
    Bill,
    BillType,
    Channel,
    Comm,
    Contract,
    Cop,
    DtcMeterType,
    EnergisationStatus,
    Era,
    GContract,
    GEra,
    GExitZone,
    GReadType,
    GReadingFrequency,
    GSupply,
    GUnit,
    GeneratorType,
    GspGroup,
    HhDatum,
    Llfc,
    MarketRole,
    MeterType,
    Participant,
    Party,
    Pc,
    ReadType,
    RegisterRead,
    Session,
    Site,
    Snag,
    Source,
    Ssc,
    Supply,
    Tpr,
    User,
    UserRole,
    VoltageLevel,
)
from chellow.utils import (
    hh_format,
    parse_bool,
    parse_channel_type,
    parse_hh_start,
    parse_mpan_core,
    parse_pc_code,
)


process_id = 0
process_lock = threading.Lock()
processes = {}

NO_CHANGE = "{no change}"

CHANNEL_TYPES = ("ACTIVE", "REACTIVE_IMP", "REACTIVE_EXP")


def add_arg(args, name, values, index):
    if index >= len(values):
        raise BadRequest(f"Another field called {name} needs to be added on the end.")

    value = values[index].strip()
    args.append((name, value))
    return value


ALLOWED_ACTIONS = ("insert", "update", "delete")


def general_import_era(sess, action, vals, args):
    if action == "update":
        mpan_core_str = add_arg(args, "mpan_core", vals, 0)
        mpan_core = parse_mpan_core(mpan_core_str)
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        date_str = add_arg(args, "date", vals, 1)
        dt = parse_hh_start(date_str)
        era = supply.find_era_at(sess, dt)
        if era is None:
            raise BadRequest("There isn't a era at this date.")

        start_date_str = add_arg(args, "Start date", vals, 2)
        if start_date_str == NO_CHANGE:
            start_date = era.start_date
        else:
            start_date = parse_hh_start(start_date_str)

        finish_date_str = add_arg(args, "Finish date", vals, 3)
        if finish_date_str == NO_CHANGE:
            finish_date = era.finish_date
        else:
            finish_date = parse_hh_start(finish_date_str)

        mop_contract = None
        mop_contract_name = add_arg(args, "MOP Contract", vals, 4)
        if mop_contract_name == NO_CHANGE:
            mop_contract = era.mop_contract
        elif len(mop_contract_name) > 0:
            mop_contract = Contract.get_mop_by_name(sess, mop_contract_name)

        mop_account = add_arg(args, "MOP Account", vals, 5)
        if mop_account == NO_CHANGE:
            mop_account = era.mop_account

        dc_contract = None
        dc_contract_name = add_arg(args, "DC Contract", vals, 6)
        if dc_contract_name == NO_CHANGE:
            dc_contract = era.dc_contract
        elif len(dc_contract_name) > 0:
            dc_contract = Contract.get_dc_by_name(sess, dc_contract_name)

        dc_account = add_arg(args, "DC account", vals, 7)
        if dc_account == NO_CHANGE:
            dc_account = era.dc_account

        msn = add_arg(args, "Meter Serial Number", vals, 8)
        if msn == NO_CHANGE:
            msn = era.msn

        pc_code_raw = add_arg(args, "Profile Class", vals, 9)
        if pc_code_raw == NO_CHANGE:
            pc = era.pc
        else:
            pc_code = parse_pc_code(pc_code_raw)
            pc = Pc.get_by_code(sess, pc_code)

        mtc_code_raw = add_arg(args, "Meter Timeswitch Class", vals, 10)
        if mtc_code_raw == NO_CHANGE:
            mtc_code = era.mtc_participant.mtc.code
        else:
            mtc_code = mtc_code_raw

        cop_code = add_arg(args, "CoP", vals, 11)
        cop = era.cop if cop_code == NO_CHANGE else Cop.get_by_code(sess, cop_code)

        comm_code = add_arg(args, "Comms Type", vals, 12)
        comm = era.comm if comm_code == NO_CHANGE else Comm.get_by_code(sess, comm_code)

        ssc_code_str = add_arg(args, "SSC", vals, 13)
        if ssc_code_str == NO_CHANGE:
            ssc_code = None if era.ssc is None else era.ssc.code
        elif len(ssc_code_str) == 0:
            ssc_code = None
        else:
            ssc_code = ssc_code_str

        es_code = add_arg(args, "Energisation Status", vals, 14)
        if es_code == NO_CHANGE:
            es = era.energisation_status
        else:
            es = EnergisationStatus.get_by_code(sess, es_code)

        dtc_meter_type_code = add_arg(args, "DTC Meter Type", vals, 15)
        if dtc_meter_type_code == NO_CHANGE:
            dtc_meter_type = era.dtc_meter_type
        else:
            dtc_meter_type = DtcMeterType.get_by_code(sess, dtc_meter_type_code)

        imp_mpan_core = add_arg(args, "Import MPAN Core", vals, 16)
        imp_llfc_code = None
        imp_sc = None
        imp_supplier_contract = None
        imp_supplier_account = None
        if imp_mpan_core == NO_CHANGE:
            imp_mpan_core = era.imp_mpan_core
        elif len(imp_mpan_core) == 0:
            imp_mpan_core = None

        if imp_mpan_core is not None:
            imp_llfc_code = add_arg(args, "Import LLFC", vals, 17)
            if imp_llfc_code == NO_CHANGE:
                imp_llfc_code = era.imp_llfc.code

            imp_sc_str = add_arg(args, "Import Agreed Supply Capacity", vals, 18)
            if imp_sc_str == NO_CHANGE:
                imp_sc = era.imp_sc
            else:
                try:
                    imp_sc = int(imp_sc_str)
                except ValueError as e:
                    raise BadRequest(
                        f"The import agreed supply capacity must be an integer. {e}"
                    )

            imp_supplier_contract_name = add_arg(
                args, "Import Supplier Contract", vals, 19
            )
            if imp_supplier_contract_name == NO_CHANGE:
                imp_supplier_contract = era.imp_supplier_contract
            else:
                imp_supplier_contract = Contract.get_supplier_by_name(
                    sess, imp_supplier_contract_name
                )

            imp_supplier_account = add_arg(args, "Import Supplier Account", vals, 20)
            if imp_supplier_account == NO_CHANGE:
                imp_supplier_account = era.imp_supplier_account

        exp_mpan_core = None
        exp_llfc_code = None
        exp_supplier_contract = None
        exp_supplier_account = None
        exp_sc = None
        if len(vals) > 21:
            exp_mpan_core = add_arg(args, "Export MPAN Core", vals, 21)
            if exp_mpan_core == NO_CHANGE:
                exp_mpan_core = era.exp_mpan_core
            elif len(exp_mpan_core) == 0:
                exp_mpan_core = None

            if exp_mpan_core is not None:
                exp_llfc_code = add_arg(args, "Export LLFC", vals, 22)
                if exp_llfc_code == NO_CHANGE:
                    exp_llfc_code = era.exp_llfc.code

                exp_sc_str = add_arg(args, "Export Agreed Supply Capacity", vals, 23)
                if exp_sc_str == NO_CHANGE:
                    exp_sc = era.exp_sc
                else:
                    try:
                        exp_sc = int(exp_sc_str)
                    except ValueError as e:
                        raise BadRequest(
                            f"The export supply capacity must be an integer. {e}"
                        )

                exp_supplier_contract_name = add_arg(
                    args, "Export Supplier Contract", vals, 24
                )
                if exp_supplier_contract_name == NO_CHANGE:
                    exp_supplier_contract = era.exp_supplier_contract
                else:
                    exp_supplier_contract = Contract.get_supplier_by_name(
                        sess, exp_supplier_contract_name
                    )

                exp_supplier_account = add_arg(
                    args, "Export Supplier Account", vals, 25
                )
                if exp_supplier_account == NO_CHANGE:
                    exp_supplier_account = era.exp_supplier_account

        supply.update_era(
            sess,
            era,
            start_date,
            finish_date,
            mop_contract,
            mop_account,
            dc_contract,
            dc_account,
            msn,
            pc,
            mtc_code,
            cop,
            comm,
            ssc_code,
            es,
            dtc_meter_type,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            imp_supplier_account,
            imp_sc,
            exp_mpan_core,
            exp_llfc_code,
            exp_supplier_contract,
            exp_supplier_account,
            exp_sc,
        )
    elif action == "delete":
        mpan_core = add_arg(args, "MPAN Core", vals, 0)
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        date_str = add_arg(args, "Date", vals, 1)
        dt = parse_hh_start(date_str)
        era = supply.find_era_at(sess, dt)
        if era is None:
            raise BadRequest("There isn't a era at this date.")

        supply.delete_era(sess, era)
    elif action == "insert":
        channel_set = set()
        mpan_core = add_arg(args, "MPAN Core", vals, 0)
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        start_date_str = add_arg(args, "Start date", vals, 1)
        if len(start_date_str) == 0:
            start_date = None
        else:
            start_date = parse_hh_start(start_date_str)
        existing_era = (
            sess.query(Era)
            .filter(
                Era.supply == supply,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            )
            .order_by(Era.start_date)
            .first()
        )
        if existing_era is None:
            raise BadRequest("The start date is after end of the supply.")

        site_code = add_arg(args, "Site Code", vals, 2)
        physical_site = None
        logical_sites = []
        if site_code == NO_CHANGE:
            for site_era in existing_era.site_eras:
                if site_era.is_physical:
                    physical_site = site_era.site
                else:
                    logical_sites.append(site_era.site)
        else:
            physical_site = Site.get_by_code(sess, site_code)

        mop_contract_name = add_arg(args, "MOP Contract", vals, 3)
        if mop_contract_name == NO_CHANGE:
            mop_contract = existing_era.mop_contract
        else:
            mop_contract = Contract.get_mop_by_name(sess, mop_contract_name)

        mop_account = add_arg(args, "MOP Account Reference", vals, 4)
        if mop_account == NO_CHANGE:
            mop_account = existing_era.mop_account

        dc_contract_name = add_arg(args, "DC Contract", vals, 5)
        if dc_contract_name == NO_CHANGE:
            dc_contract = existing_era.dc_contract
        else:
            dc_contract = Contract.get_dc_by_name(sess, dc_contract_name)

        dc_account = add_arg(args, "DC Account Reference", vals, 6)
        if dc_account == NO_CHANGE:
            dc_account = existing_era.dc_account

        msn = add_arg(args, "Meter Serial Number", vals, 7)
        if msn == NO_CHANGE:
            msn = existing_era.msn

        pc_code_raw = add_arg(args, "Profile Class", vals, 8)
        if pc_code_raw == NO_CHANGE:
            pc = existing_era.pc
        else:
            pc_code = parse_pc_code(pc_code_raw)
            pc = Pc.get_by_code(sess, pc_code)

        mtc_code_raw = add_arg(args, "Meter Timeswitch Class", vals, 9)
        if mtc_code_raw == NO_CHANGE:
            mtc_code = existing_era.mtc_participant.mtc.code
        else:
            mtc_code = mtc_code_raw

        cop_code = add_arg(args, "CoP", vals, 10)
        if cop_code == NO_CHANGE:
            cop = existing_era.cop
        else:
            cop = Cop.get_by_code(sess, cop_code)

        comm_code = add_arg(args, "Comms Type", vals, 11)
        if comm_code == NO_CHANGE:
            comm = existing_era.comm
        else:
            comm = Comm.get_by_code(sess, comm_code)

        ssc_code = add_arg(args, "Standard Settlement Configuration", vals, 12)
        if ssc_code == NO_CHANGE:
            ssc = existing_era.ssc
            if ssc is None:
                ssc_code = None
            else:
                ssc_code = ssc.code
        elif len(ssc_code) > 0:
            Ssc.get_by_code(sess, ssc_code)
        else:
            ssc_code = None

        es_code = add_arg(args, "Energisation Status", vals, 13)
        if es_code == NO_CHANGE:
            energisation_status = existing_era.energisation_status
        else:
            energisation_status = EnergisationStatus.get_by_code(sess, es_code)

        dtc_meter_type_code = add_arg(args, "DTC Meter Type", vals, 14)
        if dtc_meter_type_code == NO_CHANGE:
            dtc_meter_type = existing_era.dtc_meter_type
        else:
            dtc_meter_type = DtcMeterType.get_by_code(sess, dtc_meter_type_code)

        imp_mpan_core = add_arg(args, "Import MPAN Core", vals, 15)
        if imp_mpan_core == NO_CHANGE:
            imp_mpan_core = existing_era.imp_mpan_core
        elif len(imp_mpan_core) == 0:
            imp_mpan_core = None

        imp_supplier_contract = None
        imp_supplier_account = None
        imp_sc = None
        imp_llfc_code = None
        imp_supplier_contract_name = None

        if imp_mpan_core is not None:
            imp_llfc_code = add_arg(args, "Import Line Loss Factor Class", vals, 16)
            if imp_llfc_code == NO_CHANGE and existing_era.imp_llfc is not None:
                imp_llfc_code = existing_era.imp_llfc.code

            imp_sc_str = add_arg(args, "Import Agreed Supply Capacity", vals, 17)
            if imp_sc_str == NO_CHANGE:
                imp_sc = existing_era.imp_sc
            else:
                try:
                    imp_sc = int(imp_sc_str)
                except ValueError as e:
                    raise BadRequest(
                        f"The import agreed supply capacity must be an integer. {e}"
                    )

            imp_supplier_contract_name = add_arg(
                args, "Import Supplier Contract", vals, 18
            )
            if imp_supplier_contract_name == NO_CHANGE:
                imp_supplier_contract = existing_era.imp_supplier_contract
            else:
                imp_supplier_contract = Contract.get_supplier_by_name(
                    sess, imp_supplier_contract_name
                )

            imp_supplier_account = add_arg(
                args, "Import Supplier Account Reference", vals, 19
            )
            if imp_supplier_account == NO_CHANGE:
                imp_supplier_account = existing_era.imp_supplier_account

            for i, ctype in enumerate(CHANNEL_TYPES):
                field_name = f"Import {ctype}?"
                has_chan_str = add_arg(args, field_name, vals, i + 20)
                if has_chan_str == NO_CHANGE:
                    if existing_era.find_channel(sess, True, ctype) is not None:
                        channel_set.add((True, ctype))
                elif parse_bool(has_chan_str):
                    channel_set.add((True, ctype))

        exp_mpan_core = None
        exp_llfc_code = None
        exp_supplier_contract = None
        exp_supplier_account = None
        exp_sc = None

        if len(vals) > 23:
            exp_mpan_core = add_arg(args, "Export MPAN", vals, 23)
            if exp_mpan_core == NO_CHANGE:
                exp_mpan_core = existing_era.exp_mpan_core
            elif len(exp_mpan_core) == 0:
                exp_mpan_core = None

            if exp_mpan_core is not None:
                exp_llfc_code = add_arg(args, "Export LLFC", vals, 24)
                if exp_llfc_code == NO_CHANGE and existing_era.exp_llfc is not None:
                    exp_llfc_code = existing_era.exp_llfc.code

                exp_sc_str = add_arg(args, "Export Agreed Supply Capacity", vals, 25)
                if exp_sc_str == NO_CHANGE:
                    exp_sc = existing_era.exp_sc
                else:
                    try:
                        exp_sc = int(exp_sc_str)
                    except ValueError as e:
                        raise BadRequest(
                            f"The export supply capacity must be an integer. {e}"
                        )

                exp_supplier_contract_name = add_arg(
                    args, "Export Supplier Contract", vals, 26
                )
                if exp_supplier_contract_name == NO_CHANGE:
                    exp_supplier_contract = existing_era.exp_supplier_contract
                else:
                    exp_supplier_contract = Contract.get_supplier_by_name(
                        sess, exp_supplier_contract_name
                    )

                exp_supplier_account = add_arg(
                    args, "Export Supplier Account", vals, 27
                )
                if exp_supplier_account == NO_CHANGE:
                    exp_supplier_account = existing_era.exp_supplier_account

                for i, ctype in enumerate(CHANNEL_TYPES):
                    field_name = f"Export {ctype}?"
                    has_chan_str = add_arg(args, field_name, vals, i + 28)
                    if has_chan_str == NO_CHANGE:
                        if existing_era.find_channel(sess, False, ctype) is not None:
                            channel_set.add((False, ctype))
                    elif parse_bool(has_chan_str):
                        channel_set.add((False, ctype))

        supply.insert_era(
            sess,
            physical_site,
            logical_sites,
            start_date,
            None,
            mop_contract,
            mop_account,
            dc_contract,
            dc_account,
            msn,
            pc,
            mtc_code,
            cop,
            comm,
            ssc_code,
            energisation_status,
            dtc_meter_type,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            imp_supplier_account,
            imp_sc,
            exp_mpan_core,
            exp_llfc_code,
            exp_supplier_contract,
            exp_supplier_account,
            exp_sc,
            channel_set,
        )


def general_import_g_supply(sess, action, vals, args):
    if action == "insert":
        site_code = add_arg(args, "Site Code", vals, 0)
        site = Site.get_by_code(sess, site_code)
        mprn = add_arg(args, "MPRN", vals, 1)
        supply_name = add_arg(args, "Supply Name", vals, 2)
        g_exit_zone_code = add_arg(args, "Exit Zone", vals, 3)
        g_exit_zone = GExitZone.get_by_code(sess, g_exit_zone_code)
        start_date_str = add_arg(args, "Start Date", vals, 4)
        start_date = parse_hh_start(start_date_str)
        finish_date_str = add_arg(args, "Finish Date", vals, 5)
        finish_date = parse_hh_start(finish_date_str)
        msn = add_arg(args, "Meter Serial Number", vals, 6)
        correction_factor_str = add_arg(args, "Correction Factor", vals, 7)
        correction_factor = Decimal(correction_factor_str)
        g_unit_code = add_arg(args, "Unit of Measurement", vals, 8)
        g_unit = GUnit.get_by_code(sess, g_unit_code)
        g_contract_name = add_arg(args, "Supplier Contract", vals, 9)
        if len(g_contract_name) > 0:
            g_contract = GContract.get_supplier_by_name(sess, g_contract_name)
        else:
            g_contract = None
        account = add_arg(args, "Account", vals, 10)
        g_reading_frequency_code = add_arg(args, "Reading Frequency", vals, 11)
        g_reading_frequency = GReadingFrequency.get_by_code(
            sess, g_reading_frequency_code
        )
        aq_str = add_arg(args, "AQ", vals, 12)
        aq = Decimal(aq_str)
        soq_str = add_arg(args, "SOQ", vals, 13)
        soq = Decimal(soq_str)

        site.insert_g_supply(
            sess,
            mprn,
            supply_name,
            g_exit_zone,
            start_date,
            finish_date,
            msn,
            correction_factor,
            g_unit,
            g_contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )
        sess.flush()
    elif action == "update":
        existing_mprn = add_arg(args, "Existing MPRN", vals, 0)
        g_supply = GSupply.get_by_mprn(sess, existing_mprn)
        mprn = add_arg(args, "MPRN", vals, 0)
        mprn = g_supply.mprn if mprn == NO_CHANGE else mprn
        g_supply_name = add_arg(args, "Supply Name", vals, 4)
        if g_supply_name == NO_CHANGE:
            g_supply_name = g_supply.name
        g_supply.update(mprn, supply_name)
        sess.flush()
    elif action == "delete":
        mprn = add_arg(args, "MPRN", vals, 0)
        g_supply = GSupply.get_by_mprn(sess, mprn)
        g_supply.delete()
        sess.flush()


def general_import_g_era(sess, action, vals, args):
    if action == "insert":
        mprn = add_arg(args, "MPRN", vals, 0)
        g_supply = GSupply.get_by_mprn(sess, mprn)
        start_date_str = add_arg(args, "Start Date", vals, 1)
        if len(start_date_str) == 0:
            start_date = None
        else:
            start_date = parse_hh_start(start_date_str)

        existing_g_era = sess.scalars(
            select(GEra).where(
                GEra.g_supply == g_supply,
                GEra.start_date <= start_date,
                or_(GEra.finish_date == null(), GEra.finish_date >= start_date),
            )
        ).one_or_none()
        if existing_g_era is None:
            raise BadRequest("The start date is outside the dates of the supply.")

        site_code = add_arg(args, "Site Code", vals, 2)
        physical_site = None
        logical_sites = []
        if site_code == NO_CHANGE:
            for site_g_era in existing_g_era.site_g_eras:
                if site_g_era.is_physical:
                    physical_site = site_g_era.site
                else:
                    logical_sites.append(site_g_era.site)
        else:
            physical_site = Site.get_by_code(sess, site_code)

        msn = add_arg(args, "Meter Serial Number", vals, 3)
        if msn == NO_CHANGE:
            msn = existing_g_era.msn

        correction_factor_str = add_arg(args, "Correction Factor", vals, 4)
        if correction_factor_str == NO_CHANGE:
            correction_factor = existing_g_era.correction_factor
        else:
            correction_factor = Decimal(correction_factor_str)

        g_unit_code = add_arg(args, "Unit", vals, 5)
        if g_unit_code == NO_CHANGE:
            g_unit = existing_g_era.g_unit
        else:
            g_unit = GUnit.get_by_code(sess, g_unit_code)

        contract_name = add_arg(args, "Supplier Contract Name", vals, 6)
        if contract_name == NO_CHANGE:
            g_contract = existing_g_era.g_contract
        else:
            g_contract = GContract.get_supplier_by_name(sess, contract_name)

        account = add_arg(args, "Account", vals, 7)
        if account == NO_CHANGE:
            account = existing_g_era.account

        g_reading_frequency_code = add_arg(args, "Reading Frequency", vals, 8)
        if g_reading_frequency_code == NO_CHANGE:
            g_reading_frequency = existing_g_era.g_reading_frequency
        else:
            g_reading_frequency = GReadingFrequency.get_by_code(
                sess, g_reading_frequency_code
            )

        aq_str = add_arg(args, "AQ", vals, 9)
        aq = existing_g_era.aq if aq_str == NO_CHANGE else Decimal(aq_str)

        soq_str = add_arg(args, "SOQ", vals, 10)
        soq = existing_g_era.soq if soq_str == NO_CHANGE else Decimal(soq_str)

        g_supply.insert_g_era(
            sess,
            physical_site,
            logical_sites,
            start_date,
            None,
            msn,
            correction_factor,
            g_unit,
            g_contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )
        sess.flush()

    elif action == "update":
        mprn = add_arg(args, "MPRN", vals, 0)
        g_supply = GSupply.get_by_mprn(sess, mprn)
        date_str = add_arg(args, "date", vals, 1)
        dt = parse_hh_start(date_str)
        g_era = g_supply.find_g_era_at(sess, dt)
        if g_era is None:
            raise BadRequest("There isn't a gas era at this date.")

        start_date_str = add_arg(args, "Start Date", vals, 2)
        if start_date_str == NO_CHANGE:
            start_date = g_era.start_date
        else:
            start_date = parse_hh_start(start_date_str)

        finish_date_str = add_arg(args, "Finish Date", vals, 3)
        if finish_date_str == NO_CHANGE:
            finish_date = g_era.finish_date
        else:
            finish_date = parse_hh_start(finish_date_str)

        msn = add_arg(args, "Meter Serial Number", vals, 4)
        if msn == NO_CHANGE:
            msn = g_era.msn

        correction_factor_str = add_arg(args, "Correction Factor", vals, 5)
        if correction_factor_str == NO_CHANGE:
            correction_factor = g_era.correction_factor
        else:
            correction_factor = Decimal(correction_factor_str)

        g_unit_code = add_arg(args, "Unit", vals, 6)
        if g_unit_code == NO_CHANGE:
            g_unit = g_era.g_unit
        else:
            g_unit = GUnit.get_by_code(sess, g_unit_code)

        contract_name = add_arg(args, "Supplier Contract Name", vals, 7)
        if contract_name == NO_CHANGE:
            g_contract = g_era.g_contract
        else:
            g_contract = GContract.get_supplier_by_name(sess, contract_name)

        account = add_arg(args, "Account", vals, 8)
        if account == NO_CHANGE:
            account = g_era.account

        g_reading_frequency_code = add_arg(args, "Reading Frequency", vals, 9)
        if g_reading_frequency_code == NO_CHANGE:
            g_reading_frequency = g_era.g_reading_frequency
        else:
            g_reading_frequency = GReadingFrequency.get_by_code(
                sess, g_reading_frequency_code
            )

        aq_str = add_arg(args, "AQ", vals, 10)
        aq = g_era.aq if aq_str == NO_CHANGE else Decimal(aq_str)

        soq_str = add_arg(args, "SOQ", vals, 11)
        soq = g_era.aq if soq_str == NO_CHANGE else Decimal(soq_str)

        g_supply.update_g_era(
            sess,
            g_era,
            start_date,
            finish_date,
            msn,
            correction_factor,
            g_unit,
            g_contract,
            account,
            g_reading_frequency,
            aq,
            soq,
        )
    elif action == "delete":
        mprn = add_arg(args, "MPRN", vals, 0)
        g_supply = GSupply.get_by_mprn(sess, mprn)
        date_str = add_arg(args, "Date", vals, 1)
        dt = parse_hh_start(date_str)
        g_era = g_supply.find_g_era_at(sess, dt)
        if g_era is None:
            raise BadRequest("There isn't a gas era at this date.")

        g_supply.delete_g_era(sess, g_era)
        sess.flush()


def general_import_g_batch(sess, action, vals, args):
    if action == "insert":
        contract_name = add_arg(args, "Supplier Contract Name", vals, 0)
        g_contract = GContract.get_supplier_by_name(sess, contract_name)

        reference = add_arg(args, "Reference", vals, 1)
        description = add_arg(args, "Description", vals, 2)
        g_contract.insert_g_batch(sess, reference, description)

    elif action == "update":
        contract_name = add_arg(args, "Supplier Contract Name", vals, 0)
        g_contract = GContract.get_supplier_by_name(sess, contract_name)

        old_reference = add_arg(args, "Old Reference", vals, 1)
        g_batch = g_contract.get_batch(sess, old_reference)
        new_reference = add_arg(args, "New Reference", vals, 2)
        description = add_arg(args, "Description", vals, 3)
        g_batch.update(sess, new_reference, description)


def general_import_party(sess, action, vals, args):
    if action == "insert":
        market_role_code = add_arg(args, "Market Role Code", vals, 0)
        market_role = MarketRole.get_by_code(sess, market_role_code)
        participant_code = add_arg(args, "Participant Code", vals, 1)
        participant = Participant.get_by_code(sess, participant_code)
        name = add_arg(args, "Name", vals, 2)
        valid_from_str = add_arg(args, "Valid From", vals, 3)
        valid_from = parse_hh_start(valid_from_str)
        valid_to_str = add_arg(args, "Valid To", vals, 4)
        valid_to = parse_hh_start(valid_to_str)
        dno_code_str = add_arg(args, "DNO Code", vals, 5)
        dno_code = None if len(dno_code_str) == 0 else dno_code_str
        party = Party(
            market_role=market_role,
            participant=participant,
            name=name,
            valid_from=valid_from,
            valid_to=valid_to,
            dno_code=dno_code,
        )
        sess.add(party)
        sess.flush()

    elif action == "update":
        market_role_code = add_arg(args, "Market Role Code", vals, 0)
        participant_code = add_arg(args, "Participant Code", vals, 1)
        party = Party.get_by_participant_code_role_code(
            sess, participant_code, market_role_code
        )
        name = add_arg(args, "Name", vals, 2)
        party.name = name
        valid_from_str = add_arg(args, "Valid From", vals, 3)
        party.valid_from = parse_hh_start(valid_from_str)
        valid_to_str = add_arg(args, "Valid To", vals, 4)
        party.valid_to = parse_hh_start(valid_to_str)
        dno_code_str = add_arg(args, "DNO Code", vals, 5)
        dno_code = None if len(dno_code_str) == 0 else dno_code_str
        party.dno_code = dno_code
        sess.flush()


def general_import_meter_type(sess, action, vals, args):
    if action == "insert":
        code = add_arg(args, "Code", vals, 0)
        description = add_arg(args, "Description", vals, 1)
        valid_from_str = add_arg(args, "Valid From", vals, 2)
        valid_from = parse_hh_start(valid_from_str)
        valid_to_str = add_arg(args, "Valid To", vals, 3)
        valid_to = parse_hh_start(valid_to_str)
        meter_type = MeterType(
            code=code, description=description, valid_from=valid_from, valid_to=valid_to
        )
        sess.add(meter_type)
        sess.flush()

    elif action == "update":
        code = add_arg(args, "Code", vals, 0)
        mt = sess.query(MeterType).filter(MeterType.code == code).first()
        description = add_arg(args, "Description", vals, 1)
        mt.description = description
        valid_from_str = add_arg(args, "Valid From", vals, 2)
        valid_from = parse_hh_start(valid_from_str)
        mt.valid_from = valid_from
        valid_to_str = add_arg(args, "Valid To", vals, 3)
        valid_to = parse_hh_start(valid_to_str)
        mt.valid_to = valid_to
        sess.flush()


def _parse_breakdown(breakdown_str):
    if len(breakdown_str) == 0:
        return {}
    else:
        try:
            return loads(breakdown_str)
        except SyntaxError as e:
            raise BadRequest("Problem parsing the breakdown: " + str(e))


def _truncate_vals(vals):
    return _truncate_vals(vals[:-1]) if len(vals) > 0 and vals[0] == "" else vals


def general_import_bill(sess, action, vals, args):
    vals = _truncate_vals(vals)
    if action == "insert":
        role_name = add_arg(args, "Role Name", vals, 0).lower()
        contract_name = add_arg(args, "Contract Name", vals, 1)

        if role_name == "dc":
            contract = Contract.get_dc_by_name(sess, contract_name)
        elif role_name == "supplier":
            contract = Contract.get_supplier_by_name(sess, contract_name)
        elif role_name == "mop":
            contract = Contract.get_mop_by_name(sess, contract_name)
        else:
            raise BadRequest("The role name must be one of dc, supplier or mop.")

        batch_reference = add_arg(args, "Batch Reference", vals, 2)

        batch = contract.get_batch(sess, batch_reference)
        mpan_core = add_arg(args, "Mpan Core", vals, 3)
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        issue_date_str = add_arg(args, "Issue Date", vals, 4)
        issue_date = parse_hh_start(issue_date_str)
        start_date_str = add_arg(args, "Start Date", vals, 5)
        start_date = parse_hh_start(start_date_str)
        finish_date_str = add_arg(args, "Finish Date", vals, 6)
        finish_date = parse_hh_start(finish_date_str)
        net_str = add_arg(args, "Net", vals, 7)
        net = Decimal(net_str)
        vat_str = add_arg(args, "Vat", vals, 8)
        vat = Decimal(vat_str)
        gross_str = add_arg(args, "Gross", vals, 9)
        gross = Decimal(gross_str)
        account = add_arg(args, "Account Reference", vals, 10)
        reference = add_arg(args, "Reference", vals, 11)
        type_code = add_arg(args, "Type", vals, 12)
        typ = BillType.get_by_code(sess, type_code)
        breakdown_str = add_arg(args, "Breakdown", vals, 13)
        breakdown = _parse_breakdown(breakdown_str)

        kwh_str = add_arg(args, "kWh", vals, 14)
        kwh = Decimal(kwh_str)

        bill = batch.insert_bill(
            sess,
            account,
            reference,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net,
            vat,
            gross,
            typ,
            breakdown,
            supply,
        )

        for i in range(15, len(vals), 11):
            msn = add_arg(args, "Meter Serial Number", vals, i)
            mpan_str = add_arg(args, "MPAN", vals, i + 1)
            coefficient_str = add_arg(args, "Coefficient", vals, i + 2)
            coefficient = Decimal(coefficient_str)
            units = add_arg(args, "Units", vals, i + 3)
            tpr_code = add_arg(args, "TPR", vals, i + 4)
            if len(tpr_code) > 0:
                tpr = Tpr.get_by_code(sess, tpr_code)
            else:
                tpr = None

            prev_date_str = add_arg(args, "Previous Date", vals, i + 5)
            prev_date = parse_hh_start(prev_date_str)
            prev_value_str = add_arg(args, "Previous Value", vals, i + 6)
            prev_value = Decimal(prev_value_str)

            prev_type_str = add_arg(args, "Previous Type", vals, i + 7)
            prev_type = ReadType.get_by_code(sess, prev_type_str)

            pres_date_str = add_arg(args, "Present Date", vals, i + 8)
            pres_date = parse_hh_start(pres_date_str)
            pres_value_str = add_arg(args, "Present Value", vals, i + 9)
            pres_value = Decimal(pres_value_str)

            pres_type_str = add_arg(args, "Present Type", vals, i + 10)
            pres_type = ReadType.get_by_code(sess, pres_type_str)
            bill.insert_read(
                sess,
                tpr,
                coefficient,
                units,
                msn,
                mpan_str,
                prev_date,
                prev_value,
                prev_type,
                pres_date,
                pres_value,
                pres_type,
            )

    elif action == "update":
        bill_id_str = add_arg(args, "Bill Id", vals, 0)
        bill_id = int(bill_id_str)
        bill = Bill.get_by_id(bill_id)

        account = add_arg(args, "Account Reference", vals, 1)
        if account == NO_CHANGE:
            account = bill.getAccount()

        reference = add_arg(args, "Reference", vals, 2)
        if reference == NO_CHANGE:
            reference = bill.getReference()

        issue_date_str = add_arg(args, "Issue Date", vals, 3)
        issue_date = None

        if issue_date_str == NO_CHANGE:
            issue_date = bill.issue_date
        else:
            issue_date = parse_hh_start(issue_date_str)

        start_date_str = add_arg(args, "Start Date", vals, 4)
        if start_date_str == NO_CHANGE:
            start_date = bill.start_date
        else:
            start_date = parse_hh_start(start_date_str)

        finish_date_str = add_arg(args, "Finish Date", vals, 5)
        if finish_date_str == NO_CHANGE:
            finish_date = bill.finish_date
        else:
            finish_date = parse_hh_start(finish_date_str)

        kwh_str = add_arg(args, "kWh", vals, 6)
        kwh = bill.kwh if kwh_str == NO_CHANGE else Decimal(kwh_str)

        net_str = add_arg(args, "Net", vals, 7)
        net = bill.net if net_str == NO_CHANGE else Decimal(net_str)

        vat_str = add_arg(args, "Vat", vals, 8)
        vat = bill.vat if vat_str == NO_CHANGE else Decimal(vat_str)

        gross_str = add_arg(args, "Gross", vals, 9)
        gross = bill.gross if gross_str == NO_CHANGE else Decimal(gross_str)

        bill_type_code = add_arg(args, "Bill Type", vals, 10)
        if bill_type_code == NO_CHANGE:
            bill_type = bill.bill_type
        else:
            bill_type = BillType.get_by_code(sess, bill_type_code)

        breakdown = add_arg(args, "Breakdown", vals, 11)
        if breakdown == NO_CHANGE:
            breakdown = bill.breakdown

        bill.update(
            account,
            reference,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net,
            vat,
            gross,
            bill_type,
            breakdown,
        )


def general_import_g_bill(sess, action, vals, args):
    if action == "insert":
        contract_name = add_arg(args, "Supplier Contract Name", vals, 0)

        g_contract = GContract.get_supplier_by_name(sess, contract_name)

        batch_reference = add_arg(args, "Batch Reference", vals, 1)

        g_batch = g_contract.get_g_batch_by_reference(sess, batch_reference)

        mprn = add_arg(args, "MPRN", vals, 2)
        g_supply = GSupply.get_by_mprn(sess, mprn)

        issue_date_str = add_arg(args, "Issue Date", vals, 3)
        issue_date = parse_hh_start(issue_date_str)
        start_date_str = add_arg(args, "Start Date", vals, 4)
        start_date = parse_hh_start(start_date_str)
        finish_date_str = add_arg(args, "Finish Date", vals, 5)
        finish_date = parse_hh_start(finish_date_str)
        net_gbp_str = add_arg(args, "Net GBP", vals, 6)
        net_gbp = Decimal(net_gbp_str)
        vat_gbp_str = add_arg(args, "Vat GBP", vals, 7)
        vat_gbp = Decimal(vat_gbp_str)
        gross_gbp_str = add_arg(args, "Gross GBP", vals, 8)
        gross_gbp = Decimal(gross_gbp_str)
        account = add_arg(args, "Account Reference", vals, 9)
        reference = add_arg(args, "Reference", vals, 10)
        bill_type_code = add_arg(args, "Type", vals, 11)
        bill_type = BillType.get_by_code(sess, bill_type_code)
        breakdown_str = add_arg(args, "Breakdown", vals, 12)
        breakdown = _parse_breakdown(breakdown_str)

        kwh_str = add_arg(args, "kWh", vals, 13)
        kwh = Decimal(kwh_str)

        g_bill = g_batch.insert_g_bill(
            sess,
            g_supply,
            bill_type,
            reference,
            account,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net_gbp,
            vat_gbp,
            gross_gbp,
            "",
            breakdown,
        )

        for i in range(14, len(vals), 10):
            msn = add_arg(args, "Meter Serial Number", vals, i)
            g_unit_code = add_arg(args, "Unit", vals, i + 1)
            g_unit = GUnit.get_by_code(sess, g_unit_code)
            correction_factor_str = add_arg(args, "Correction Factor", vals, i + 2)
            correction_factor = Decimal(correction_factor_str)
            calorific_value_str = add_arg(args, "Calorific Value", vals, i + 3)
            calorific_value = Decimal(calorific_value_str)

            prev_date_str = add_arg(args, "Previous Date", vals, i + 4)
            prev_date = parse_hh_start(prev_date_str)
            prev_value_str = add_arg(args, "Previous Value", vals, i + 5)
            prev_value = Decimal(prev_value_str)

            prev_type_str = add_arg(args, "Previous Type", vals, i + 6)
            prev_type = GReadType.get_by_code(sess, prev_type_str)

            pres_date_str = add_arg(args, "Present Date", vals, i + 7)
            pres_date = parse_hh_start(pres_date_str)
            pres_value_str = add_arg(args, "Present Value", vals, i + 8)
            pres_value = Decimal(pres_value_str)

            pres_type_str = add_arg(args, "Present Type", vals, i + 9)
            pres_type = GReadType.get_by_code(sess, pres_type_str)

            g_bill.insert_g_read(
                sess,
                msn,
                g_unit,
                correction_factor,
                calorific_value,
                prev_value,
                prev_date,
                prev_type,
                pres_value,
                pres_date,
                pres_type,
            )


def general_import_register_read(sess, action, vals, args):
    if action == "insert":
        pass
    elif action == "update":
        read_id_str = add_arg(args, "Chellow Id", vals, 0)
        read = RegisterRead.get_by_id(int(read_id_str))

        tpr_code = add_arg(args, "TPR", vals, 1)
        if tpr_code == NO_CHANGE:
            tpr = read.tpr
        else:
            tpr = Tpr.get_by_code(sess, tpr_code)

        coefficient_str = add_arg(args, "Coefficient", vals, 2)
        if coefficient_str == NO_CHANGE:
            coefficient = read.coefficient
        else:
            coefficient = Decimal(coefficient_str)

        units = add_arg(args, "Units", vals, 3)

        msn = add_arg(args, "Meter Serial Number", vals, 4)
        if msn == NO_CHANGE:
            msn = read.msn

        mpan_str = add_arg(args, "MPAN", vals, 5)
        if mpan_str == NO_CHANGE:
            mpan_str = read.mpan_str

        prev_date_str = add_arg(args, "Previous Date", vals, 6)
        if prev_date_str == NO_CHANGE:
            prev_date = read.prev_date
        else:
            prev_date = parse_hh_start(prev_date_str)

        prev_value_str = add_arg(args, "Previous Value", vals, 7)
        if prev_value_str == NO_CHANGE:
            prev_value = read.prev_value
        else:
            prev_value = parse_hh_start(prev_value_str)

        prev_type_code = add_arg(args, "Previous Type", vals, 8)
        if prev_type_code == NO_CHANGE:
            prev_type = read.prev_type
        else:
            prev_type = ReadType.get_by_code(sess, prev_type_code)

        pres_date_str = add_arg(args, "Present Date", vals, 9)
        if pres_date_str == NO_CHANGE:
            pres_date = read.pres_date
        else:
            pres_date = parse_hh_start(pres_date_str)

        pres_value_str = add_arg(args, "Present Value", vals, 10)
        if pres_value_str == NO_CHANGE:
            pres_value = read.pres_value
        else:
            pres_value = parse_hh_start(pres_value_str)

        pres_type_code = add_arg(args, "Present Type", vals, 11)
        if pres_type_code == NO_CHANGE:
            pres_type = read.pres_type
        else:
            pres_type = ReadType.get_by_code(sess, pres_type_code)

        read.update(
            tpr,
            coefficient,
            units,
            msn,
            mpan_str,
            prev_date,
            prev_value,
            prev_type,
            pres_date,
            pres_value,
            pres_type,
        )


def general_import_supply(sess, action, vals, args):
    if action == "insert":
        site_code = add_arg(args, "Site Code", vals, 0)
        site = Site.get_by_code(sess, site_code)
        source_code = add_arg(args, "Source Code", vals, 1)
        source = Source.get_by_code(sess, source_code)
        gen_type_code = add_arg(args, "Generator Type", vals, 2)
        gen_type = None
        if source.code == "gen" or source.code == "gen-net":
            gen_type = GeneratorType.get_by_code(sess, gen_type_code)

        supply_name = add_arg(args, "Supply Name", vals, 3)
        gsp_group_code = add_arg(args, "Gsp Group", vals, 4)
        gsp_group = GspGroup.get_by_code(sess, gsp_group_code)
        start_date_str = add_arg(args, "Start Date", vals, 5)
        start_date = parse_hh_start(start_date_str)
        finish_date_str = add_arg(args, "Finish Date", vals, 6)
        finish_date = parse_hh_start(finish_date_str)
        mop_contract_name = add_arg(args, "MOP Contract", vals, 7)
        if len(mop_contract_name) > 0:
            mop_contract = Contract.get_mop_by_name(sess, mop_contract_name)
        else:
            mop_contract = None

        mop_account = add_arg(args, "MOP Account", vals, 8)
        dc_contract_name = add_arg(args, "DC Contract", vals, 9)
        if len(dc_contract_name) > 0:
            dc_contract = Contract.get_dc_by_name(sess, dc_contract_name)
        else:
            dc_contract = None

        dc_account = add_arg(args, "DC Account", vals, 10)
        msn = add_arg(args, "Meter Serial Number", vals, 11)
        dno_code = add_arg(args, "DNO Code", vals, 12)
        dno = Party.get_dno_by_code(sess, dno_code, start_date)
        pc_code = add_arg(args, "Profile Class", vals, 13)
        pc = Pc.get_by_code(sess, parse_pc_code(pc_code))
        mtc_code = add_arg(args, "Meter Timeswitch Class", vals, 14)
        cop_code = add_arg(args, "CoP", vals, 15)
        cop = Cop.get_by_code(sess, cop_code)
        comm_code = add_arg(args, "Comms Type", vals, 16)
        comm = Comm.get_by_code(sess, comm_code)
        ssc_code_str = add_arg(args, "Standard Settlement Configuration", vals, 17)
        if len(ssc_code_str) > 0:
            ssc = Ssc.get_by_code(sess, ssc_code_str, start_date)
            ssc_code = ssc.code
        else:
            ssc_code = None
        energisation_status_code = add_arg(args, "Energisation Status", vals, 18)
        energisation_status = EnergisationStatus.get_by_code(
            sess, energisation_status_code
        )
        dtc_meter_type_code = add_arg(args, "DTC Meter Type", vals, 19)
        dtc_meter_type = DtcMeterType.get_by_code(sess, dtc_meter_type_code)
        imp_mpan_core = add_arg(args, "Import MPAN Core", vals, 20)
        if len(imp_mpan_core) == 0:
            imp_mpan_core = None
        else:
            imp_mpan_core = parse_mpan_core(imp_mpan_core)

        if imp_mpan_core is None:
            imp_llfc_code = None
            imp_supplier_contract = None
            imp_supplier_account = None
            imp_sc = None
        else:
            imp_llfc_code = add_arg(args, "Import LLFC", vals, 21)
            imp_sc_str = add_arg(args, "Import Agreed Supply Capacity", vals, 22)
            try:
                imp_sc = int(imp_sc_str)
            except ValueError as e:
                raise BadRequest(f"The import supply capacity must be an integer. {e}")

            imp_supplier_contract_name = add_arg(
                args, "Import Supplier Contract", vals, 23
            )
            imp_supplier_account = add_arg(args, "Import Supplier Account", vals, 24)
            imp_supplier_contract = Contract.get_supplier_by_name(
                sess, imp_supplier_contract_name
            )

        exp_supplier_contract = exp_sc = exp_llfc_code = exp_mpan_core = None
        exp_supplier_account = None
        if len(vals) > 25:
            exp_mpan_core = add_arg(args, "Export MPAN Core", vals, 25)
            if len(exp_mpan_core) == 0:
                exp_mpan_core = None
            else:
                exp_mpan_core = parse_mpan_core(exp_mpan_core)

            if exp_mpan_core is not None:
                exp_llfc_code = add_arg(args, "Export LLFC", vals, 26)
                exp_sc_str = add_arg(args, "Export Agreed Supply Capacity", vals, 27)
                try:
                    exp_sc = int(exp_sc_str)
                except ValueError as e:
                    raise BadRequest(
                        f"The export agreed supply capacity must be an integer. {e}"
                    )

                exp_supplier_contract_name = add_arg(
                    args, "Export Supplier Contract", vals, 28
                )
                exp_supplier_contract = Contract.get_supplier_by_name(
                    sess, exp_supplier_contract_name
                )
                exp_supplier_account = add_arg(
                    args, "Export Supplier Account", vals, 29
                )

        supply = site.insert_e_supply(
            sess,
            source,
            gen_type,
            supply_name,
            start_date,
            finish_date,
            gsp_group,
            mop_contract,
            mop_account,
            dc_contract,
            dc_account,
            msn,
            dno,
            pc,
            mtc_code,
            cop,
            comm,
            ssc_code,
            energisation_status,
            dtc_meter_type,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            imp_supplier_account,
            imp_sc,
            exp_mpan_core,
            exp_llfc_code,
            exp_supplier_contract,
            exp_supplier_account,
            exp_sc,
        )
        sess.flush()

    elif action == "update":
        mpan_core = add_arg(args, "MPAN Core", vals, 0)
        source_code = add_arg(args, "Source Code", vals, 1)
        gen_type_code = add_arg(args, "Generator Type", vals, 2)
        gsp_group_code = add_arg(args, "GSP Group", vals, 3)
        supply_name = add_arg(args, "Supply Name", vals, 4)
        supply = Supply.get_by_mpan_core(sess, mpan_core)

        supply_name = supply.name if supply_name == NO_CHANGE else supply_name
        if source_code == NO_CHANGE:
            source = Source.get_by_code(sess, source_code)
        else:
            source = supply.source

        if gen_type_code == NO_CHANGE:
            gen_type = supply.generator_type
        else:
            gen_type = GeneratorType.get_by_code(sess, gen_type_code)

        if gsp_group_code == NO_CHANGE:
            gsp_group = supply.gsp_group
        else:
            gsp_group = GspGroup.get_by_code(sess, gsp_group_code)

        supply.update(supply_name, source, gen_type, gsp_group)

    elif action == "delete":
        mpan_core = add_arg(args, "MPAN Core", vals, 0)
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        supply.delete()


def general_import_llfc(sess, action, vals, args):
    if action == "insert":
        dno_code = add_arg(args, "dno", vals, 0)
        llfc_code = add_arg(args, "llfc", vals, 1)
        llfc_description = add_arg(args, "llfc_description", vals, 2)
        vl_code = add_arg(args, "voltage_level", vals, 3)
        vl = VoltageLevel.get_by_code(sess, vl_code.upper())
        is_substation_str = add_arg(args, "is_substation", vals, 4)
        is_substation = parse_bool(is_substation_str)
        is_import_str = add_arg(args, "is_import", vals, 5)
        is_import = parse_bool(is_import_str)
        valid_from_str = add_arg(args, "valid_from", vals, 6)
        valid_from = parse_hh_start(valid_from_str)
        valid_to_str = add_arg(args, "valid_to", vals, 7)
        valid_to = parse_hh_start(valid_to_str)

        dno = Party.get_dno_by_code(sess, dno_code, valid_from)
        existing_llfc = dno.find_llfc_by_code(sess, llfc_code, valid_from)

        if existing_llfc is None:
            llfc = Llfc(
                dno,
                llfc_code,
                llfc_description,
                vl,
                is_substation,
                is_import,
                valid_from,
                valid_to,
            )
            sess.add(llfc)
            sess.flush()
        else:
            raise BadRequest(
                "There's already a LLFC with this DNO and code for this " "period."
            )

    elif action == "update":
        dno_code = add_arg(args, "dno", vals, 0)
        llfc_code = add_arg(args, "llfc", vals, 1)
        valid_from_str = add_arg(args, "valid_from", vals, 2)
        valid_from = parse_hh_start(valid_from_str)

        dno = Party.get_dno_by_code(sess, dno_code, valid_from)
        llfc = (
            sess.query(Llfc)
            .filter(
                Llfc.dno == dno, Llfc.code == llfc_code, Llfc.valid_from == valid_from
            )
            .first()
        )
        if llfc is None:
            raise BadRequest(
                f"Can't find an LLFC for the DNO {dno_code} and 'valid from' "
                f"date {hh_format(valid_from)}."
            )

        llfc_description_str = add_arg(args, "llfc_description", vals, 3)
        if llfc_description_str == NO_CHANGE:
            llfc_description = llfc.description
        else:
            llfc_description = llfc_description_str

        vl_code_str = add_arg(args, "voltage_level", vals, 4)
        if vl_code_str == NO_CHANGE:
            vl = llfc.voltage_level
        else:
            vl = VoltageLevel.get_by_code(sess, vl_code_str.upper())

        is_substation_str = add_arg(args, "is_substation", vals, 5)
        if is_substation_str == NO_CHANGE:
            is_substation = llfc.is_substation
        else:
            is_substation = parse_bool(is_substation_str)

        is_import_str = add_arg(args, "is_import", vals, 6)
        if is_import_str == NO_CHANGE:
            is_import = llfc.is_import
        else:
            is_import = parse_bool(is_import_str)

        valid_to_str = add_arg(args, "valid_to", vals, 7)
        if valid_to_str == NO_CHANGE:
            valid_to = llfc.valid_to
        else:
            valid_to = parse_hh_start(valid_to_str)

        llfc.update(
            llfc_description, vl, is_substation, is_import, llfc.valid_from, valid_to
        )
        sess.flush()

    elif action == "delete":
        dno_code = add_arg(args, "dno_code", vals, 0)
        dno = Party.get_dno_by_code(sess, dno_code)
        llfc_code = add_arg(args, "llfc", vals, 1)
        date_str = add_arg(args, "date", vals, 2)
        date = parse_hh_start(date_str)

        llfc = dno.get_llfc_by_code(sess, llfc_code, date)
        sess.delete(llfc)
        sess.flush()
    else:
        raise BadRequest("Action not recognized.")


def general_import_site_era(sess, action, vals, args):
    site_code = add_arg(args, "site_code", vals, 0)
    site = Site.get_by_code(sess, site_code)
    mpan_core = add_arg(args, "mpan_core", vals, 1)
    start_date_str = add_arg(args, "generation_start_date", vals, 2)
    start_date = datetime.datetime(start_date_str)
    era = Era.get_by_core_date(mpan_core, start_date)
    if action == "insert":
        is_location_str = add_arg(args, "is_location", vals, 3)
        is_location = bool(is_location_str)
        era.attach_site(site, is_location)
        sess.flush()


def general_import_channel(sess, action, vals, args):
    mpan_core_raw = add_arg(args, "MPAN Core", vals, 0)
    mpan_core = parse_mpan_core(mpan_core_raw)
    supply = Supply.find_by_mpan_core(sess, mpan_core)
    dt_raw = add_arg(args, "Date", vals, 1)
    dt = parse_hh_start(dt_raw)
    era = supply.find_era_at(sess, dt)
    import_related_str = add_arg(args, "Import Related?", vals, 2)
    import_related = parse_bool(import_related_str)
    channel_type_raw = add_arg(args, "Channel Type", vals, 3)
    channel_type = parse_channel_type(channel_type_raw)

    if action == "insert":
        era.insert_channel(sess, import_related, channel_type)
    elif action == "delete":
        era.delete_channel(sess, import_related, channel_type)


def general_import_user(sess, action, vals, args):
    if action == "insert":
        email_address = add_arg(args, "email_address", vals, 0)
        password = add_arg(args, "password", vals, 1)
        digest = add_arg(args, "password_digest", vals, 2)
        user_role_code = add_arg(args, "user_role_code", vals, 3)
        user_role = UserRole.get_by_code(sess, user_role_code)
        participant_code = add_arg(args, "participant_code", vals, 4)
        party = None
        if len(participant_code.strip()) > 0:
            market_role_code = add_arg(args, "market_role_code", vals, 5)
        party = Party.get_by_participant_role(participant_code, market_role_code)
        if len(password) == 0:
            if len(digest) == 0:
                raise BadRequest("The password and digest fields can't both be blank.")
        elif len(digest) > 0:
            raise BadRequest("The password and digest fields can't both be filled.")
        else:
            digest = User.digest(password)

        User.insert(email_address, user_role, party, digest)
    elif action == "update":
        pass


def general_import_site(sess, action, vals, args):
    code = add_arg(args, "site_code", vals, 0)

    if action == "insert":
        name = add_arg(args, "site_name", vals, 1)
        Site.insert(sess, code, name)
    else:
        site = Site.get_by_code(sess, code)

        if action == "delete":
            site.delete()
        elif action == "update":
            new_code = add_arg(args, "new_site_code", vals, 1)
            if new_code == NO_CHANGE:
                new_code = site.code
            name = add_arg(args, "new_site_name", vals, 2)
            if name == NO_CHANGE:
                name = site.name
            site.update(new_code, name)


def general_import_batch(sess, action, vals, args):
    if action == "insert":
        role_name = add_arg(args, "Role Name", vals, 0).lower()
        contract_name = add_arg(args, "Contract Name", vals, 1)

        if role_name == "dc":
            contract = Contract.get_dc_by_name(sess, contract_name)
        elif role_name == "supplier":
            contract = Contract.get_supplier_by_name(sess, contract_name)
        elif role_name == "mop":
            contract = Contract.get_mop_by_name(sess, contract_name)
        else:
            raise BadRequest("The role name must be one of dc, supplier or mop.")

        reference = add_arg(args, "Reference", vals, 2)
        description = add_arg(args, "Description", vals, 3)
        contract.insert_batch(sess, reference, description)
    elif action == "update":
        role_name = add_arg(args, "Role Name", vals, 0).lower()
        contract_name = add_arg(args, "Contract Name", vals, 1)

        if role_name == "dc":
            contract = Contract.get_dc_by_name(sess, contract_name)
        elif role_name == "supplier":
            contract = Contract.get_supplier_by_name(sess, contract_name)
        elif role_name == "mop":
            contract = Contract.get_mop_by_name(sess, contract_name)
        else:
            raise BadRequest("The role name must be one of dc, supplier or mop.")

        old_reference = add_arg(args, "Old Reference", vals, 2)
        batch = contract.get_batch(sess, sess, old_reference)
        new_reference = add_arg(args, "New Reference", vals, 3)
        description = add_arg(args, "Description", vals, 4)
        batch.update(sess, new_reference, description)


def general_import_site_snag_ignore(sess, action, vals, args):
    if action == "insert":
        site_code = add_arg(args, "Site Code", vals, 0)
        site = Site.get_by_code(sess, site_code)
        description = add_arg(args, "Snag Description", vals, 1)
        start_date_str = add_arg(args, "Start Date", vals, 2)
        start_date = parse_hh_start(start_date_str)
        finish_date_str = add_arg(args, "Finish Date", vals, 3)
        finish_date = parse_hh_start(finish_date_str)

        for snag in sess.query(Snag).filter(
            Snag.site_id == site.id,
            Snag.description == description,
            Snag.is_ignored != false(),
            Snag.start_date <= finish_date,
            or_(Snag.finish_date == null(), Snag.finish_date >= start_date),
        ):
            snag.set_is_ignored(True)

    elif action == "update":
        raise BadRequest("The 'update' action isn't supported for site snags.")


def general_import_channel_snag_ignore(sess, action, vals, args):
    _channel_snag_update(sess, action, vals, args, True)


def general_import_channel_snag_unignore(sess, action, vals, args):
    _channel_snag_update(sess, action, vals, args, False)


def _channel_snag_update(sess, action, vals, args, ignore):
    if action == "insert":
        mpan_core_str = add_arg(args, "MPAN Core", vals, 0)
        mpan_core = parse_mpan_core(mpan_core_str)
        supply = Supply.get_by_mpan_core(sess, mpan_core)
        imp_related_str = add_arg(args, "Import Related?", vals, 1)
        imp_related = parse_bool(imp_related_str)
        channel_type_str = add_arg(args, "Channel Type", vals, 2)
        channel_type = parse_channel_type(channel_type_str)
        description = add_arg(args, "Snag Description", vals, 3)
        start_str = add_arg(args, "From", vals, 4)
        start_date = parse_hh_start(start_str)
        finish_str = add_arg(args, "To", vals, 5)
        finish_date = parse_hh_start(finish_str)

        for era in supply.find_eras(sess, start_date, finish_date):
            channel = (
                sess.query(Channel)
                .filter(
                    Channel.era == era,
                    Channel.imp_related == imp_related,
                    Channel.channel_type == channel_type,
                )
                .first()
            )
            if channel is not None:
                snag_query = sess.query(Snag).filter(
                    Snag.channel == channel,
                    Snag.is_ignored == (not ignore),
                    Snag.description == description,
                    or_(Snag.finish_date == null(), Snag.finish_date >= start_date),
                )

            if finish_date is not None:
                snag_query = snag_query.filter(Snag.start_date <= finish_date)

            for snag in snag_query:
                snag.set_is_ignored(ignore)

    elif action == "update":
        raise BadRequest("The action 'update' isn't supported for channel snags.")


PREFIX = "general_import_"

typ_funcs = {}
for k in tuple(globals().keys()):
    if k.startswith(PREFIX):
        typ_funcs[k[len(PREFIX) :]] = globals()[k]


def _process_line(sess, hh_data, line, args):

    action = add_arg(args, "action", line, 0).lower()
    if action not in ALLOWED_ACTIONS:
        raise BadRequest(f"The 'action' field must be one of {ALLOWED_ACTIONS}")
    typ = add_arg(args, "type", line, 1).lower()
    vals = line[2:]
    if typ == "hh_datum":
        if action == "insert":
            hh_data.append(
                {
                    "mpan_core": parse_mpan_core(add_arg(args, "MPAN Core", vals, 0)),
                    "start_date": parse_hh_start(add_arg(args, "Start Date", vals, 1)),
                    "channel_type": parse_channel_type(
                        add_arg(args, "Channel Type", vals, 2)
                    ),
                    "value": Decimal(add_arg(args, "Value", vals, 3)),
                    "status": add_arg(args, "Status", vals, 4),
                }
            )
    else:
        try:
            typ_func = typ_funcs[typ]
            typ_func(sess, action, vals, args)
        except KeyError:
            raise BadRequest(f"The type {typ} is not recognized.")


class GeneralImporter(threading.Thread):
    def __init__(self, f):
        threading.Thread.__init__(self)
        self.line_number = None
        self.f = f
        self.error_message = None
        self.args = []
        self.failed_args = []
        self.failed_lines = []

    def run(self):
        try:
            with Session() as sess:
                reader = csv.reader(self.f)
                hh_data = []
                for idx, line in enumerate(reader):
                    self.args = []
                    self.line_number = idx + 1

                    if len(line) == 0:
                        continue

                    if len(line) > 0 and line[0].startswith("#"):
                        continue

                    try:
                        with sess.begin_nested():
                            _process_line(sess, hh_data, line, self.args)

                    except BadRequest as e:
                        self.args.insert(0, ("Error", e.description))
                        self.failed_args.append(self.args)
                        self.failed_lines.append(line)

                HhDatum.insert(sess, hh_data)

                if len(self.failed_lines) == 0:
                    sess.commit()
                else:
                    sess.rollback()
        except BadRequest as e:
            self.error_message = e.description
        except BaseException:
            self.error_message = traceback.format_exc()


def start_process(f):
    with process_lock:
        global process_id
        proc_id = process_id
        process_id += 1

    process = GeneralImporter(f)
    processes[proc_id] = process
    process.start()
    return proc_id


def get_process_ids():
    with process_lock:
        return processes.keys()


def get_process(id):
    return processes[id]
