from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

import pytest

from chellow.e.dno_rate_parser import find_rates, str_to_hr, to_llfcs, to_pcs


@pytest.mark.parametrize("llfc_str,llfc_list", [["H00-H01", ["H00", "H01"]]])
def test_to_llfcs(mocker, llfc_str, llfc_list):
    mocker.patch("chellow.e.dno_rate_parser.get_value", return_value=llfc_str)

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_llfcs(row, idx)
    assert actual == llfc_list


@pytest.mark.parametrize(
    "pc_str,pc_list", [["3 to 8 or 0", ["03", "04", "05", "06", "07", "08", "00"]]]
)
def test_to_pcs(mocker, pc_str, pc_list):
    mocker.patch("chellow.e.dno_rate_parser.get_value", return_value=pc_str)

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_pcs(row, idx)
    assert actual == pc_list


@pytest.mark.parametrize("hr_str,hr", [["1600", Decimal("16")]])
def test_str_to_hr(mocker, hr_str, hr):
    actual = str_to_hr(hr_str)
    assert actual == hr


def test_find_rates():
    file_name = "a.zip"
    file_like = BytesIO()
    with ZipFile(file_like, "w") as zf:
        zf.writestr("b.txt", "")
    file_like.seek(0)
    find_rates(file_name, file_like)
