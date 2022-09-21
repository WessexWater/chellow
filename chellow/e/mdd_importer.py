import csv
from datetime import datetime as Datetime, timedelta as Timedelta
from io import StringIO

import requests

from sqlalchemy import null, or_, select
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Contract,
    GspGroup,
    Llfc,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfc,
    MtcLlfcSsc,
    MtcLlfcSscPc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Party,
    Pc,
    Ssc,
    VoltageLevel,
)
from chellow.utils import (
    ct_datetime,
    to_ct,
    to_utc,
)


def parse_date(date_str):
    if len(date_str) == 0:
        return None
    else:
        return to_utc(to_ct(Datetime.strptime(date_str, "%d/%m/%Y")))


def parse_to_date(date_str):
    if len(date_str) == 0:
        return None
    else:
        dt = to_ct(Datetime.strptime(date_str, "%d/%m/%Y"))
        dt += Timedelta(hours=23, minutes=30)
        return to_utc(dt)


def parse_bool(bool_str):
    return bool_str == "T"


VOLTAGE_MAP = {"24": {"602": {to_utc(ct_datetime(2010, 4, 1)): "LV"}}}


def _import_GSP_Group(sess, rows, ctx):
    for values in rows:
        code = values[0]
        description = values[1]

        group = GspGroup.find_by_code(sess, code)

        if group is None:
            GspGroup.insert(sess, code, description)

        else:
            group.description = description
            sess.flush()


def _import_Line_Loss_Factor_Class(sess, rows, ctx):
    VOLTAGE_LEVELS = {v.code: v for v in sess.execute(select(VoltageLevel)).scalars()}
    DNO_MAP = {
        dno.participant.code: dno
        for dno in sess.execute(
            select(Party)
            .join(MarketRole)
            .where(MarketRole.code == "R")
            .options(joinedload(Party.participant))
        ).scalars()
    }
    llfcs = {
        (v.dno.id, v.code, v.valid_from): v
        for v in sess.execute(select(Llfc)).scalars()
    }

    for values in rows:
        participant_code = values[0]
        # market_role_code = values[1]
        llfc_code = values[3].zfill(3)
        valid_from = parse_date(values[4])
        description = values[5]
        is_import = values[6] in ("A", "B")
        is_substation = any(
            p in description for p in ("_SS", " SS", " S/S", "(S/S)", "sub", "Sub")
        )

        valid_to = parse_to_date(values[7])

        try:
            dno = DNO_MAP[participant_code]
        except KeyError:
            raise BadRequest(
                f"There is no DNO with participant code {participant_code}"
            )

        try:
            voltage_level_code = VOLTAGE_MAP[dno.dno_code][llfc_code][valid_from]
        except KeyError:
            voltage_level_code = "LV"
            description_upper = description.upper()
            for vl_code in VOLTAGE_LEVELS.keys():
                if vl_code in description_upper:
                    voltage_level_code = vl_code
                    break

        voltage_level = VOLTAGE_LEVELS[voltage_level_code]

        try:
            llfc = llfcs[(dno.id, llfc_code, valid_from)]
            llfc.description = description
            llfc.voltage_level = voltage_level
            llfc.is_substation = is_substation
            llfc.is_import = is_import
            llfc.valid_to = valid_to
            sess.flush()
        except KeyError:
            dno.insert_llfc(
                sess,
                llfc_code,
                description,
                voltage_level,
                is_substation,
                is_import,
                valid_from,
                valid_to,
            )


def _import_Market_Participant(sess, rows, ctx):
    for values in rows:
        participant_code = values[0]
        participant_name = values[1]

        participant = Participant.find_by_code(sess, participant_code)

        if participant is None:
            Participant.insert(sess, participant_code, participant_name)

        else:
            participant.update(participant_name)
            sess.flush()


def _import_Market_Role(sess, rows, ctx):
    for values in rows:
        role_code = values[0]
        role_description = values[1]

        role = MarketRole.find_by_code(sess, role_code)

        if role is None:
            MarketRole.insert(sess, role_code, role_description)

        else:
            role.description = role_description
            sess.flush()


