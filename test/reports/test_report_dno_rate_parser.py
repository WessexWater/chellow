from chellow.reports.report_dno_rate_parser import to_llfcs, to_pcs


def test_to_llfcs(mocker):
    llfc_str = "H00-H01"
    mocker.patch(
        "chellow.reports.report_dno_rate_parser.get_value", return_value=llfc_str
    )

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_llfcs(row, idx)
    assert actual == ["H00", "H01"]


def test_to_pcs(mocker):
    pc_str = "3 to 8 or 0"
    mocker.patch(
        "chellow.reports.report_dno_rate_parser.get_value", return_value=pc_str
    )

    row = mocker.Mock()
    idx = mocker.Mock()
    actual = to_pcs(row, idx)
    assert actual == ["03", "04", "05", "06", "07", "08", "00"]
