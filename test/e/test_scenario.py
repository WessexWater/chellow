from chellow.scenario import make_site_deltas
from chellow.utils import utc_datetime


def test_make_site_deltas(mocker):
    era_1 = mocker.Mock()
    era_1.start_date = utc_datetime(2018, 1, 1)
    era_1.finish_date = None
    filter_returns = iter([[era_1], []])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def filter(self, *args):
            return next(filter_returns)

    sess = Sess()
    report_context = {}
    site = mocker.Mock()
    site.code = "1"
    scenario_hh = {site.code: {"used": "2019-03-01 00:00, 0"}}
    forecast_from = utc_datetime(2019, 4, 1)
    supply_id = None

    ss = mocker.patch("chellow.scenario.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-net-kwh": 0,
            "import-net-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.scenario.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.scenario.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    sup_s_instance.hh_data = {}

    res = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert len(res["supply_deltas"][False]["net"]["site"]) == 0


def test_make_site_deltas_nhh(mocker):
    era_1 = mocker.Mock()
    era_1.start_date = utc_datetime(2018, 1, 1)
    era_1.finish_date = None
    """
    filter_args = iter(
        [
            [
                'False',
                'era.finish_date IS NULL OR era.finish_date >= :finish_date_1',
                'era.imp_mpan_core IS NOT NULL',
                'era.start_date <= :start_date_1', 'pc.code != :code_1',
                'true = :param_1'
            ],
            [
                'False',
                'era.finish_date IS NULL OR era.finish_date >= :finish_date_1',
                'era.imp_mpan_core IS NOT NULL',
                'era.start_date <= :start_date_1', 'source.code = :code_1',
                'true = :param_1'
            ]
        ]
    )
    """

    filter_returns = iter([[era_1], []])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def filter(self, *args):
            """
            actual_args = sorted(map(str, args))
            expected_args = next(filter_args)
            assert actual_args == expected_args
            """
            return next(filter_returns)

    sess = Sess()
    report_context = {}
    site = mocker.Mock()
    site.code = "1"
    scenario_hh = {site.code: {"used": "2019-03-01 00:00, 0"}}
    forecast_from = utc_datetime(2019, 4, 1)
    supply_id = None

    ss = mocker.patch("chellow.scenario.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-net-kwh": 0,
            "import-net-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.scenario.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.scenario.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    hh_start_date = utc_datetime(2019, 3, 1)
    sup_s_instance.hh_data = [{"start-date": hh_start_date, "msp-kwh": 10}]

    res = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert res["supply_deltas"][True]["net"]["site"] == {hh_start_date: -10.0}
