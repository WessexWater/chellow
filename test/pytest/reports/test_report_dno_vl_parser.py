from chellow.reports.report_dno_vl_parser import _make_row, to_llfcs
from chellow.utils import ct_datetime, to_utc


def test_to_llfcs_desc(mocker):
    llfc_str = "310 - 311 inclusive"

    actual = to_llfcs(llfc_str)
    assert actual == ["310", "311"]


def test_to_llfcs_lines(mocker):
    llfc_str = """310
311
"""

    actual = to_llfcs(llfc_str)
    assert actual == ["310", "311"]


def test_make_row(mocker):
    llfc = mocker.Mock()
    llfc.code = '651'
    voltage_level = mocker.Mock()
    llfc.voltage_level = voltage_level
    voltage_level.code = 'LV'
    llfc.is_substation = False
    llfc.valid_from = to_utc(ct_datetime(2020, 4, 1))
    dno = mocker.Mock()
    llfc.dno = dno
    dno.dno_code = '22'

    ss_llfc = {
        'voltage_level': 'HV',
        'is_substation': False,
    }

    actual = _make_row(llfc, ss_llfc)

    expected = (
        'update', 'llfc', '22', '651', '2020-04-01 00:00', '{no change}',
        'HV', '{no change}', '{no change}', '{no change}'
    )
    assert actual == expected
