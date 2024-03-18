import chellow.dloads
from chellow.models import Contract, MarketRole, Participant, ReportRun, User, UserRole
from chellow.reports.report_supply_contacts import content
from chellow.utils import ct_datetime, to_utc


def test_content(sess):
    vf = to_utc(ct_datetime(2020, 1, 1))
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    report_run = ReportRun.insert(sess, "asset", None, "asset", {})
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    Contract.insert_non_core(
        sess, "configuration", "", {"dno_contacts": {}}, vf, None, {}
    )
    sess.commit()

    content(user_id, report_run.id)

    files = list(p.name for p in chellow.dloads.download_path.iterdir())
    assert files == ["00000_FINISHED_adminexamplecom_supply_contacts.csv"]