def _import_Market_Participant_Role(sess, rows, ctx):
    for values in rows:
        participant_code = values[0]
        participant = Participant.get_by_code(sess, participant_code)
        market_role_code = values[1]
        market_role = MarketRole.get_by_code(sess, market_role_code)
        valid_from = parse_date(values[2])
        party = Party.find_by_participant_role(
            sess, participant, market_role, valid_from
        )
        valid_to = parse_to_date(values[3])
        name = values[4]
        dno_code_str = values[14]
        dno_code = None if len(dno_code_str) == 0 else dno_code_str
        if dno_code == "99":
            continue

        if party is None:
            participant.insert_party(
                sess,
                market_role,
                name,
                valid_from,
                valid_to,
                dno_code,
            )

            if dno_code is not None:
                contract = Contract.find_dno_by_name(sess, dno_code)
                if contract is None:
                    Contract.insert_dno(
                        sess, dno_code, participant, "", {}, valid_from, None, {}
                    )

        else:
            party.name = name
            party.valid_to = valid_to
            party.dno_code = dno_code
            sess.flush()


def _import_Meter_Timeswitch_Class(sess, rows, ctx):
    ctx_mtcs = ctx["mtcs"] = {}
    meter_types = dict((m.code, m) for m in sess.execute(select(MeterType)).scalars())
    meter_payment_types = dict(
        (m.code, m) for m in sess.execute(select(MeterPaymentType)).scalars()
    )

    for values in rows:
        code = values[0].zfill(3)  # Meter Timeswitch Class ID
        valid_from = parse_date(values[1])  # Effective From Settlement Date (MTC)
        valid_to = parse_to_date(values[2])  # Effective To Settlement Date (MTC)
        description = values[3]  # Meter Timeswitch Class Description
        is_common = parse_bool(values[4])  # MTC Common Code Indicator
        has_related_metering_str = values[5]  # MTC Related Metering System Indicator
        has_related_metering = parse_bool(has_related_metering_str)

        ctx_mtc = {
            "code": code,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "description": description,
            "is_common": is_common,
            "has_related_metering": has_related_metering,
        }

        if is_common:
            meter_type_code = values[6]  # Mtc Meter Type ID
            meter_type = meter_types[meter_type_code]
            meter_payment_type_code = values[7]  # MTC Payment Type ID
            meter_payment_type = meter_payment_types[meter_payment_type_code]
            has_comms_str = values[8]  # MTC Communication Indicator
            has_comms = parse_bool(has_comms_str)
            is_hh_str = values[9]  # MTC Type Indicator
            is_hh = parse_bool(is_hh_str)
            tpr_count_str = values[10]  # TPR Count
            tpr_count = None if tpr_count_str == "" else int(tpr_count_str)

            ctx_mtc["meter_type"] = meter_type
            ctx_mtc["meter_payment_type"] = meter_payment_type
            ctx_mtc["has_comms"] = has_comms
            ctx_mtc["is_hh"] = is_hh
            ctx_mtc["tpr_count"] = tpr_count

        ctx_mtcs[(code, valid_from)] = ctx_mtc

        mtc = Mtc.find_by_code(sess, code, valid_from)
        if mtc is None:
            Mtc.insert(
                sess,
                code,
                is_common,
                has_related_metering,
                valid_from,
                valid_to,
            )

        else:
            mtc.description = description
            mtc.has_related_metering = has_related_metering
            mtc.valid_to = valid_to
            sess.flush()


