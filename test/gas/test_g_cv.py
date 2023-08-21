import chellow.gas.cv
from chellow.models import GContract
from chellow.utils import ct_datetime, to_utc


def test_fetch_cvs(mocker, sess):
    properties = {
        "enabled": True,
    }
    g_contract = GContract.insert(
        sess, True, "cv", "", properties, to_utc(ct_datetime(2014, 6, 1)), None, {}
    )
    sess.commit()

    mock_response = mocker.Mock()
    mock_response.text = (
        "Applicable At,Applicable For,Data Item,Value,Generated Time,Quality Indicator"
    )
    mock_response.text += """
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(SC)",39.3,21/02/2018 10:32:01,
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(SE)",39,21/02/2018 10:32:01,
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(SO)",39,21/02/2018 10:32:01,
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(SW)",39.1,21/02/2018 10:32:01,
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(WM)",39.4,21/02/2018 10:32:01,
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(WN)",39.5,21/02/2018 10:32:01,
30/07/2014 10:30:23,30/07/2014,"Calorific Value, LDZ(WS)",39.2,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(SC)",39.3,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(SE)",39,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(SO)",39,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(SW)",39.1,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(WM)",39.4,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(WN)",39.5,21/02/2018 10:32:01,
31/07/2014 10:30:23,31/07/2014,"Calorific Value, LDZ(WS)",39.2,21/02/2018 10:32:01,
"""

    mock_requests = mocker.patch("chellow.gas.cv.requests")
    mock_s = mocker.Mock()
    mock_requests.Session = mocker.Mock(return_value=mock_s)
    mock_s.get = mocker.Mock(return_value=mock_response)

    messages = []

    def log_f(msg):
        messages.append(msg)

    chellow.gas.cv.fetch_cvs(sess, log_f, g_contract)

    assert messages[-1] == (
        "Added applicable_for: 31/07/2014, applicable_at: 31/07/2014 10:30:23, "
        "value: 39.2"
    )
