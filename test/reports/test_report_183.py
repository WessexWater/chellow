from io import BytesIO
from zipfile import ZipFile

from requests.auth import _basic_auth_str

from utils import match

from chellow.models import Contract, MarketRole, Participant, Site, User, UserRole
from chellow.reports.report_183 import _process_site, none_content
from chellow.utils import ct_datetime, to_utc


def test_do_post(mocker, client, sess):
    user = User.get_by_email_address(sess, "admin@example.com")
    MockThread = mocker.patch("chellow.reports.report_183.threading.Thread")

    data = {
        "start_year": "2022",
        "start_month": "07",
        "start_day": "01",
        "finish_year": "2022",
        "finish_month": "07",
        "finish_day": "31",
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
        "finish_year": "2022",
        "finish_month": "07",
        "finish_day": "31",
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


def test_do_post_viewer(mocker, raw_client, sess):
    vf = to_utc(ct_datetime(2022, 7, 1))
    user_role = UserRole.insert(sess, "viewer")
    user = User.insert(sess, "admin@example.com", "admin", user_role, None)
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "neut", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    sess.commit()

    MockThread = mocker.patch("chellow.reports.report_183.threading.Thread")

    data = {
        "start_year": "2022",
        "start_month": "07",
        "start_day": "01",
        "finish_year": "2022",
        "finish_month": "07",
        "finish_day": "31",
        "type": "used",
        "site_codes": "",
    }
    headers = {"Authorization": _basic_auth_str("admin@example.com", "admin")}
    response = raw_client.post("/reports/183", data=data, headers=headers)

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


def test_process_site(sess):
    f = BytesIO()
    zf = ZipFile(f, mode="w")
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = to_utc(ct_datetime(2022, 7, 1))
    finish_date = to_utc(ct_datetime(2022, 7, 31, 23, 30))
    typ = "used"
    _process_site(sess, zf, site, start_date, finish_date, typ)
    assert zf.namelist() == ["CI017_202207312330.csv"]


def test_none_content(mocker, sess):
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    sess.commit()

    f = BytesIO()
    mocker.patch("chellow.reports.report_183.open_file", return_value=f)

    site_codes = []
    typ = "used"
    start_date = to_utc(ct_datetime(2022, 7, 1))
    finish_date = to_utc(ct_datetime(2022, 7, 31, 23, 30))
    file_name = "output"
    none_content(site_codes, typ, start_date, finish_date, user_id, file_name)