def _import_MTC_in_PES_Area(sess, rows, ctx):
    mtc_participants = {
        (m.participant.id, m.mtc.id, m.valid_from): m
        for m in sess.execute(
            select(MtcParticipant).options(
                joinedload(MtcParticipant.meter_type),
                joinedload(MtcParticipant.meter_payment_type),
            )
        ).scalars()
    }
    mtcs = {(m.code, m.valid_from): m for m in sess.execute(select(Mtc)).scalars()}
    participants = {p.code: p for p in sess.execute(select(Participant)).scalars()}
    meter_types = {m.code: m for m in sess.execute(select(MeterType)).scalars()}
    meter_payment_types = {
        m.code: m for m in sess.execute(select(MeterPaymentType)).scalars()
    }

    for values in rows:
        mtc_code_str = values[0]  # Meter Timeswitch Class ID
        mtc_code = mtc_code_str.zfill(3)
        mtc_from_str = values[1]  # Effective From Settlement Date (MTC)
        mtc_from = parse_date(mtc_from_str)
        mtc = mtcs[(mtc_code, mtc_from)]
        participant_code = values[2]  # Market Participant ID
        participant = participants[participant_code]
        valid_from_str = values[3]  # Effective From Settlement Date (MTCPA)
        valid_from = parse_date(valid_from_str)
        mtc_participant = mtc_participants.get((participant.id, mtc.id, valid_from))
        valid_to_str = values[4]  # Effective To Settlement Date (MTCPA)
        valid_to = parse_to_date(valid_to_str)

        if mtc.is_common:
            ctx_mtc = ctx["mtcs"][(mtc_code, mtc_from)]
            description = ctx_mtc["description"]
            meter_type = ctx_mtc["meter_type"]
            meter_payment_type = ctx_mtc["meter_payment_type"]
            has_comms = ctx_mtc["has_comms"]
            is_hh = ctx_mtc["is_hh"]
            tpr_count = ctx_mtc["tpr_count"]

        else:
            description = values[5]  # Meter Timeswitch Class Description
            meter_type_code = values[6]  # Mtc Meter Type ID
            meter_type = meter_types[meter_type_code]
            meter_payment_type_code = values[7]  # MTC Payment Type ID
            meter_payment_type = meter_payment_types[meter_payment_type_code]
            has_comms = values[8] == "Y"  # MTC Comm. Indicator
            is_hh = values[9] == "H"  # MTC Type Indicator
            tpr_count_str = values[10]  # TPR Count
            tpr_count = 0 if tpr_count_str == "" else int(tpr_count_str)

        if mtc_participant is None:

            MtcParticipant.insert(
                sess,
                mtc,
                participant,
                description,
                has_comms,
                is_hh,
                meter_type,
                meter_payment_type,
                tpr_count,
                valid_from,
                valid_to,
            )

        else:
            mtc.description = description
            mtc.has_comms = has_comms
            mtc.is_hh = is_hh
            mtc.meter_type = meter_type
            mtc.meter_payment_type = meter_payment_type
            mtc.tpr_count = tpr_count
            mtc.valid_to = valid_to
            sess.flush()


def _import_MTC_Meter_Type(sess, rows, ctx):
    meter_types = dict(
        ((v.code, v.valid_from), v) for v in sess.execute(select(MeterType)).scalars()
    )
    for values in rows:
        code = values[0]
        description = values[1]
        valid_from = parse_date(values[2])
        valid_to = parse_to_date(values[3])
        meter_type = meter_types.get((code, valid_from))

        if meter_type is None:
            MeterType.insert(sess, code, description, valid_from, valid_to)

        else:
            meter_type.description = description
            meter_type.valid_to = valid_to
            sess.flush()


def _import_MTC_Payment_Type(sess, rows, ctx):
    meter_payment_types = dict(
        ((v.code, v.valid_from), v)
        for v in sess.execute(select(MeterPaymentType)).scalars()
    )
    for values in rows:
        code = values[0]
        description = values[1]
        valid_from = parse_date(values[2])
        valid_to = parse_to_date(values[3])
        meter_payment_type = meter_payment_types.get((code, valid_from))

        if meter_payment_type is None:
            MeterPaymentType.insert(sess, code, description, valid_from, valid_to)

        else:
            meter_payment_type.description = description
            meter_payment_type.valid_to = valid_to
            sess.flush()


def _import_Profile_Class(sess, rows, ctx):
    for values in rows:
        code_str = values[0]
        code = code_str.zfill(2)
        valid_from = parse_date(values[1])
        name = values[2]
        valid_to = parse_to_date(values[4])

        pc = Pc.find_by_code(sess, code)

        if pc is None:
            Pc.insert(sess, code, name, valid_from, valid_to)

        else:
            pc.name = name
            pc.valid_to = valid_to
            sess.flush()


def _import_Standard_Settlement_Configuration(sess, rows, ctx):
    sscs = dict(
        ((v.code, v.valid_from), v) for v in sess.execute(select(Ssc)).scalars()
    )
    for values in rows:
        code = values[0]
        valid_from = parse_date(values[1])
        valid_to = parse_to_date(values[2])
        description = values[3]
        is_import = values[4] == "I"
        ssc = sscs.get((code, valid_from))

        if ssc is None:
            Ssc.insert(sess, code, description, is_import, valid_from, valid_to)

        else:
            ssc.description = description
            ssc.is_import = is_import
            ssc.valid_to = valid_to
            sess.flush()


