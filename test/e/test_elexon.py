from chellow.e.elexon import run_import
from chellow.models import MarketRole, Participant
from chellow.utils import ct_datetime, to_utc


def test_elexon_import(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    sess.commit()
    mocker.patch("chellow.e.system_price.elexon_import", autospec=True)
    mocker.patch("chellow.e.tlms.elexon_import", autospec=True)
    mocker.patch("chellow.e.rcrc.elexon_import", autospec=True)
    mocker.patch("chellow.e.lafs.elexon_import", autospec=True)

    log = mocker.Mock()
    set_progress = mocker.Mock()
    scripting_key = mocker.Mock()

    run_import(sess, log, set_progress, scripting_key)
