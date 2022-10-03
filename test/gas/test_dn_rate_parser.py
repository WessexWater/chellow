from decimal import Decimal

from chellow.gas.dn_rate_parser import (
    State,
    _handle_EXIT_CAPACITY,
    _handle_SECTION,
    find_dn_rates,
    tab_gdn_unit_rates,
)


def test_handle_EXIT_CAPACITY_first_row(mocker):
    state = State.EXIT_CAPACITY
    b1 = mocker.Mock()
    b1.value = "EXIT CAPACITY UNIT RATES BY EXIT ZONE"
    sheet = {"B1": b1}
    row = 1
    rates = {}
    networks = {"EE": "C"}

    _handle_EXIT_CAPACITY(state, sheet, row, rates, networks)

    assert rates == {}


def test_handle_EXIT_CAPACITY_rate_row(mocker):
    state = State.EXIT_CAPACITY
    b1 = mocker.Mock()
    b1.value = "EA1"
    c1 = mocker.Mock()
    c1.value = 0.2
    sheet = {"B1": b1, "C1": c1}
    row = 1
    rates = {"exit_zones": {}}
    networks = {"EE": "C"}

    _handle_EXIT_CAPACITY(state, sheet, row, rates, networks)

    expected = {
        "exit_zones": {"EA1": {"exit_capacity_gbp_per_kwh_per_day": Decimal("0.002")}}
    }
    assert rates == expected


def test_handle_SECTION_system_capacity_to_73200(mocker):
    state = State.SYSTEM_CAPACITY
    b1 = mocker.Mock()
    b1.value = "UP TO 73,200 KWH PER ANNUM"
    c1 = mocker.Mock()
    c1.value = 0.2
    sheet = {"B1": b1, "C1": c1}
    row = 1
    rates = {"gdn": {"EE": {"system_capacity": {}}}}
    networks = {"EE": "C"}

    _handle_SECTION(state, sheet, row, rates, networks)

    expected = {
        "gdn": {
            "EE": {
                "system_capacity": {"to_73200_gbp_per_kwh_per_day": Decimal("0.002")}
            }
        }
    }
    assert rates == expected


def test_handle_SECTION_system_capacity_73200_and_over(mocker):
    state = State.SYSTEM_CAPACITY
    b1 = mocker.Mock()
    b1.value = "732,000 KWH PER ANNUM AND ABOVE"
    c1 = mocker.Mock()
    c1.value = 0.2
    c3 = mocker.Mock()
    c3.value = 0.6
    sheet = {"B1": b1, "C1": c1, "C3": c3}
    row = 1
    rates = {"gdn": {"EE": {"system_capacity": {"732000_and_over": {}}}}}
    networks = {"EE": "C"}

    _handle_SECTION(state, sheet, row, rates, networks)

    expected = {
        "gdn": {
            "EE": {
                "system_capacity": {
                    "732000_and_over": {
                        "gbp_per_kwh_per_day": Decimal("0.002000"),
                        "exponent": Decimal("0.6000"),
                    }
                }
            }
        }
    }
    assert rates == expected


def test_handle_SECTION_system_capacity_minimum(mocker):
    state = State.SYSTEM_CAPACITY
    b1 = mocker.Mock()
    b1.value = "SUBJECT TO A MINIMUM RATE OF"
    c1 = mocker.Mock()
    c1.value = 0.2
    sheet = {"B1": b1, "C1": c1}
    row = 1
    rates = {"gdn": {"EE": {"system_capacity": {"732000_and_over": {}}}}}
    networks = {"EE": "C"}

    _handle_SECTION(state, sheet, row, rates, networks)

    expected = {
        "gdn": {
            "EE": {
                "system_capacity": {
                    "732000_and_over": {
                        "minimum_gbp_per_kwh_per_day": Decimal("0.002"),
                    }
                }
            }
        }
    }
    assert rates == expected


def test_tab_gdn_unit_rates(mocker):
    b1 = mocker.Mock()
    b1.value = "NETWORK"
    b1.column_letter = "B"
    c1 = mocker.Mock()
    c1.value = "EAST OF ENGLAND"
    c1.column_letter = "C"
    b2 = mocker.Mock()
    b2.value = "EXIT CAPACITY UNIT RATES BY EXIT ZONE"
    b2.column_letter = "B"
    b3 = mocker.Mock()
    b3.value = None
    b3.column_letter = "B"
    sheet = {
        "B1": b1,
        "C1": c1,
        "B2": b2,
        "B3": b3,
        "B": [b1, b2, b3],
        1: [None, b1, c1],
    }
    rates = {"gdn": {}}
    tab_gdn_unit_rates(sheet, rates)


def test_find_dn_rates(mocker):
    mock_book = mocker.Mock()
    mock_book.worksheets = []
    mocker.patch(
        "chellow.gas.dn_rate_parser.openpyxl.load_workbook", return_value=mock_book
    )
    file_name = "fname.xls"
    file_like = mocker.Mock()
    rates = find_dn_rates(file_name, file_like)
    assert rates == {"a_file_name": file_name, "exit_zones": {}, "gdn": {}}