def _import_Valid_MTC_LLFC_Combination(sess, rows, ctx):
    mtcs = {(v.code, v.valid_from): v for v in sess.execute(select(Mtc)).scalars()}
    participants = {v.code: v for v in sess.execute(select(Participant)).scalars()}
    mtc_participants = {
        (v.mtc.id, v.participant.id, v.valid_from): v
        for v in sess.execute(select(MtcParticipant)).scalars()
    }
    mtc_llfcs = {
        (v.mtc_participant.id, v.llfc.id, v.valid_from): v
        for v in sess.execute(select(MtcLlfc)).scalars()
    }
    dnos = {}
    llfcs = {}

    for values in rows:
        mtc_code_str = values[0]  # Meter Timeswitch Class ID
        mtc_code = mtc_code_str.zfill(3)
        mtc_from_str = values[1]  # Effective From Settlement Date (MTC)
        mtc_from = parse_date(mtc_from_str)
        mtc = mtcs[(mtc_code, mtc_from)]
        participant_code = values[2]  # Market Participant ID
        participant = participants[participant_code]

        mtc_participant_from_str = values[3]  # Effective From Settlement Date (MTCPA)
        mtc_participant_from = parse_date(mtc_participant_from_str)
        mtc_participant = mtc_participants[
            (mtc.id, participant.id, mtc_participant_from)
        ]
        llfc_code = values[4]  # Line Loss Factor Class ID
        valid_from_str = values[5]  # Effective From Settlement Date (VMTCLC)
        valid_from = parse_date(valid_from_str)
        valid_to_str = values[6]  # Effective To Settlement Date (VMTCLC)
        valid_to = parse_to_date(valid_to_str)

        try:
            dno = dnos[(participant.id, valid_from)]
        except KeyError:
            dno = dnos[(participant.id, valid_from)] = sess.execute(
                select(Party)
                .join(Participant)
                .join(MarketRole)
                .where(
                    Participant.code == participant_code,
                    MarketRole.code == "R",
                    Party.valid_from <= valid_from,
                    or_(Party.valid_to == null(), Party.valid_to >= valid_from),
                )
            ).scalar_one()
        try:
            llfc = llfcs[(dno.id, llfc_code, valid_from)]
        except KeyError:
            llfc = llfcs[(dno.id, llfc_code, valid_from)] = dno.get_llfc_by_code(
                sess, llfc_code, valid_from
            )

        try:
            mtc_llfc = mtc_llfcs[(mtc_participant.id, llfc.id, valid_from)]
            mtc_llfc.valid_to = valid_to
            sess.flush()
        except KeyError:
            MtcLlfc.insert(
                sess,
                mtc_participant,
                llfc,
                valid_from,
                valid_to,
            )


def _import_Valid_MTC_SSC_Combination(sess, rows, ctx):
    mtcs = dict(
        ((v.code, v.valid_from), v) for v in sess.execute(select(Mtc)).scalars()
    )
    participants = dict(
        (v.code, v) for v in sess.execute(select(Participant)).scalars()
    )
    mtc_participants = dict(
        ((v.mtc.id, v.participant.id, v.valid_from), v)
        for v in sess.execute(select(MtcParticipant)).scalars()
    )
    sscs = dict(
        ((v.code, v.valid_from), v) for v in sess.execute(select(Ssc)).scalars()
    )
    mtc_sscs = dict(
        ((v.mtc_participant.id, v.ssc.id, v.valid_from), v)
        for v in sess.execute(select(MtcSsc)).scalars()
    )

    for values in rows:
        mtc_code = values[0].zfill(3)  # Meter Timeswitch Class ID
        mtc_from_str = values[1]  # Effective From Settlement Date (MTC)
        mtc_from = parse_date(mtc_from_str)
        mtc = mtcs[(mtc_code, mtc_from)]
        participant_code = values[2]  # Market Participant ID
        participant = participants[participant_code]
        mtc_participant_from_str = values[3]  # Effective From Settlement Date (MTCPA)
        mtc_participant_from = parse_date(mtc_participant_from_str)
        mtc_participant = mtc_participants[
            (mtc.id, participant.id, mtc_participant_from)
        ]
        ssc_code = values[4]  # Standard Settlement Configuration ID
        valid_from_str = values[5]  # Effective From Settlement Date (VMTCSC)
        valid_from = parse_date(valid_from_str)
        valid_to_str = values[6]  # Effective To Settlement Date (VMTCSC)
        valid_to = parse_to_date(valid_to_str)

        try:
            ssc = sscs[(ssc_code, valid_from)]
        except KeyError:
            ssc = sscs[(ssc_code, valid_from)] = Ssc.get_by_code(
                sess, ssc_code, valid_from
            )

        try:
            mtc_ssc = mtc_sscs[(mtc_participant.id, ssc.id, valid_from)]
            mtc_ssc.valid_to = valid_to
            sess.flush()
        except KeyError:
            MtcSsc.insert(
                sess,
                mtc_participant,
                ssc,
                valid_from,
                valid_to,
            )


