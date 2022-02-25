from io import StringIO

from utils import match


def test_do_get(client, mocker):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_batches.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_batches.chellow.dloads.make_names",
        return_value=("a", "b"),
    )
    mocker.patch("chellow.reports.report_batches.os.rename")
    response = client.get("/reports/batches")
    match(response, 303)
