from chellow.models import Contract, MarketRole, Participant
from chellow.rate_server import run_import
from chellow.utils import ct_datetime, to_utc


def test_run_import(mocker, sess):
    vf = to_utc(ct_datetime(1996, 4, 1))
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    sess.commit()
    messages = []

    mocker.patch("chellow.e.bsuos.rate_server_import")
    mocker.patch("chellow.e.dno_rate_parser.rate_server_import")
    mocker.patch("chellow.e.lafs.rate_server_import")
    mocker.patch("chellow.e.mdd_importer.rate_server_import")
    mocker.patch("chellow.e.tlms.rate_server_import")
    mocker.patch("chellow.gas.dn_rate_parser.rate_server_import")

    def mock_api_get(s, url, params=None):
        responses = {
            "https://api.github.com/repos/WessexWater/chellow-rates": {
                "html_url": "https://example.com"
            },
            "https://api.github.com/repos/WessexWater/chellow-rates/branches/main": {
                "commit": {"commit": {"tree": {"url": "https://example.com/tree"}}}
            },
            "https://example.com/tree": {"tree": [], "truncated": False},
        }
        return responses[url]

    mocker.patch("chellow.rate_server.api_get", mock_api_get)

    def log(message):
        messages.append(message)

    def set_progress(progress):
        pass

    run_import(sess, log, set_progress)


def test_run_import_lowercase_readme(mocker, sess):
    vf = to_utc(ct_datetime(1996, 4, 1))
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    sess.commit()
    messages = []

    mocker.patch("chellow.e.bsuos.rate_server_import")
    mocker.patch("chellow.e.dno_rate_parser.rate_server_import")
    mocker.patch("chellow.e.lafs.rate_server_import")
    mocker.patch("chellow.e.mdd_importer.rate_server_import")
    mocker.patch("chellow.e.tlms.rate_server_import")
    mocker.patch("chellow.gas.dn_rate_parser.rate_server_import")

    def mock_api_get(s, url, params=None):
        responses = {
            "https://api.github.com/repos/WessexWater/chellow-rates": {
                "html_url": "https://example.com"
            },
            "https://api.github.com/repos/WessexWater/chellow-rates/branches/main": {
                "commit": {"commit": {"tree": {"url": "https://example.com/tree"}}}
            },
            "https://example.com/tree": {
                "tree": [{"path": "readme.md"}],
                "truncated": False,
            },
        }
        return responses[url]

    mocker.patch("chellow.rate_server.api_get", mock_api_get)

    def log(message):
        messages.append(message)

    def set_progress(progress):
        pass

    run_import(sess, log, set_progress)
