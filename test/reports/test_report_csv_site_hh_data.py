from io import StringIO

from utils import match

from chellow.models import User
from chellow.reports.report_csv_site_hh_data import content
from chellow.utils import ct_datetime, to_utc


def test_do_get(client, mocker, sess):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_csv_site_hh_data.open_file", return_value=mock_file
    )
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
