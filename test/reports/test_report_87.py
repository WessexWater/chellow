from io import StringIO

import chellow.e.computer
import chellow.reports.report_87
from chellow.utils import ct_datetime, to_utc


class Sess:
    def __init__(self, *results):
        self.it = iter(results)

    def query(self, *arg):
        return self

    def join(self, *arg):
        return self

    def order_by(self, *arg):
        return self

    def filter(self, *arg):
        return self

    def scalar(self, *arg):
        return next(self.it)

    def first(self, *arg):
        return next(self.it)

    def distinct(self, *arg):
        return next(self.it)


def test_summertime(mocker):
    start_date_ct = ct_datetime(2010, 5)
    finish_date_ct = ct_datetime(2010, 5, 31, 23, 30)
    start_date = to_utc(start_date_ct)
    finish_date = to_utc(finish_date_ct)
    contract_id = 1
    user = mocker.Mock()
    user.email_address = "sfreud"

    mock_c_months_u = mocker.patch(
        "chellow.reports.report_87.c_months_u", autospec=True
    )

    MockEra = mocker.patch("chellow.reports.report_87.Era", autospec=True)
    MockEra.finish_date = finish_date
    MockEra.start_date = start_date

    mocker.patch(
        "chellow.reports.report_87.contract_func",
        autospec=True,
        return_value=lambda: ["standing_gbp"],
    )

    f = StringIO()
    sess = Sess([], [])

    chellow.reports.report_87.create_csv(f, sess, start_date, finish_date, contract_id)

    mock_c_months_u.assert_called_with(
        start_year=start_date_ct.year,
        start_month=start_date_ct.month,
        finish_year=finish_date_ct.year,
        finish_month=finish_date_ct.month,
    )
