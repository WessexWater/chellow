from decimal import Decimal
from enum import Enum, auto
from io import BytesIO

import openpyxl

from sqlalchemy import select

from werkzeug.exceptions import BadRequest

from chellow.models import GContract, GRateScript
from chellow.rate_server import download
from chellow.utils import (
    ct_datetime,
    hh_format,
    to_utc,
)


def get_rate(sheet, col, row):
    return get_decimal(sheet, col, row) / Decimal("100")


def get_decimal(sheet, col, row):
    return round(Decimal(get_value(sheet, col, row)), 4)


def normalize_text(txt):
    return None if txt is None else " ".join(txt.split()).lower()


def get_str(sheet, row, idx):
    return str(get_value(sheet, row, idx)).strip()


def get_value(sheet, col, row):
    return get_cell(sheet, col, row).value


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


class State(Enum):
    BLANK = auto()
    NETWORK = auto()
    SYSTEM_COMMODITY = auto()
    SYSTEM_CAPACITY = auto()
    CUSTOMER_CAPACITY = auto()
    CUSTOMER_FIXED = auto()
    ADMIN_CHARGE = auto()
    EXIT_CAPACITY = auto()


def _handle_NETWORK(state, sheet, row, rates, networks):
    for cell in sheet[row][2:]:
        if cell.value is not None and len(cell.value) > 0:
            dn_text = normalize_text(cell.value)
            dn_code = DN_LOOKUP[dn_text]
            networks[dn_code] = cell.column_letter
            rates["gdn"][dn_code] = {
                "system_commodity": {"732000_and_over": {}},
                "system_capacity": {"732000_and_over": {}},
                "customer_capacity": {"732000_and_over": {}},
                "customer_fixed": {},
            }


def _handle_SECTION(state, sheet, row, rates, networks):
    b_cell = get_cell(sheet, "B", row)
    b_val = normalize_text(get_value(sheet, "B", row))
    if b_val not in (
        "ldz system commodity charges",
        "ldz system commodity charges",
        "ldz customer fixed charges",
        "ldz system capacity charges",
        "ldz customer capacity charges",
    ) and not isinstance(b_cell, openpyxl.cell.cell.MergedCell):
        section_name = SECTION_LOOKUP[state]
        rate_name = RATE_NAMES[section_name][b_val]

        for dn_code, col in networks.items():
            state_rates = rates["gdn"][dn_code][section_name]
            if rate_name == "732000_and_over":
                if state in (State.SYSTEM_CAPACITY, State.CUSTOMER_CAPACITY):
                    suffix = "_per_day"
                else:
                    suffix = ""
                over_rates = state_rates[rate_name]
                over_rates[f"gbp_per_kwh{suffix}"] = get_rate(sheet, col, row)
                over_rates["exponent"] = get_decimal(sheet, col, row + 2)
            elif rate_name == "minimum_gbp_per_kwh":
                state_rates["732000_and_over"]["minimum_gbp_per_kwh"] = get_rate(
                    sheet, col, row
                )
            elif rate_name == "minimum_gbp_per_kwh_per_day":
                state_rates["732000_and_over"]["minimum_gbp_per_kwh_per_day"] = (
                    get_rate(sheet, col, row)
                )
            else:
                state_rates[rate_name] = get_rate(sheet, col, row)


def _handle_ADMIN_CHARGE(state, sheet, row, rates, networks):
    b_val = normalize_text(get_value(sheet, "B", row))
    if b_val == "supply point admin charge":
        for dn_code, col in networks.items():
            rates["gdn"][dn_code]["cesp_administration_gbp_per_mprn"] = get_rate(
                sheet, col, row
            )


def _handle_EXIT_CAPACITY(state, sheet, row, rates, networks):
    b_val = get_str(sheet, "B", row)
    b_norm = normalize_text(b_val)
    if b_norm != "exit capacity unit rates by exit zone":
        for col in networks.values():
            v = get_value(sheet, col, row)
            if v is not None:
                rates["exit_zones"][b_val] = {
                    "exit_capacity_gbp_per_kwh_per_day": get_rate(sheet, col, row)
                }


