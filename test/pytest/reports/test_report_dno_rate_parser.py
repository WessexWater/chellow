from chellow.reports.report_dno_rate_parser import to_llfcs


def test_to_llfcs(mocker):
    llfc_str = "H00-H01"
    mocker.patch(
        "chellow.reports.report_dno_rate_parser.get_value", return_value=llfc_str
    )

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_llfcs(row, idx)
    assert actual == ["H00", "H01"]
