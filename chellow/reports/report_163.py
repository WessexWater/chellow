import csv
import os
import threading
import traceback
from datetime import datetime as Datetime, timedelta as Timedelta
from io import BytesIO, StringIO
from zipfile import ZipFile

from flask import g, render_template, request

from sqlalchemy import null
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.models import (
    Llfc,
    MarketRole,
    MeterType,
    Mtc,
    Participant,
    Party,
    Session,
    VoltageLevel,
)
from chellow.utils import ct_datetime, hh_format, to_ct, to_utc
from chellow.views import chellow_redirect


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


def is_common_mtc(code):
    return 499 < code < 510 or 799 < code < 1000


def do_get(sess):
    return render_template("report_163.html")


VOLTAGE_MAP = {"24": {"602": {to_utc(ct_datetime(2010, 4, 1)): "LV"}}}


def _parse_Line_Loss_Factor_Class(sess, csv_reader):
    VOLTAGE_LEVEL_CODES = set([v.code for v in sess.query(VoltageLevel)])
    DNO_MAP = dict(
        (dno.participant.code, dno)
        for dno in sess.query(Party)
        .join(MarketRole)
        .filter(MarketRole.code == "R")
        .options(joinedload(Party.participant))
    )

    rows = []
    for values in csv_reader:
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
            rows.append(("# There is no DNO with participant code ", participant_code))
            continue

        try:
            voltage_level_code = VOLTAGE_MAP[dno.dno_code][llfc_code][valid_from]
        except KeyError:
            voltage_level_code = "LV"
            description_upper = description.upper()
            for vl_code in VOLTAGE_LEVEL_CODES:
                if vl_code in description_upper:
                    voltage_level_code = vl_code
                    break

        llfc = (
            sess.query(Llfc)
            .filter(
                Llfc.dno == dno, Llfc.code == llfc_code, Llfc.valid_from == valid_from
            )
            .first()
        )

        if llfc is None:
            row = (
                "insert",
                "llfc",
                dno.dno_code,
                llfc_code,
                description,
                voltage_level_code,
                is_substation,
                is_import,
                hh_format(valid_from),
                hh_format(valid_to, ongoing_str=""),
            )
            rows.append(row)

        elif any(
            (
                description != llfc.description,
                voltage_level_code != llfc.voltage_level.code,
                is_substation != llfc.is_substation,
                is_import != llfc.is_import,
                valid_to != llfc.valid_to,
            )
        ):
            row = (
                "update",
                "llfc",
                dno.dno_code,
                llfc.code,
                hh_format(llfc.valid_from),
                description,
                voltage_level_code,
                is_substation,
                is_import,
                hh_format(valid_to, ongoing_str=""),
            )
            rows.append(row)

    return rows


def _parse_Market_Participant(sess, csv_reader):
    rows = []
    for values in csv_reader:
        participant_code = values[0]
        participant_name = values[1]

        participant = (
            sess.query(Participant).filter(Participant.code == participant_code).first()
        )

        if participant is None:
            row = "insert", "participant", participant_code, participant_name
            rows.append(row)

        elif participant_name != participant.name:
            row = "update", "participant", participant_code, participant_name
            rows.append(row)

    return rows


def _parse_Market_Role(sess, csv_reader):
    rows = []
    for values in csv_reader:
        role_code = values[0]
        role_description = values[1]

        role = sess.query(MarketRole).filter(MarketRole.code == role_code).first()

        if role is None:
            row = "insert", "market_role", role_code, role_description
            rows.append(row)

        elif role_description != role.description:
            row = "update", "market_role", role_code, role_description
            rows.append(row)

    return rows