def _handle_BLANK(state, sheet, row, rates, networks):
    pass


DN_LOOKUP = {
    "east of england": "EE",
    "london": "LO",
    "north west": "NW",
    "west midlands": "WM",
    "scotland": "SC",
    "southern": "SO",
    "northern": "NO",
    "wales & west": "WW",
}

SECTION_LOOKUP = {
    State.SYSTEM_COMMODITY: "system_commodity",
    State.SYSTEM_CAPACITY: "system_capacity",
    State.CUSTOMER_CAPACITY: "customer_capacity",
    State.CUSTOMER_FIXED: "customer_fixed",
}

HANDLER_LOOKUP = {
    State.NETWORK: _handle_NETWORK,
    State.SYSTEM_COMMODITY: _handle_SECTION,
    State.SYSTEM_CAPACITY: _handle_SECTION,
    State.CUSTOMER_CAPACITY: _handle_SECTION,
    State.CUSTOMER_FIXED: _handle_SECTION,
    State.ADMIN_CHARGE: _handle_ADMIN_CHARGE,
    State.EXIT_CAPACITY: _handle_EXIT_CAPACITY,
    State.BLANK: _handle_BLANK,
}

RATE_NAMES = {
    "system_commodity": {
        "up to 73,200 kwh per annum": "to_73200_gbp_per_kwh",
        "73,200 kwh - 732,000 kwh per annum": "73200_to_732000_gbp_per_kwh",
        "732,000 kwh per annum and above": "732000_and_over",
        "subject to a minimum rate of": "minimum_gbp_per_kwh",
    },
    "system_capacity": {
        "up to 73,200 kwh per annum": "to_73200_gbp_per_kwh_per_day",
        "73,200 kwh - 732,000 kwh per annum": "73200_to_732000_gbp_per_kwh_per_day",
        "732,000 kwh per annum and above": "732000_and_over",
        "subject to a minimum rate of": "minimum_gbp_per_kwh_per_day",
    },
    "customer_capacity": {
        "up to 73,200 kwh per annum": "to_73200_gbp_per_kwh_per_day",
        "73,200 kwh - 732,000 kwh per annum": "73200_to_732000_gbp_per_kwh_per_day",
        "732,000 kwh per annum and above": "732000_and_over",
        "subject to a minimum rate of": "minimum_gbp_per_kwh_per_day",
    },
    "customer_fixed": {
        "73,200 kwh - 732,000 kwh per annum bi annual read sites": "73200_to_732000_"
        "biannual_gbp_per_day",
        "73,200 kwh - 732,000 kwh per annum monthly read sites": "73200_to_732000_"
        "monthly_gbp_per_day",
    },
}

STATE_LOOKUP = {
    "": State.BLANK,
    None: State.BLANK,
    "network": State.NETWORK,
    "ldz system commodity charges": State.SYSTEM_COMMODITY,
    "ldz system capacity charges": State.SYSTEM_CAPACITY,
    "ldz customer capacity charges": State.CUSTOMER_CAPACITY,
    "ldz customer fixed charges": State.CUSTOMER_FIXED,
    "csep administration charge": State.ADMIN_CHARGE,
    "exit capacity unit rates by exit zone": State.EXIT_CAPACITY,
}


def tab_gdn_unit_rates(sheet, rates):
    state = State.BLANK
    networks = {}

    for row in range(1, len(sheet["B"]) + 1):
        cell_1 = get_cell(sheet, "B", row)
        if isinstance(cell_1, openpyxl.cell.cell.Cell):
            val_1 = normalize_text(get_value(sheet, "B", row))
            try:
                state = STATE_LOOKUP[val_1]
            except KeyError:
                pass

        HANDLER_LOOKUP[state](state, sheet, row, rates, networks)


def find_dn_rates(file_name, file_like):
    rates = {"a_file_name": file_name, "exit_zones": {}, "gdn": {}}

    book = openpyxl.load_workbook(file_like, data_only=True)

    for sheet in book.worksheets:
        title = sheet.title.strip().lower()
        if title.startswith("gdn unit rates"):
            tab_gdn_unit_rates(sheet, rates)

    return rates


