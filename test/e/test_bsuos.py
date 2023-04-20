from chellow.e.bsuos import _process_url


def test_process_url_csv(mocker, sess):
    res = mocker.Mock()
    res.text = "Date"
    res.status_code = 200
    res.reason = "okay"
    logger = mocker.Mock()
    contract = mocker.Mock()
    url = mocker.Mock()
    s = mocker.Mock()
    s.get = mocker.Mock(return_value=res)
    _process_url(logger, sess, url, contract, s)
