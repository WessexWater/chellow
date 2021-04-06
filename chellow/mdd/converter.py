import csv
import os
import shutil
import sys
from datetime import timedelta as Timedelta

from chellow.utils import ct_datetime, to_utc


mdd_ver = None
GSP_PREFIX = "GSP_Group_"
DOWNLOAD_DIR = "download"

for nm in os.listdir(DOWNLOAD_DIR):
    if nm.startswith(GSP_PREFIX):
        mdd_ver = nm[len(GSP_PREFIX) : -4]
        break

if mdd_ver is None:
    sys.exit(
        "Can't find a file beginning with "
        + GSP_PREFIX
        + " in the '"
        + DOWNLOAD_DIR
        + "' directory."
    )
else:
    print("MDD version is " + mdd_ver + ".")


def to_date(dmy):
    if len(dmy) == 0:
        return None
    else:
        return ct_datetime(int(dmy[6:]), int(dmy[3:5]), int(dmy[:2]))


FMT = "%Y-%m-%d %H:%M:%S+00"


def to_vf(dmy):
    dt = to_date(dmy)
    if dt is None:
        return ""
    else:
        return to_utc(dt).strftime(FMT)


def to_vt(dmy):
    dt = to_date(dmy)
    if dt is None:
        return ""
    else:
        return to_utc(dt + Timedelta(hours=23, minutes=30)).strftime(FMT)


for nm in os.listdir(DOWNLOAD_DIR):
    shutil.copyfile("download/" + nm, "original/" + nm[: -5 - len(mdd_ver)] + ".csv")

dno_lookup = {}


gsp_group_map = {}
with open("original/GSP_Group.csv") as fl, open("converted/gsp_group.csv", "w") as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "description"])
    for eid, line in enumerate(f):
        code = line[0]
        description = line[1]

        gsp_group_map[code] = eid
        converted.writerow([eid, code, description])


