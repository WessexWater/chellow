from chellow.utils import utc_datetime
import chellow.reports.report_181
import chellow.computer


def test_write_sites(mocker):
    sess = mocker.Mock()
    caches = {}
    writer = mocker.Mock()
    year = 2010
    year_start = utc_datetime(year - 1, 4, 1)
    year_finish = utc_datetime(year, 3, 31, 23, 30)
    month_start = utc_datetime(year, 3, 1)

    site_id = None
    site = mocker.Mock()
    era = mocker.Mock()
    source_codes = ('gen', 'gen-net')

    ms = mocker.patch('chellow.reports.report_181._make_sites', autospec=True)
    ms.return_value = [site]
    de = mocker.patch('chellow.computer.displaced_era', autospec=True)
    de.return_value = era
    ss = mocker.patch('chellow.computer.SiteSource', autospec=True)
    ss_instance = ss.return_value
    ss_instance.supplier_bill = {
        'triad-actual-1-date': utc_datetime(year, 1, 12),
        'triad-actual-1-msp-kw': 12,
        'triad-actual-1-laf': 1,
        'triad-actual-1-gsp-kw': 12,
        'triad-actual-2-date': utc_datetime(year, 1, 12),
        'triad-actual-2-msp-kw': 12,
        'triad-actual-2-laf': 1,
        'triad-actual-2-gsp-kw': 12,
        'triad-actual-3-date': utc_datetime(year, 1, 12),
        'triad-actual-3-msp-kw': 12,
        'triad-actual-3-laf': 1,
        'triad-actual-3-gsp-kw': 12,
        'triad-actual-gsp-kw': 12,
        'triad-actual-rate': 10,
        'triad-actual-gbp': 120
    }
    ss_instance.supplier_rate_sets = {}

    mocker.patch('chellow.duos.duos_vb', autospec=True)
    mocker.patch('chellow.triad.hh', autospec=True)
    mocker.patch('chellow.triad.bill', autospec=True)

    forecast_date = chellow.computer.forecast_date()

    chellow.reports.report_181._write_sites(
        sess, caches, writer, year, site_id)

    ms.assert_called_once_with(
        sess, year_start, year_finish, site_id, source_codes)
    de.assert_called_once_with(
        sess, caches, site, month_start, year_finish, forecast_date)