def find_nts_1_rates(file_name, file_like):
    return find_nts_rates(file_name, file_like, "D")


def find_nts_2_rates(file_name, file_like):
    return find_nts_rates(file_name, file_like, "F")


def get_nts_rate(sheet, col, row):
    val_raw = get_value(sheet, col, row)
    return Decimal("0") if val_raw is None else Decimal(val_raw) / Decimal("100")


def find_nts_rates(file_name, file_like, col):
    rates = {"a_file_name": file_name}

    book = openpyxl.load_workbook(file_like, data_only=True)

    for sheet in book.worksheets:
        title = sheet.title.strip().lower()
        if title.startswith("nts unit rates") or title.startswith("ngt unit rates"):
            rates["so_entry_gbp_per_kwh"] = get_nts_rate(sheet, col, 11)
            rates["so_exit_gbp_per_kwh"] = get_nts_rate(sheet, col, 13)
            rates["to_entry_gbp_per_kwh"] = get_nts_rate(sheet, col, 10)
            rates["to_exit_gbp_per_kwh"] = get_nts_rate(sheet, col, 12)

    return rates


def rate_server_import(sess, log, set_progress, s, paths):
    log("Starting to check for new DN spreadsheets")

    year_entries = {}
    for path, url in paths:
        if len(path) == 4:
            year_str, utility, rate_type, file_name = path
            if utility == "gas" and rate_type == "dn":
                year = int(year_str)
                try:
                    fl_entries = year_entries[year]
                except KeyError:
                    fl_entries = year_entries[year] = {}

                fl_entries[file_name] = url

    for year, year_sheets in sorted(year_entries.items()):
        year_start = to_utc(ct_datetime(year, 4, 1))
        oct_start = to_utc(ct_datetime(year, 10, 1))
        nts_contract = GContract.get_industry_by_name(sess, "nts_commodity")
        if year_start < nts_contract.start_g_rate_script.start_date:
            continue
        nts_rs_1 = sess.execute(
            select(GRateScript).where(
                GRateScript.g_contract == nts_contract,
                GRateScript.start_date == year_start,
            )
        ).scalar_one_or_none()
        if nts_rs_1 is None:
            nts_rs_1 = nts_contract.insert_g_rate_script(sess, year_start, {})

        nts_rs_2 = sess.execute(
            select(GRateScript).where(
                GRateScript.g_contract == nts_contract,
                GRateScript.start_date == oct_start,
            )
        ).scalar_one_or_none()
        if nts_rs_2 is None:
            nts_rs_2 = nts_contract.insert_g_rate_script(sess, oct_start, {})

        dn_contract = GContract.get_industry_by_name(sess, "dn")
        dn_rs = sess.execute(
            select(GRateScript).where(
                GRateScript.g_contract == dn_contract,
                GRateScript.start_date == year_start,
            )
        ).scalar_one_or_none()
        if dn_rs is None:
            dn_rs = dn_contract.insert_g_rate_script(sess, year_start, {})

        if len(year_sheets) > 0:
            file_name, url = sorted(year_sheets.items())[-1]

            nts_rs_1_script = nts_rs_1.make_script()
            if nts_rs_1_script.get("a_file_name") != file_name:
                nts_rs_1.update(find_nts_1_rates(file_name, BytesIO(download(s, url))))
                log(f"Updated NTS rate script for {hh_format(year_start)}")

            nts_rs_2_script = nts_rs_2.make_script()
            if nts_rs_2_script.get("a_file_name") != file_name:
                nts_rs_2.update(find_nts_2_rates(file_name, BytesIO(download(s, url))))
                log(f"Updated NTS rate script for {hh_format(oct_start)}")

            dn_rs_script = dn_rs.make_script()
            if dn_rs_script.get("a_file_name") != file_name:
                dn_rs.update(find_dn_rates(file_name, BytesIO(download(s, url))))
                log(f"Updated DN rate script for {hh_format(year_start)}")

    log("Finished DN spreadsheets")
    sess.commit()
