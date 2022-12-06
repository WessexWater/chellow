import pytest

from chellow.e.bsuos import _find_file_type, _process_url


@pytest.mark.parametrize(
    "filename,ext",
    [
        ['filename="bsuos.csv"', "csv"],
        ['inline; filename="Current_RF_BSUoS_Data_175.xls"', "xls"],
        ["inline; filename=Current_RF_BSUoS_Data_175.xls", "xls"],
    ],
)
def test_find_file_type_csv(filename, ext):
    assert _find_file_type(filename) == ext


def test_process_url_csv(mocker, sess):
    res = mocker.Mock()
    res.text = "Date"
    res.status_code = 200
    res.reason = "okay"
    res.headers = {"Content-Disposition": 'filename="bsuos.csv"'}
    mocker.patch("chellow.e.bsuos.requests.get", return_value=res)
    logger = mocker.Mock()
    contract = mocker.Mock()
    url = mocker.Mock()
    _process_url(logger, sess, url, contract)
