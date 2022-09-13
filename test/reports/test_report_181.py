import chellow.e.computer
import chellow.reports.report_181
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_write_sites(mocker):
    sess = mocker.Mock()
    caches = {}
    writer = mocker.Mock()
    year = 2010
    year_start = to_utc(ct_datetime(year - 1, 4, 1))
    year_finish = to_utc(ct_datetime(year, 3, 31, 23, 30))
    month_start = to_utc(utc_datetime(year, 3, 1))

    site_id = None
    site = mocker.Mock()
    era = mocker.Mock()
    source_codes = ("gen", "gen-net")

    ms = mocker.patch("chellow.reports.report_181._make_sites", autospec=True)
    ms.return_value = [site]
    de = mocker.patch("chellow.e.computer.displaced_era", autospec=True)
    de.return_value = era
    ss = mocker.patch("chellow.e.computer.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": month_start,
            "triad-actual-1-date": utc_datetime(year, 1, 12),
            "triad-actual-1-msp-kw": 12,
            "triad-actual-1-laf": 1,
            "triad-actual-1-gsp-kw": 12,
            "triad-actual-2-date": utc_datetime(year, 1, 12),
            "triad-actual-2-msp-kw": 12,
            "triad-actual-2-laf": 1,
            "triad-actual-2-gsp-kw": 12,
            "triad-actual-3-date": utc_datetime(year, 1, 12),
            "triad-actual-3-msp-kw": 12,
            "triad-actual-3-laf": 1,
            "triad-actual-3-gsp-kw": 12,
            "triad-actual-gsp-kw": 12,
            "triad-actual-rate": 10,
            "triad-actual-gbp": 120,
        }
    ]

    ss_instance.supplier_bill_hhs = {month_start: {}}

    mocker.patch("chellow.e.duos.duos_vb", autospec=True)
    mocker.patch("chellow.e.tnuos.hh", autospec=True)

    forecast_date = chellow.e.computer.forecast_date()

    chellow.reports.report_181._write_sites(sess, caches, writer, year, site_id)

    ms.assert_called_once_with(sess, year_start, year_finish, site_id, source_codes)
    de.assert_called_once_with(
        sess, caches, site, month_start, year_finish, forecast_date
    )