def _parse_Market_Participant_Role(sess, csv_reader):
    rows = []
    for values in csv_reader:
        participant_code = values[0]
        market_role_code = values[1]
        valid_from = parse_date(values[2])
        party = (
            sess.query(Party)
            .join(Participant)
            .join(MarketRole)
            .filter(
                Party.valid_from == valid_from,
                Participant.code == participant_code,
                MarketRole.code == market_role_code,
            )
            .first()
        )
        valid_to = parse_to_date(values[3])
        name = values[4]
        dno_code_str = values[14]
        dno_code = None if len(dno_code_str) == 0 else dno_code_str
        if dno_code == "99":
            continue

        if party is None:
            row = (
                "insert",
                "party",
                market_role_code,
                participant_code,
                name,
                hh_format(valid_from),
                hh_format(valid_to, ongoing_str=""),
                dno_code_str,
            )
            rows.append(row)

        elif any(
            (name != party.name, dno_code != party.dno_code, valid_to != party.valid_to)
        ):
            row = (
                "update",
                "party",
                market_role_code,
                participant_code,
                name,
                hh_format(valid_from),
                hh_format(valid_to, ongoing_str=""),
                dno_code_str,
            )
            rows.append(row)

    return rows


def _parse_Meter_Timeswitch_Class(sess, csv_reader):
    rows = []
    for values in csv_reader:
        code = values[0].zfill(3)
        valid_from = parse_date(values[1])
        valid_to = parse_to_date(values[2])
        description = values[3]
        is_common = values[4] == "T"
        has_related_metering = values[5] == "T"
        meter_type_code = values[6]
        meter_payment_type_code = values[7]
        has_comms = values[8] == "T"
        is_hh = values[9] == "H"
        tpr_count_str = values[10]
        tpr_count = 0 if tpr_count_str == "" else int(tpr_count_str)

        if is_common:
            mtc = (
                sess.query(Mtc)
                .filter(
                    Mtc.dno == null(), Mtc.code == code, Mtc.valid_from == valid_from
                )
                .first()
            )
            if mtc is None:
                row = (
                    "insert",
                    "mtc",
                    "",
                    code,
                    description,
                    has_related_metering,
                    has_comms,
                    is_hh,
                    meter_type_code,
                    meter_payment_type_code,
                    tpr_count,
                    hh_format(valid_from),
                    hh_format(valid_to, ongoing_str=""),
                )
                rows.append(row)

            elif any(
                (
                    description != mtc.description,
                    has_related_metering != mtc.has_related_metering,
                    has_comms != mtc.has_comms,
                    is_hh != mtc.is_hh,
                    meter_type_code != mtc.meter_type.code,
                    meter_payment_type_code != mtc.meter_payment_type.code,
                    tpr_count != mtc.tpr_count,
                    valid_to != mtc.valid_to,
                )
            ):
                row = (
                    "update",
                    "mtc",
                    "",
                    mtc.code,
                    description,
                    has_related_metering,
                    has_comms,
                    is_hh,
                    meter_type_code,
                    meter_payment_type_code,
                    tpr_count,
                    hh_format(mtc.valid_from),
                    hh_format(valid_to, ongoing_str=""),
                )
                rows.append(row)

    return rows


def _parse_MTC_in_PES_Area(sess, csv_reader):
    rows = []
    dnos = dict(
        (p.participant.code, (p.id, p.dno_code))
        for p in sess.query(Party)
        .join(Participant)
        .join(MarketRole)
        .filter(MarketRole.code == "R")
        .options(joinedload(Party.participant))
    )
    mtcs = dict(
        ((m.dno_id, m.code, m.valid_from), m)
        for m in sess.query(Mtc)
        .options(joinedload(Mtc.meter_type), joinedload(Mtc.meter_payment_type))
        .all()
    )

    for values in csv_reader:
        code_str = values[0]
        if not Mtc.has_dno(code_str):
            continue

        code_int = int(code_str)
        code = code_str.zfill(3)
        participant_code = values[2]
        dno_id, dno_code = dnos[participant_code]
        valid_from = parse_date(values[3])
        valid_to = parse_to_date(values[4])
        description = values[5]
        meter_type_code = values[6]
        meter_payment_type_code = values[7]
        has_related_metering = code_int > 500
        has_comms = values[8] == "Y"
        is_hh = values[9] == "H"
        tpr_count_str = values[10]
        tpr_count = 0 if tpr_count_str == "" else int(tpr_count_str)

        mtc = mtcs.get((dno_id, code, valid_from))

        if mtc is None:
            row = (
                "insert",
                "mtc",
                dno_code,
                code,
                description,
                has_related_metering,
                has_comms,
                is_hh,
                meter_type_code,
                meter_payment_type_code,
                tpr_count,
                hh_format(valid_from),
                hh_format(valid_to, ongoing_str=""),
            )
            rows.append(row)

        elif any(
            (
                description != mtc.description,
                has_related_metering != mtc.has_related_metering,
                has_comms != mtc.has_comms,
                is_hh != mtc.is_hh,
                meter_type_code != mtc.meter_type.code,
                meter_payment_type_code != mtc.meter_payment_type.code,
                tpr_count != mtc.tpr_count,
                valid_to != mtc.valid_to,
            )
        ):
            row = (
                "update",
                "mtc",
                mtc.dno.dno_code,
                mtc.code,
                description,
                has_related_metering,
                has_comms,
                is_hh,
                meter_type_code,
                meter_payment_type_code,
                tpr_count,
                hh_format(mtc.valid_from),
                hh_format(valid_to, ongoing_str=""),
            )
            rows.append(row)

    return rows


