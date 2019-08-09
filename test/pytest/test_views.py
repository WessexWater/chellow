import chellow.views
from werkzeug.exceptions import BadRequest
from sqlalchemy.orm.session import Session
from chellow.utils import utc_datetime
from datetime import datetime as Datetime


def test_supply_edit_post(mocker):
    """ When inserting an era that fails, make sure rollback is called.
    """
    supply_id = 1
    g = mocker.patch("chellow.views.g", autospec=True)
    g.sess = mocker.Mock(spec=Session)
    supply_class = mocker.patch("chellow.views.Supply", autospec=True)

    request = mocker.patch("chellow.views.request", autospec=True)
    request.form = {'insert_era': 0}

    req_date = mocker.patch("chellow.views.req_date", autospec=True)
    req_date.return_value = utc_datetime(2019, 1, 1)

    mocker.patch("chellow.views.flash", autospec=True)
    era_class = mocker.patch("chellow.views.Era", autospec=True)
    era_class.supply = mocker.Mock()

    mocker.patch("chellow.views.make_response", autospec=True)
    mocker.patch("chellow.views.render_template", autospec=True)

    supply = mocker.Mock()
    supply.insert_era_at.side_effect = BadRequest()

    supply_class.get_by_id.return_value = supply

    chellow.views.supply_edit_post(supply_id)
    g.sess.rollback.assert_called_once_with()


class Sess():
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


def test_read_add_get(mocker):
    bill_id = 1

    class MockDatetime(Datetime):
        def __new__(cls, y, m, d):
            return Datetime.__new__(cls, y, m, d)

    dt = MockDatetime(2019, 1, 1)
    dt.desc = mocker.Mock()

    g = mocker.patch("chellow.views.g", autospec=True)
    g.sess = Sess(None, None)

    MockBill = mocker.patch('chellow.views.Bill', autospec=True)
    MockBill.supply = mocker.Mock()
    MockBill.start_date = dt

    mock_bill = mocker.Mock()
    MockBill.get_by_id.return_value = mock_bill
    mock_bill.supply.find_era_at.return_value = None
    mock_bill.start_date = dt

    MockRegisterRead = mocker.patch(
        'chellow.views.RegisterRead', autospec=True)
    MockRegisterRead.bill = mocker.Mock()

    mocker.patch('chellow.views.render_template', autospec=True)

    chellow.views.read_add_get(bill_id)
