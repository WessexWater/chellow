from io import StringIO

from utils import match

from chellow.models import User
from chellow.reports.report_batches import content


def test_do_get(client, mocker, sess):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_batches.open_file", return_value=mock_file)
    MockThread = mocker.patch("chellow.reports.report_batches.threading.Thread")
    user = User.get_by_email_address(sess, "admin@example.com")
    expected_args = (user.id,)
    response = client.get("/reports/batches")
    match(response, 303)
    MockThread.assert_called_with(target=content, args=expected_args)