def _import_Valid_MTC_LLFC_SSC_Combination(sess, rows, ctx):
    mtcs = {(v.code, v.valid_from): v for v in sess.execute(select(Mtc)).scalars()}
    participants = {v.code: v for v in sess.execute(select(Participant)).scalars()}
    mtc_participants = {
        (v.mtc.id, v.participant.id, v.valid_from): v
        for v in sess.execute(select(MtcParticipant)).scalars()
    }
    sscs = {(v.code, v.valid_from): v for v in sess.execute(select(Ssc)).scalars()}
    mtc_sscs = {
        (v.mtc_participant.id, v.ssc.id, v.valid_from): v
        for v in sess.execute(select(MtcSsc)).scalars()
    }
    dnos = {}
    llfcs = {}
    mtc_llfc_sscs = {
        (v.mtc_ssc.id, v.llfc.id, v.valid_from): v
        for v in sess.execute(select(MtcLlfcSsc)).scalars()
    }

    for values in rows:
        mtc_code = values[0].zfill(3)  # Meter Timeswitch Class ID
        mtc_from_str = values[1]  # Effective From Settlement Date (MTC)
        mtc_from = parse_date(mtc_from_str)
        mtc = mtcs[(mtc_code, mtc_from)]
        participant_code = values[2]  # Market Participant ID
        participant = participants[participant_code]
        mtc_participant_from_str = values[3]  # Effective From Settlement Date (MTCPA)
        mtc_participant_from = parse_date(mtc_participant_from_str)
        mtc_participant = mtc_participants[
            (mtc.id, participant.id, mtc_participant_from)
        ]
        ssc_code = values[4]  # Standard Settlement Configuration ID
        mtc_ssc_from_str = values[5]  # Effective From Settlement date (VMTCSC)
        mtc_ssc_from = parse_date(mtc_ssc_from_str)
        try:
            ssc = sscs[(ssc_code, mtc_ssc_from)]
        except KeyError:
            ssc = sscs[(ssc_code, mtc_ssc_from)] = Ssc.get_by_code(
                sess, ssc_code, mtc_ssc_from
            )
        mtc_ssc = mtc_sscs[(mtc_participant.id, ssc.id, mtc_ssc_from)]
        llfc_code = values[6]  # Line Loss Factor Class ID
        valid_from_str = values[7]  # Effective From Settlement Date (VMTCLSC)
        valid_from = parse_date(valid_from_str)
        valid_to_str = values[8]  # Effective To Settlement Date (VMTCLSC)
        valid_to = parse_to_date(valid_to_str)

        try:
            dno = dnos[(participant.id, valid_from)]
        except KeyError:
            dno = dnos[(participant.id, valid_from)] = sess.execute(
                select(Party)
                .join(Participant)
                .join(MarketRole)
                .where(
                    Participant.code == participant_code,
                    MarketRole.code == "R",
                    Party.valid_from <= valid_from,
                    or_(Party.valid_to == null(), Party.valid_to >= valid_from),
                )
            ).scalar_one()

        try:
            llfc = llfcs[(dno.id, llfc_code, valid_from)]
        except KeyError:
            llfc = llfcs[(dno.id, llfc_code, valid_from)] = dno.get_llfc_by_code(
                sess, llfc_code, valid_from
            )

        try:
            mtc_llfc_ssc = mtc_llfc_sscs[mtc_ssc.id, llfc.id, valid_from]
            mtc_llfc_ssc.valid_to = valid_to
            sess.flush()
        except KeyError:
            MtcLlfcSsc.insert(
                sess,
                mtc_ssc,
                llfc,
                valid_from,
                valid_to,
            )


