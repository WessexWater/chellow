import chellow.gas.cv
from chellow.models import GContract
from chellow.utils import ct_datetime, to_utc


def test_fetch_cvs(mocker, sess):
    properties = {
        "enabled": True,
        "url": "https://example.com",
    }
    GContract.insert(
        sess, True, "cv", "", properties, to_utc(ct_datetime(2014, 6, 1)), None, {}
    )
    sess.commit()

    mock_response = mocker.Mock()
    with open("test/gas/test_cv.py/cv.csv") as f:
        mock_response.text = f.read()

    mock_requests = mocker.patch("chellow.gas.cv.requests")
    mock_requests.post = mocker.Mock(return_value=mock_response)

    messages = []

    def log_f(msg):
        messages.append(msg)

    chellow.gas.cv.fetch_cvs(sess, log_f)

    assert messages[-1] == "Added new rate script."
