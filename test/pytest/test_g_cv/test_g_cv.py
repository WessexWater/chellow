import chellow.g_cv
from chellow.models import Contract, MarketRole, Participant
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_fetch_cvs(mocker, sess):
    market_role_Z = MarketRole.insert(sess, 'Z', 'Non-core')
    participant = Participant.insert(sess, 'CALB', 'AK Industries')
    participant.insert_party(
        sess, market_role_Z, 'None core', utc_datetime(2000, 1, 1), None,
        None)
    properties = {
        'enabled': True,
        'url': 'https://example.com',
    }
    Contract.insert_non_core(
        sess, 'g_cv', '', properties, to_utc(ct_datetime(2014, 6, 1)), None,
        {})
    sess.commit()

    mock_response = mocker.Mock()
    with open('test/pytest/test_g_cv/cv.csv') as f:
        mock_response.text = f.read()

    mock_requests = mocker.patch('chellow.g_cv.requests')
    mock_requests.post = mocker.Mock(return_value=mock_response)

    messages = []

    def log_f(msg):
        messages.append(msg)

    chellow.g_cv.fetch_cvs(sess, log_f)

    assert messages[-1] == 'Added new rate script.'
