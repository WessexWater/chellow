import chellow.dloads
from chellow.models import (
    GContract,
    User,
    UserRole,
)
from chellow.reports.report_g_virtual_bills import content
from chellow.utils import ct_datetime, to_utc


def test_content(sess):
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    vf = to_utc(ct_datetime(2020, 1, 1))
    g_contract = GContract.insert(sess, False, "Fusion 2020", "", {}, vf, None, {})
    sess.commit()

    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))
    content(start_date, finish_date, g_contract.id, user_id)

    files = list(p.name for p in chellow.dloads.download_path.iterdir())
    assert files == ["00000_FINISHED_adminexamplecom_gas_virtual_bills.csv"]
