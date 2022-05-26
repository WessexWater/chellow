import pytest

from chellow.dno_rate_parser import to_llfcs, to_pcs


@pytest.mark.parametrize("llfc_str,llfc_list", [["H00-H01", ["H00", "H01"]]])
def test_to_llfcs(mocker, llfc_str, llfc_list):
    mocker.patch("chellow.dno_rate_parser.get_value", return_value=llfc_str)

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_llfcs(row, idx)
    assert actual == llfc_list


@pytest.mark.parametrize(
    "pc_str,pc_list", [["3 to 8 or 0", ["03", "04", "05", "06", "07", "08", "00"]]]
)
def test_to_pcs(mocker, pc_str, pc_list):
    mocker.patch("chellow.dno_rate_parser.get_value", return_value=pc_str)

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_pcs(row, idx)
    assert actual == pc_list
