from io import StringIO
from utils import match

from chellow.models import User
from chellow.reports.report_169 import content
from chellow.utils import ct_datetime, to_utc


def test_handle_request(mocker, client, sess):
    user = User.get_by_email_address(sess, "admin@example.com")
    MockThread = mocker.patch("chellow.reports.report_169.threading.Thread")

    channel_type = "used"

    query_string = {
        "start_year": "2020",
        "start_month": "06",
        "start_day": "01",
        "finish_year": "2020",
        "finish_month": "06",
        "finish_day": "01",
        "channel_type": channel_type,
    }
    response = client.get("/reports/169", query_string=query_string)

    match(response, 303)

    expected_args = (
        to_utc(ct_datetime(2020, 6, 1)),
        to_utc(ct_datetime(2020, 6, 1, 23, 30)),
        False,
        channel_type,
        False,
        None,
        None,
        user.id,
    )

    MockThread.assert_called_with(target=content, args=expected_args)


def test_content(mocker, client, sess):
    user = User.get_by_email_address(sess, "admin@example.com")

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_169.open", return_value=mock_file)
    mock_make_names = mocker.patch(
        "chellow.reports.report_169.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_169.os.rename")
    start_date = to_utc(ct_datetime(2020, 6, 1))
    finish_date = to_utc(ct_datetime(2020, 6, 1, 23, 30))
    imp_related = True
    channel_type = "used"
    is_zipped = False
    supply_id = None
    mpan_cores = None
    user_id = user.id
    content(
        start_date,
        finish_date,
        imp_related,
        channel_type,
        is_zipped,
        supply_id,
        mpan_cores,
        user_id,
    )
    call_args = mock_make_names.call_args
    arg_name, arg_user = call_args[0]
    assert arg_name == "supplies_hh_data_202006012330.csv"
    assert arg_user.id == user.id

    expected = [
        "import_mpan_core",
        "export_mpan_core",
        "is_hh",
        "is_import_related",
        "channel_type",
        "hh_start_clock_time",
        "total",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
    ]
    assert mock_file.getvalue() == ",".join(expected) + "\n"
