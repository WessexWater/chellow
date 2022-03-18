from io import StringIO

from chellow.models import (
    Site,
)
from chellow.reports.report_59 import _process, content
from chellow.utils import ct_datetime, to_utc


def test_process(mocker, sess):
    Site.insert(sess, "CI017", "Water Works")
    sess.commit()
    f = StringIO()
    start_date = to_utc(ct_datetime(2010, 1, 1))
    finish_date = to_utc(ct_datetime(2010, 1, 31, 23, 20))
    site_id = None
    site_codes = None
    _process(sess, f, start_date, finish_date, site_id, site_codes)
    actual_str = f.getvalue()
    expected = [
        [
            "site_code",
            "site_name",
            "associated_site_ids",
            "sources",
            "generator_types",
            "from",
            "to",
            "imp_net_sum_kwh",
            "imp_net_max_kw",
            "imp_net_avg_kw",
            "displaced_sum_kwh",
            "displaced_max_kw",
            "displaced_avg_kw",
            "exp_net_sum_kwh",
            "exp_net_max_kw",
            "exp_net_avg_kw",
            "used_sum_kwh",
            "used_max_kw",
            "used_avg_kw",
            "exp_gen_sum_kwh",
            "exp_gen_max_kw",
            "exp_gen_avg_kw",
            "imp_gen_sum_kwh",
            "imp_gen_max_kw",
            "imp_gen_avg_kw",
            "metering_type",
        ],
        [
            "CI017",
            "Water Works",
            "",
            "",
            "",
            "2010-01-01 00:00",
            "2010-01-31 23:20",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "",
        ],
    ]
    expected_str = "\n".join(",".join(line) for line in expected) + "\n"
    assert actual_str == expected_str


def test_process_site_codes(mocker, sess):
    site_code = "CI017"
    Site.insert(sess, site_code, "Water Works")
    sess.commit()
    f = StringIO()
    start_date = to_utc(ct_datetime(2010, 1, 1))
    finish_date = to_utc(ct_datetime(2010, 1, 31, 23, 20))
    site_id = None
    site_codes = [site_code]
    _process(sess, f, start_date, finish_date, site_id, site_codes)
    actual_str = f.getvalue()
    expected = [
        [
            "site_code",
            "site_name",
            "associated_site_ids",
            "sources",
            "generator_types",
            "from",
            "to",
            "imp_net_sum_kwh",
            "imp_net_max_kw",
            "imp_net_avg_kw",
            "displaced_sum_kwh",
            "displaced_max_kw",
            "displaced_avg_kw",
            "exp_net_sum_kwh",
            "exp_net_max_kw",
            "exp_net_avg_kw",
            "used_sum_kwh",
            "used_max_kw",
            "used_avg_kw",
            "exp_gen_sum_kwh",
            "exp_gen_max_kw",
            "exp_gen_avg_kw",
            "imp_gen_sum_kwh",
            "imp_gen_max_kw",
            "imp_gen_avg_kw",
            "metering_type",
        ],
        [
            "CI017",
            "Water Works",
            "",
            "",
            "",
            "2010-01-01 00:00",
            "2010-01-31 23:20",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "0",
            "0",
            "0.0",
            "",
        ],
    ]
    expected_str = "\n".join(",".join(line) for line in expected) + "\n"
    assert actual_str == expected_str


def test_content(mocker, sess):
    f = StringIO()
    mocker.patch("chellow.reports.report_59.open", return_value=f)
    mocker.patch("chellow.reports.report_59.os.rename")
    start_date = to_utc(ct_datetime(2010, 1, 1))
    finish_date = to_utc(ct_datetime(2010, 1, 31, 23, 30))
    site_id = None
    user = None
    site_codes = None
    content(start_date, finish_date, site_id, user, site_codes)
