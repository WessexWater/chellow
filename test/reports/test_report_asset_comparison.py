import csv
from io import StringIO

from chellow.models import Site
from chellow.reports.report_asset_comparison import _process_sites


def test_process_sites(sess):
    site_code = "109"
    Site.insert(sess, site_code, "A Site")
    sess.commit()

    asset_str = "\n".join(("code,,,status",))
    file_like = StringIO(asset_str)
    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")
    props = {"asset_comparison": {"ignore_site_codes": []}}

    _process_sites(sess, file_like, writer, props)

    assert output.getvalue() == "Site Code,Asset Status,Chellow Status,Problem\n"