def _import_Valid_MTC_LLFC_SSC_PC_Combination(sess, rows, ctx):
    mtcs = {(v.code, v.valid_from): v for v in sess.execute(select(Mtc)).scalars()}
    participants = {v.code: v for v in sess.execute(select(Participant)).scalars()}
    mtc_participants = {
        (v.mtc.id, v.participant.id, v.valid_from): v
        for v in sess.execute(select(MtcParticipant)).scalars()
    }
    mtc_sscs = {
        (v.mtc_participant.id, v.ssc.id, v.valid_from): v
        for v in sess.execute(select(MtcSsc)).scalars()
    }
    mtc_llfc_sscs = {
        (v.mtc_ssc.id, v.llfc.id, v.valid_from): v
        for v in sess.execute(select(MtcLlfcSsc)).scalars()
    }
    dnos = {}
    llfcs = {}
    sscs = {}
    pcs = {v.code: v for v in sess.execute(select(Pc)).scalars()}
    combos = {
        (v.mtc_llfc_ssc.id, v.pc.id, v.valid_from): v
        for v in sess.execute(select(MtcLlfcSscPc)).scalars()
    }
    for values in rows:
        mtc_code = values[0].zfill(3)  # Meter Timeswitch Class ID
        mtc_from_str = values[1]  # Effective From Settlement Date (MTC)
        mtc_from = parse_date(mtc_from_str)
        mtc = mtcs[(mtc_code, mtc_from)]
        participant_code = values[2]  # Market Participant ID
        participant = participants[participant_code]
        mtc_participant_from_str = values[3]  # Effective From Settlement Date (MTCPA)
        mtc_participant_from = parse_date(mtc_participant_from_str)
        mtc_participant = mtc_participants[
            (mtc.id, participant.id, mtc_participant_from)
        ]
        ssc_code = values[4]  # Standard Settlement Configuration ID
        mtc_ssc_from_str = values[5]  # Effective From Settlement date (VMTCSC)
        mtc_ssc_from = parse_date(mtc_ssc_from_str)

        try:
            ssc = sscs[(ssc_code, mtc_ssc_from)]
        except KeyError:
            ssc = sscs[(ssc_code, mtc_ssc_from)] = Ssc.get_by_code(
                sess, ssc_code, mtc_ssc_from
            )

        mtc_ssc = mtc_sscs[(mtc_participant.id, ssc.id, mtc_ssc_from)]
        llfc_code = values[6]  # Line Loss Factor Class ID
        mtc_llfc_ssc_from_str = values[7]  # Effective From Settlement Date (VMTCLSC)
        mtc_llfc_ssc_from = parse_date(mtc_llfc_ssc_from_str)
        pc_code = values[8].zfill(2)  # Profile Class ID
        valid_from_str = values[9]  # Effective From Settlement Date (VMTCLSPC)
        valid_from = parse_date(valid_from_str)
        valid_to_str = values[10]  # Effective To Settlement Date (VMTCLSPC)
        valid_to = parse_to_date(valid_to_str)

        try:
            dno = dnos[(participant_code, valid_from)]
        except KeyError:
            dno = dnos[(participant_code, valid_from)] = sess.execute(
                select(Party)
                .join(Participant)
                .join(MarketRole)
                .where(
                    Participant.code == participant_code,
                    MarketRole.code == "R",
                    Party.valid_from <= valid_from,
                    or_(Party.valid_to == null(), Party.valid_to >= valid_from),
                )
            ).scalar_one()

        try:
            llfc = llfcs[(dno.id, llfc_code, mtc_llfc_ssc_from)]
        except KeyError:
            llfc = llfcs[(dno.id, llfc_code, mtc_llfc_ssc_from)] = dno.get_llfc_by_code(
                sess, llfc_code, mtc_llfc_ssc_from
            )

        mtc_llfc_ssc = mtc_llfc_sscs[(mtc_ssc.id, llfc.id, mtc_llfc_ssc_from)]

        pc = pcs[pc_code]
        try:
            combo = combos[(mtc_llfc_ssc.id, pc.id, valid_from)]
            combo.valid_to = valid_to
            sess.flush()
        except KeyError:
            MtcLlfcSscPc.insert(
                sess,
                mtc_llfc_ssc,
                pc,
                valid_from,
                valid_to,
            )


