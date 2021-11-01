from chellow.bsuos import _find_file_type, _process_url


def test_find_file_type_csv():
    filetype = "csv"
    assert _find_file_type(f'filename="bsuos.{filetype}"') == filetype


def test_find_file_type_xsl():
    expected = "xls"
    actual = _find_file_type(f'inline; filename="Current_RF_BSUoS_Data_175.{expected}"')
    assert actual == expected


def test_process_url_csv(mocker, sess):
    res = mocker.Mock()
    res.text = "Date"
    res.status_code = 200
    res.reason = "okay"
    res.headers = {"Content-Disposition": 'filename="bsuos.csv"'}
    mocker.patch("chellow.bsuos.requests.get", return_value=res)
    logger = mocker.Mock()
    contract = mocker.Mock()
    url = mocker.Mock()
    _process_url(logger, sess, url, contract)
