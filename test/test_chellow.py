from chellow import create_app, get_importer_modules
from chellow.models import Pc, Session


def test_create_app(mocker, fresh_db):
    mock_startups = []
    for importer_module in get_importer_modules():
        mock_startup = importer_module.startup = mocker.Mock()
        mock_startups.append(mock_startup)

    mock_module = mocker.patch("chellow.chellow.dloads")
    mock_startup = mock_module.startup = mocker.Mock()
    mock_startups.append(mock_startup)

    create_app()

    for mock_startup in mock_startups:
        mock_startup.assert_called_once()

    sess = Session()
    Pc.get_by_code(sess, "00")
    sess.close()