def import_mdd(sess, repo_url, logger):
    s = requests.Session()
    s.verify = False
    mdd_entries = {}
    for year_entry in s.get(f"{repo_url}/contents").json():
        if year_entry["type"] == "dir":
            for util_entry in s.get(year_entry["url"]).json():
                if util_entry["name"] == "electricity" and util_entry["type"] == "dir":
                    for dl_entry in s.get(util_entry["url"]).json():
                        if dl_entry["name"] == "mdd" and dl_entry["type"] == "dir":
                            for mdd_entry in s.get(dl_entry["url"]).json():
                                if mdd_entry["type"] == "dir":
                                    mdd_entries[mdd_entry["name"]] = mdd_entry

    if len(mdd_entries) == 0:
        raise BadRequest("Can't find any MDD versions on the rate server.")

    mdd_entry = sorted(mdd_entries.items())[-1][1]
    mdd_version = int(mdd_entry["name"])
    logger(f"Latest version on rate server: {mdd_version} at {mdd_entry['path']}")

    config = Contract.get_non_core_by_name(sess, "configuration")
    state = config.make_state()
    current_version = state.get("mdd_version", 0)

    logger(f"Latest version in Chellow: {current_version}")
    if mdd_version <= current_version:
        return

    gnames = {}
    ctx = {}
    version = None

    for entry in s.get(mdd_entry["url"]).json():
        if entry["type"] == "file":
            csv_file = StringIO(s.get(entry["download_url"]).text)
            csv_reader = iter(csv.reader(csv_file))
            next(csv_reader)  # Skip titles

            entry_name = entry["name"]
            table_name_elements = entry_name.split("_")
            ver = int(table_name_elements[-1].split(".")[0])
            if version is None:
                version = ver

            if version != ver:
                raise BadRequest(
                    f"There's a mixture of MDD versions in the file names. "
                    f"Expected version {version} but found version {ver} in "
                    f"{entry_name}."
                )
            table_name = "_".join(table_name_elements[:-1])
            gnames[table_name] = list(csv_reader)

    for tname, func in [
        ("GSP_Group", _import_GSP_Group),
        ("Market_Participant", _import_Market_Participant),
        ("Market_Role", _import_Market_Role),
        ("Market_Participant_Role", _import_Market_Participant_Role),
        ("Line_Loss_Factor_Class", _import_Line_Loss_Factor_Class),
        ("MTC_Meter_Type", _import_MTC_Meter_Type),
        ("MTC_Payment_Type", _import_MTC_Payment_Type),
        ("Meter_Timeswitch_Class", _import_Meter_Timeswitch_Class),
        ("MTC_in_PES_Area", _import_MTC_in_PES_Area),
        (
            "Standard_Settlement_Configuration",
            _import_Standard_Settlement_Configuration,
        ),
        (
            "Valid_MTC_LLFC_Combination",
            _import_Valid_MTC_LLFC_Combination,
        ),
        (
            "Valid_MTC_SSC_Combination",
            _import_Valid_MTC_SSC_Combination,
        ),
        (
            "Valid_MTC_LLFC_SSC_Combination",
            _import_Valid_MTC_LLFC_SSC_Combination,
        ),
        ("Profile_Class", _import_Profile_Class),
        (
            "Valid_MTC_LLFC_SSC_PC_Combination",
            _import_Valid_MTC_LLFC_SSC_PC_Combination,
        ),
    ]:

        if tname in gnames:
            logger(f"Found {tname} and will now import it.")
            func(sess, gnames[tname], ctx)
        else:
            raise BadRequest(f"Can't find {tname} on the rate server.")

    config = Contract.get_non_core_by_name(sess, "configuration")
    state = config.make_state()
    state["mdd_version"] = version
    config.update_state(state)
    sess.commit()
