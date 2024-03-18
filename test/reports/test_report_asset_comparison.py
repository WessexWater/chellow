import csv
from io import StringIO

import chellow.dloads
from chellow.models import (
    Contract,
    MarketRole,
    Participant,
    ReportRun,
    Site,
    User,
    UserRole,
)
from chellow.reports.report_asset_comparison import _process_sites, content
from chellow.utils import ct_datetime, to_utc


def test_content(sess):
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    report_run = ReportRun.insert(sess, "asset", None, "asset", {})
    vf = to_utc(ct_datetime(2020, 1, 1))
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    Contract.insert_non_core(
        sess,
        "configuration",
        "",
        {"asset_comparison": {"ignore_site_codes": []}},
        vf,
        None,
        {},
    )
    sess.commit()

    asset_str = "\n".join(("code,,,status",))
    file_like = StringIO(asset_str)
    report_run_id = report_run.id
    content(user_id, file_like, report_run_id)

    files = list(p.name for p in chellow.dloads.download_path.iterdir())
    assert files == ["00000_FINISHED_adminexamplecom_asset_comparison.csv"]


def test_process_sites(sess):
    site_code = "109"
    Site.insert(sess, site_code, "A Site")
    report_run = ReportRun.insert(sess, "asset", None, "asset", {})
    sess.commit()

    asset_str = "\n".join(("code,,,status",))
    file_like = StringIO(asset_str)
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    props = {"asset_comparison": {"ignore_site_codes": []}}

    _process_sites(sess, file_like, writer, props, report_run.id)

    assert output.getvalue() == "site_code,asset_status,chellow_status\n"
