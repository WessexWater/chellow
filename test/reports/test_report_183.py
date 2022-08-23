from io import BytesIO
from zipfile import ZipFile

from utils import match

from chellow.models import Site, User
from chellow.reports.report_183 import _process_site, none_content
from chellow.utils import ct_datetime, to_utc


def test_do_post(mocker, client, sess):
    user = User.get_by_email_address(sess, "admin@example.com")
    MockThread = mocker.patch("chellow.reports.report_183.threading.Thread")

    data = {
        "start_year": "2022",
        "start_month": "07",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2022",
        "finish_month": "07",
        "finish_day": "31",
        "finish_hour": "23",
        "finish_minute": "30",
        "type": "used",
        "site_codes": "",
    }
    response = client.post("/reports/183", data=data)

    match(response, 303)

    expected_args = (
        None,
        "used",
        to_utc(ct_datetime(2022, 7, 1)),
        to_utc(ct_datetime(2022, 7, 31, 23, 30)),
        user.id,
        "sites_hh_data_202207312330_filter.zip",
    )

    MockThread.assert_called_with(target=none_content, args=expected_args)


def test_do_post_site_codes(mocker, client, sess):
    user = User.get_by_email_address(sess, "admin@example.com")
    MockThread = mocker.patch("chellow.reports.report_183.threading.Thread")

    data = {
        "start_year": "2022",
        "start_month": "07",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2022",
        "finish_month": "07",
        "finish_day": "31",
        "finish_hour": "23",
        "finish_minute": "30",
        "type": "used",
        "site_codes": "8ghh3",
    }
    response = client.post("/reports/183", data=data)

    match(response, 303)

    expected_args = (
        ["8ghh3"],
        "used",
        to_utc(ct_datetime(2022, 7, 1)),
        to_utc(ct_datetime(2022, 7, 31, 23, 30)),
        user.id,
        "sites_hh_data_202207312330_filter.zip",
    )

    MockThread.assert_called_with(target=none_content, args=expected_args)


def test_process_site(sess):
    f = BytesIO()
    zf = ZipFile(f, mode="w")
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = to_utc(ct_datetime(2022, 7, 1))
    finish_date = to_utc(ct_datetime(2022, 7, 31, 23, 30))
    typ = "used"
    _process_site(sess, zf, site, start_date, finish_date, typ)
    assert zf.namelist() == ["CI017_202207312330.csv"]
