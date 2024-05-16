from io import StringIO

from chellow.models import Contract, MarketRole, Participant, User, UserRole

from chellow.reports.report_233 import content
from chellow.utils import ct_datetime, to_utc


def test_content(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()
    f = StringIO()
    mocker.patch("chellow.reports.report_233.open_file", return_value=f)
    days_hidden = 0
    is_ignored = True
    content(dc_contract.id, days_hidden, is_ignored, user_id)