def _parse_MTC_Meter_Type(sess, csv_reader):
    rows = []
    for values in csv_reader:
        code = values[0]
        description = values[1]
        valid_from = parse_date(values[2])
        valid_to = parse_to_date(values[3])
        pt = (
            sess.query(MeterType)
            .filter(MeterType.code == code, MeterType.valid_from == valid_from)
            .first()
        )
        if pt is None:
            row = (
                "insert",
                "meter_type",
                code,
                description,
                hh_format(valid_from),
                hh_format(valid_to, ongoing_str=""),
            )
            rows.append(row)

        elif (description, valid_from, valid_to) != (
            pt.description,
            pt.valid_from,
            pt.valid_to,
        ):
            row = (
                "update",
                "meter_type",
                code,
                description,
                hh_format(valid_from),
                hh_format(valid_to),
            )
            rows.append(row)

    return rows


def content(fin, user):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "mdd__general_import.csv", user
        )
        f = open(running_name, mode="w", newline="")
        w = csv.writer(f, lineterminator="\n")

        zip_file = ZipFile(fin)
        for zname in zip_file.namelist():
            csv_file = StringIO(zip_file.read(zname).decode("utf-8"))
            csv_reader = iter(csv.reader(csv_file))
            next(csv_reader)  # Skip titles
            rows = []

            if zname.startswith("Line_Loss_Factor_Class"):
                rows = _parse_Line_Loss_Factor_Class(sess, csv_reader)

            elif zname.startswith("Market_Participant"):
                rows = _parse_Market_Participant(sess, csv_reader)

            elif zname.startswith("Market_Role"):
                rows = _parse_Market_Role(sess, csv_reader)

            elif zname.startswith("Market_Participant_Role"):
                rows = _parse_Market_Participant_Role(sess, csv_reader)

            elif zname.startswith("Meter_Timeswitch_Class"):
                rows = _parse_Meter_Timeswitch_Class(sess, csv_reader)

            elif zname.startswith("MTC_in_PES_Area"):
                rows = _parse_MTC_in_PES_Area(sess, csv_reader)

            elif zname.startswith("MTC_Meter_Type"):
                rows = _parse_MTC_Meter_Type(sess, csv_reader)

            w.writerows(rows)

    except BaseException:
        w.writerow([traceback.format_exc()])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_post(sess):
    file_item = request.files["file"]
    file_path = file_item.filename
    file_head, file_name = os.path.split(file_path)
    file_title, file_ext = os.path.splitext(file_name)
    if file_ext != ".zip":
        raise BadRequest(
            f"The file name should have the extension .zip, but in fact it "
            f"has the extension '{file_ext}'."
        )
    f = BytesIO(file_item.read())
    f.seek(0)

    threading.Thread(target=content, args=(f, g.user)).start()
    return chellow_redirect("/downloads", 303)