participant_map = {}
with open("original/Market_Participant.csv") as fl, open(
    "converted/participant.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "name"])
    for eid, line in enumerate(f):
        code = line[0]
        name = line[1]

        participant_map[code] = eid
        converted.writerow([eid, code, name])


market_role_map = {}
with open("original/Market_Role.csv") as fl, open(
    "converted/market_role.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "description"])
    for eid, line in enumerate(f):
        code = line[0]
        description = line[1]

        market_role_map[code] = eid
        converted.writerow([eid, code, description])


meter_type_map = {}
with open("original/MTC_Meter_Type.csv") as fl, open(
    "converted/meter_type.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "description", "valid_from", "valid_to"])
    for eid, line in enumerate(f):
        code = line[0]
        description = line[1]
        valid_from = line[2]
        valid_to = line[3]

        meter_type_map[code] = eid
        converted.writerow([eid, code, description, to_vf(valid_from), to_vt(valid_to)])


meter_payment_type_map = {}
with open("original/MTC_Payment_Type.csv") as fl, open(
    "converted/meter_payment_type.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "description", "valid_from", "valid_to"])
    for eid, line in enumerate(f):
        code = line[0]
        description = line[1]
        valid_from = line[2]
        valid_to = line[3]

        meter_payment_type_map[code] = eid
        converted.writerow([eid, code, description, to_vf(valid_from), to_vt(valid_to)])


pc_map = {}
with open("original/Profile_Class.csv") as fl, open("converted/pc.csv", "w") as conv:
    eid = 0
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "name", "valid_from", "valid_to"])
    converted.writerow([eid, "00", "Half-hourly", "2000-01-01 00:00:00+00", ""])
    for line in f:
        eid += 1
        code = line[0].zfill(2)
        valid_from = line[1]
        name = line[2]
        valid_to = line[4]

        pc_map[(code, valid_from)] = eid
        converted.writerow([eid, code, name, to_vf(valid_from), to_vt(valid_to)])


ssc_map = {}
with open("original/Standard_Settlement_Configuration.csv") as fl, open(
    "converted/ssc.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(
        ["id", "code", "description", "is_import", "valid_from", "valid_to"]
    )
    for eid, line in enumerate(f):
        code = line[0]
        valid_from = line[1]
        valid_to = line[2]
        description = line[3]
        is_import = "1" if line[4] == "I" else "0"

        ssc_map[code] = eid
        converted.writerow(
            [eid, code, description, is_import, to_vf(valid_from), to_vt(valid_to)]
        )

tpr_map = {}
with open("original/Time_Pattern_Regime.csv") as fl, open(
    "converted/tpr.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "code", "is_teleswitch", "is_gmt"])
    for eid, line in enumerate(f):
        code = line[0]
        is_teleswitch = "0" if line[1] == "C" else "1"
        is_gmt = "1" if line[2] == "Y" else "0"

        tpr_map[code] = eid
        converted.writerow([eid, code, is_teleswitch, is_gmt])


party_map = {}
with open("original/Market_Participant_Role.csv") as fl, open(
    "converted/party.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(
        [
            "id",
            "participant_id",
            "market_role_id",
            "name",
            "valid_from",
            "valid_to",
            "dno_code",
        ]
    )

    for eid, line in enumerate(f):
        participant_code = line[0]
        market_role_code = line[1]
        valid_from = line[2]
        valid_to = line[3]
        name = line[4]
        dno_code = line[-1]
        if len(dno_code) > 0:
            if dno_code == "99":
                valid_from = "01/01/2000"
            dno_lookup[participant_code] = eid

        party_map[(participant_code, market_role_code, valid_from)] = eid

        participant_id = participant_map[participant_code]
        market_role_id = market_role_map[market_role_code]
        converted.writerow(
            [
                eid,
                participant_id,
                market_role_id,
                name,
                to_vf(valid_from),
                to_vt(valid_to),
                dno_code,
            ]
        )

    party_id = eid + 1
    participant_code = "CIDA"
    valid_from = "01/01/2000"
    market_role_code = "R"
    party_map[(participant_code, market_role_code, valid_from)] = party_id
    dno_lookup[participant_code] = party_id
    participant_id = participant_map[participant_code]
    market_role_id = market_role_map[market_role_code]
    converted.writerow(
        [
            party_id,
            participant_id,
            market_role_id,
            "Virtual DNO",
            to_vf(valid_from),
            to_vt(""),
            "88",
        ]
    )


with open("original/Clock_Interval.csv") as fl, open(
    "converted/clock_interval.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(
        [
            "id",
            "tpr_id",
            "Day of the Week Id",
            "Start Day",
            "Start Month",
            "End Day",
            "End Month",
            "Start Hour",
            "Start Minute",
            "End Hour",
            "End Minute",
        ]
    )
    for eid, fields in enumerate(f):
        tpr_code = fields[0]
        time_fields = []
        for field in fields[-2:]:
            time_fields += field.split(":")
        converted.writerow([eid, tpr_map[tpr_code]] + fields[1:-2] + time_fields)


voltage_levels = {"LV": "1", "HV": "2", "EHV": "3"}
llfc_map = {}
with open("original/Line_Loss_Factor_Class.csv") as fl, open(
    "converted/llfc.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converter = csv.writer(conv)
    converter.writerow(
        [
            "id",
            "dno_id",
            "code",
            "description",
            "voltage_level_id",
            "is_substation",
            "is_import",
            "valid_from",
            "valid_to",
        ]
    )
    eid = 0
    for fields in f:
        participant_code = fields[0]
        code = fields[3].zfill(3)
        valid_from = fields[4]
        description = fields[5]
        valid_to = fields[7]
        vl_id = voltage_levels["LV"]
        for k, v in voltage_levels.items():
            if k in description:
                vl_id = v
        is_substation = "0"
        for pattern in ["_SS", " SS", " S/S", "(S/S)", "sub", "Sub"]:
            if pattern in description:
                is_substation = "1"
        is_import = "1"
        for pattern in ["C", "D"]:
            if pattern in fields[6]:
                is_import = "0"
        converter.writerow(
            [
                eid,
                dno_lookup[participant_code],
                code,
                description,
                vl_id,
                is_substation,
                is_import,
                to_vf(valid_from),
                to_vt(valid_to),
            ]
        )
        eid += 1

    for participant_code in ("CIDC", "CIDA"):
        for (
            code,
            description,
            voltage_level_id,
            is_substation,
            is_import,
            valid_from,
        ) in (
            ("510", "PC 5-8 & HH HV", 2, 0, 1, "1996-04-01"),
            ("521", "Export (HV)", 2, 0, 0, "1996-04-01"),
            ("570", "PC 5-8 & HH LV", 1, 0, 1, "1996-04-01"),
            ("581", "Export (LV)", 1, 0, 0, "1996-04-01"),
            ("110", "Profile 3 Unrestricted", 1, 0, 1, "1996-04-01"),
            ("210", "Profile 4 Economy 7", 1, 0, 1, "1996-04-01"),
        ):
            converter.writerow(
                (
                    eid,
                    dno_lookup[participant_code],
                    code,
                    description,
                    voltage_level_id,
                    is_substation,
                    is_import,
                    valid_from,
                    "",
                )
            )
            eid += 1

with open("original/Measurement_Requirement.csv") as fl, open(
    "converted/measurement_requirement.csv", "w"
) as conv:
    f = csv.reader(fl)
    next(f)
    converted = csv.writer(conv)
    converted.writerow(["id", "ssc_id", "tpr_id"])
    for eid, fields in enumerate(f):
        ssc_code = fields[0]
        ssc_id = ssc_map[ssc_code]
        tpr_code = fields[1]
        tpr_id = tpr_map[tpr_code]
        converted.writerow([str(eid), ssc_id, tpr_id])

mtc_map = {}
with open("converted/mtc.csv", "w") as conv:
    converted = csv.writer(conv)
    eid = 0
    converted.writerow(
        [
            "id",
            "dno_id",
            "code",
            "description",
            "has_related_metering",
            "has_comms",
            "is_hh",
            "meter_type_id",
            "meter_payment_type_id",
            "tpr_count",
            "valid_from",
            "valid_to",
        ]
    )
    with open("original/Meter_Timeswitch_Class.csv") as orig_file:
        f = csv.reader(orig_file)
        next(f)
        for fields in f:
            mtc_code = fields[0].zfill(3)
            mtc_code_int = int(mtc_code)
            if 499 < mtc_code_int < 510 or 799 < mtc_code_int < 1000:
                valid_from = fields[1]
                valid_to = fields[2]
                description = fields[3]
                meter_type_code = fields[6]
                meter_payment_type_code = fields[7]
                has_related_meter = "1" if fields[5] == "T" else "0"
                has_comms = "1" if fields[8] == "Y" else "0"
                is_hh = "1" if fields[9] == "H" else "0"
                tpr_count_str = fields[10]
                tpr_count = "0" if len(tpr_count_str) == 0 else tpr_count_str
                meter_type_id = meter_type_map[meter_type_code]
                meter_payment_type_id = meter_payment_type_map[meter_payment_type_code]
                converted.writerow(
                    [
                        eid,
                        "",
                        mtc_code,
                        description,
                        has_related_meter,
                        has_comms,
                        is_hh,
                        meter_type_id,
                        meter_payment_type_id,
                        tpr_count,
                        to_vf(valid_from),
                        to_vf(valid_to),
                    ]
                )
                eid += 1

    with open("original/MTC_in_PES_Area.csv") as orig_file:
        f = csv.reader(orig_file)
        next(f)
        for fields in f:
            mtc_code = fields[0].zfill(3)
            mtc_code_int = int(mtc_code)
            if not (499 < mtc_code_int < 510 or 799 < mtc_code_int < 1000):
                participant_code = fields[2]
                valid_from = fields[3]
                valid_to = fields[4]
                description = fields[5]
                meter_type_code = fields[6]
                payment_type_code = fields[7]
                has_related_meter = "1" if mtc_code_int > 500 else "0"
                has_comms = "1" if fields[8] == "Y" else "0"
                is_hh = "1" if fields[9] == "H" else "0"
                dno_id = dno_lookup[participant_code]
                meter_type_id = meter_type_map[meter_type_code]
                payment_type_id = meter_payment_type_map[payment_type_code]
                tpr_count_str = fields[10]
                tpr_count = "0" if len(tpr_count_str) == 0 else tpr_count_str
                converted.writerow(
                    [
                        eid,
                        dno_id,
                        mtc_code,
                        description,
                        has_related_meter,
                        has_comms,
                        is_hh,
                        meter_type_id,
                        payment_type_id,
                        tpr_count,
                        to_vf(valid_from),
                        to_vt(valid_to),
                    ]
                )
                eid += 1
