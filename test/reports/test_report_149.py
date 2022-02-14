from chellow.reports.report_149 import content
from chellow.utils import ct_datetime, to_utc


def test_with_scenario(mocker, client):
    supply_id = None
    start_date = to_utc(ct_datetime(2022, 1, 1))
    finish_date = to_utc(ct_datetime(2022, 1, 31, 23, 30))
    user = None
    content(supply_id, start_date, finish_date, user)
