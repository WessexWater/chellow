import csv
from io import StringIO

from utils import match, match_tables

from chellow.models import Site, User, UserRole
from chellow.reports.report_csv_site_hh_data import content
from chellow.utils import ct_datetime, to_utc


def test_do_get(client, mocker, sess):
    MockThread = mocker.patch(
        "chellow.reports.report_csv_site_hh_data.threading.Thread"
    )
    user = User.get_by_email_address(sess, "admin@example.com")
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))
    site_id = None
    expected_args = start_date, finish_date, site_id, user.id
    query_string = {
        "start_year": "2020",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2020",
        "finish_month": "01",
        "finish_day": "31",
        "finish_hour": "23",
        "finish_minute": "30",
    }
    response = client.get("/reports/csv_site_hh_data", query_string=query_string)
    match(response, 303)
    MockThread.assert_called_with(target=content, args=expected_args)


def test_content(mocker, sess):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_csv_site_hh_data.open_file", return_value=mock_file
    )

    site = Site.insert(sess, "CI017", "Water Works")
    site_id = site.id
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()

    start_date = to_utc(ct_datetime(2024, 6, 1))
    finish_date = to_utc(ct_datetime(2024, 6, 1))
    content(start_date, finish_date, site_id, user_id)
    mock_file.seek(0)
    actual = list(csv.reader(mock_file))
    expected = [
        [
            "site_id",
            "site_name",
            "associated_site_ids",
            "sources",
            "generator_types",
            "hh_start_clock_time",
            "imported_kwh",
            "displaced_kwh",
            "exported_kwh",
            "used_kwh",
            "parasitic_kwh",
            "generated_kwh",
            "3rd_party_import",
            "3rd_party_export",
            "meter_type",
        ],
        [
            "CI017",
            "Water Works",
            "",
            "",
            "",
            "2024-06-01 00:00",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "0",
            "",
        ],
    ]

    match_tables(expected, actual)
