import chellow.dloads
from chellow.models import User, UserRole
from chellow.reports.report_csv_site_snags import content


def test_content(sess):
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    sess.commit()

    content(user_id)

    files = list(p.name for p in chellow.dloads.download_path.iterdir())
    assert files == ["00000_FINISHED_admin_example_com_site_snags.csv"]
