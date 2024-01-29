from chellow.e.system_price import elexon_import
from chellow.models import Contract, MarketRole, Participant
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_process(sess, mocker):
    from_date = to_utc(ct_datetime(2000, 1, 1))
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "non-core", from_date, None, None)
    system_price_properties = {
        "enabled": True,
    }
    rate_script_properties = {"gbp_per_nbp_mwh": {}}
    Contract.insert_non_core(
        sess,
        "system_price",
        "",
        system_price_properties,
        utc_datetime(2001, 4, 1),
        None,
        rate_script_properties,
    )
    Contract.insert_non_core(
        sess,
        "configuration",
        "",
        {"elexonportal_scripting_key": "xxx"},
        from_date,
        None,
        {},
    )
    sess.commit()

    log = []

    def log_f(msg):
        log.append(msg)

    mock_s = mocker.Mock()
    mock_response = mocker.Mock()
    mock_s.get.return_value = mock_response
    with open("test/e/system_price/prices.xls", "rb") as f:
        mock_response.content = f.read()
    mock_response.status_code = 200
    mock_response.reason = "OK"

    mock_set_progress = mocker.Mock()
    scripting_key = "xxx"
    elexon_import(sess, log_f, mock_set_progress, mock_s, scripting_key)

    assert log == [
        "Starting to check System Prices.",
        "Downloading from "
        "https://downloads.elexonportal.co.uk/file/download/BESTVIEWPRICES_FILE?"
        "key=xxx and extracting data from 2001-04-01 01:00",
        "Received 200 OK",
        "Successfully extracted data.",
        "Updating rate script starting at 2001-04-01 01:00.",
    ]
