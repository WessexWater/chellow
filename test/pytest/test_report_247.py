from chellow.utils import utc_datetime
import chellow.reports.report_247


def test_make_site_deltas(mocker):
    era_1 = mocker.Mock()
    era_1.start_date = utc_datetime(2018, 1, 1)
    era_1.finish_date = None
    filter_returns = iter([[era_1], []])

    class Sess():
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def filter(self, *args):
            return next(filter_returns)

    sess = Sess()
    report_context = {}
    site = mocker.Mock()
    site.code = '1'
    scenario_hh = {
        site.code: {
            'used': '2019-03-01 00:00, 0'
        }
    }
    forecast_from = utc_datetime(2019, 4, 1)
    supply_id = None

    ss = mocker.patch('chellow.computer.SiteSource', autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            'start-date': utc_datetime(2019, 3, 1),
            'used-kwh': 0,
            'export-net-kwh': 0,
            'import-net-kwh': 0,
            'msp-kwh': 0
        }
    ]

    se = mocker.patch('chellow.reports.report_247.SiteEra', autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch(
        'chellow.reports.report_247.SupplySource', autospec=True)
    sup_s_instance = sup_s.return_value
    sup_s_instance.hh_data = {}

    res = chellow.reports.report_247._make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id)

    assert len(res['supply_deltas'][False]['net']['site']) == 0
