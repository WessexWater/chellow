import pytest

from werkzeug.exceptions import BadRequest

from chellow.e.bill_parsers.haven_csv import _process_READING, _process_line, _to_date
from chellow.utils import ct_datetime, to_utc


def test_process_line_unknown_code(mocker):
    code = "BOB"
    row = []
    headers = {}

    with pytest.raises(BadRequest, match=code):
        _process_line(code, row, headers)


def test_process_line_SUMMARY():
    code = "SUMMARY"
    row = []
    headers = {}

    _process_line(code, row, headers)


def test_to_date():
    date_str = "20200430"
    row = [date_str]
    dt = _to_date(row, 0)
    assert dt == to_utc(ct_datetime(2020, 4, 30))


def test_process_READING_unknown_unit():
    units = "BOB"
    row = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "20200401",  # 11
        0,
        "E",
        "20200430",
        0,
        "E",
        0,
        units,
    ]
    headers = {}

    with pytest.raises(BadRequest, match=units):
        _process_READING(row, headers)


def test_process_READING_success():
    row = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "20200401",  # 11
        0,
        "E",
        "20200430",
        0,
        "E",
        0,
        "KWH",
    ]
    headers = {"reads": []}

    _process_READING(row, headers)
