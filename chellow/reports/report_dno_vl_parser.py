import csv
import os
import re
import sys
import threading
import traceback
from decimal import Decimal
from io import BytesIO

from flask import g, request

import openpyxl

from sqlalchemy import null, or_

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.models import Llfc, Party, Session
from chellow.utils import ct_datetime, ct_datetime_now, hh_format, req_int, to_utc
from chellow.views.home import chellow_redirect


LV_NET = ("LV", False)
LV_SUB = ("LV", True)
HV_NET = ("HV", False)
HV_SUB = ("HV", True)
EHV_NET = ("EHV", False)


VL_LOOKUP = {
    "Low-voltage network": LV_NET,
    "Low Voltage Network": LV_NET,
    "Low-voltage substation": LV_SUB,
    "Low Voltage Substation": LV_SUB,
    "High-voltage network": HV_NET,
    "High Voltage Network": HV_NET,
    "High-voltage substation": HV_SUB,
    "High Voltage Substation": HV_SUB,
    "Greater than 22kV connected - demand": HV_NET,
    "Greater than 22kV connected - generation": HV_NET,
    "33kV generic": EHV_NET,
    "33kV generic (demand)": EHV_NET,
    "33kV generic (generation)": EHV_NET,
    "132/33kV generic": EHV_NET,
    "132kV to 33kV generic": EHV_NET,
    "132/HV connected": HV_NET,
    "132kV generic": EHV_NET,
    "132kV generic (demand)": EHV_NET,
    "132kV generic (generation)": EHV_NET,
    "132kV connected": EHV_NET,
    "EHV connected": EHV_NET,
    "EHV 33kV Export": EHV_NET,
    "EHV 33kV Import": EHV_NET,
    "132/EHV connected": EHV_NET,
}


def get_value(row, idx):
    val = row[idx].value
    return val.strip() if isinstance(val, str) else val


def to_llfcs(val):
    llfcs = []
    if isinstance(val, str):
        val = ",".join(val.splitlines())
        val = val.replace("/", ",").replace("inclusive", ",")
        for v in map(str.strip, val.split(",")):
            if len(v) > 0:
                if "-" in v:
                    start, finish = v.split("-")
                    m = re.search(r"\d", start)
                    s = m.start()
                    m = re.search(r"\d", finish)
                    f = m.start()

                    for i in range(int(start[s:]), int(finish[f:]) + 1):
                        llfcs.append(str(i))
                else:
                    llfcs.append(v)
    elif isinstance(val, Decimal):
        llfcs.append(str(int(val)))
    elif isinstance(val, float):
        llfcs_str = str(int(val))
        for i in range(0, len(llfcs_str), 3):
            llfcs.append(llfcs_str[i : i + 3])
    elif isinstance(val, int):
        val_str = str(val)
        for i in range(0, len(val_str), 3):
            llfcs.append(val_str[i : i + 3])
    return [v.zfill(3) for v in llfcs]


def col_match(row, pattern, repeats=1):
    for i, cell in enumerate(row):
        txt = cell.value
        if txt is not None:
            txt_str = " ".join(str(txt).lower().split())
            if re.search(pattern, txt_str) is not None:
                if repeats == 1:
                    return i
                else:
                    repeats -= 1

    raise BadRequest(
        f"Pattern '{pattern}' not found in row "
        + ", ".join(str(cell.value) for cell in row)
    )


def tab_llfcs(sheet):
    llfcs = []

    in_llfcs = False
    # title_row = None
    for row in sheet.iter_rows():
        val = get_value(row, 0)
        val_0 = None if val is None else " ".join(val.split())
        if in_llfcs:
            if val_0 is None or len(val_0) == 0:
                in_llfcs = False
            else:
                vl, is_substation = VL_LOOKUP[val_0]
                for llfc_code in to_llfcs(get_value(row, 5)):
                    llfc = {
                        "code": llfc_code,
                        "voltage_level": vl,
                        "is_substation": is_substation,
                    }
                    llfcs.append(llfc)

        elif val_0 == "Metered voltage":
            in_llfcs = True
            # title_row = row

    return llfcs


def content(user, file_name, file_like, dno_id):
    f = sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "voltage_levels_general_importer.csv", user
        )
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")
        titles = (
            "# update",
            "llfc",
            "DNO Code",
            "LLFC Code",
            "Valid From",
            "LLFC Description",
            "Voltage Level Code",
            "Is Substation?",
            "Is Import?",
            "Valid To",
        )
        writer.writerow(titles)
        dno = Party.get_by_id(sess, dno_id)

        if not file_name.endswith(".xlsx"):
            raise BadRequest(f"The file extension for {file_name} isn't recognized.")

        book = openpyxl.load_workbook(file_like, data_only=True, read_only=True)

        TITLE_START = "annex 5 "
        ss_llfcs = []
        for sheet in book.worksheets:
            title = sheet.title.strip().lower()
            print(title)
            if title.startswith(TITLE_START):

                # if llfs_sheet is None:
                #     raise BadRequest(
                #         f"Can't find the sheet with LLFCs in. Looking for a "
                #        f"case-insenstive match on sheet titles begining "
                #       with "
                #        f"'{TITLE_START}'.")
                ss_llfcs.extend(tab_llfcs(sheet))

        now_ct = ct_datetime_now()
        if now_ct.month < 4:
            fy_year_ct = now_ct.year - 1
        else:
            fy_year_ct = now_ct.year

        fy_start = to_utc(ct_datetime(fy_year_ct, 4, 1))
        fy_finish = to_utc(ct_datetime(fy_year_ct + 1, 3, 31, 23, 30))
        for ss_llfc in ss_llfcs:
            ss_llfc_code = ss_llfc["code"]
            llfc = (
                sess.query(Llfc)
                .filter(
                    Llfc.dno == dno,
                    Llfc.code == ss_llfc_code,
                    Llfc.valid_from <= fy_finish,
                    or_(Llfc.valid_to == null(), Llfc.valid_to >= fy_start),
                )
                .first()
            )

            if llfc is None:
                raise BadRequest(
                    f"There is no LLFC with the code '{ss_llfc_code}' "
                    f"associated with the DNO {dno.code} from "
                    f"{hh_format(fy_start)} to {hh_format(fy_finish)}."
                )

            row = _make_row(llfc, ss_llfc)
            if row is not None:
                writer.writerow(row)

            # Avoid a long-running transaction
            sess.rollback()

    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def _make_row(llfc, ss_llfc):
    if (
        llfc.voltage_level.code != ss_llfc["voltage_level"]
        or llfc.is_substation != ss_llfc["is_substation"]
    ):

        if llfc.voltage_level.code != ss_llfc["voltage_level"]:
            new_vl = ss_llfc["voltage_level"]
        else:
            new_vl = "{no change}"

        if llfc.is_substation != ss_llfc["is_substation"]:
            new_ss = ss_llfc["is_substation"]
        else:
            new_ss = "{no change}"

        return (
            "update",
            "llfc",
            llfc.dno.dno_code,
            llfc.code,
            hh_format(llfc.valid_from),
            "{no change}",
            new_vl,
            new_ss,
            "{no change}",
            "{no change}",
        )


def do_post(session):
    user = g.user
    file_item = request.files["dno_file"]
    dno_id = req_int("dno_id")

    args = user, file_item.filename, BytesIO(file_item.read()), dno_id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
