from datetime import datetime as Datetime

import chellow.views
from chellow.models import Contract
from chellow.utils import utc_datetime

from utils import match

from werkzeug.exceptions import BadRequest


def test_dtc_meter_types(client):
    response = client.get('/dtc_meter_types')

    match(response, 200, [])


def test_supply_edit_post(mocker):
    """ When inserting an era that fails, make sure rollback is called.
    """
    supply_id = 1
    g = mocker.patch("chellow.views.g", autospec=True)
    g.sess = mocker.Mock()
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
    mock_bill.finish_date = dt

    MockRegisterRead = mocker.patch(
        'chellow.views.RegisterRead', autospec=True)
    MockRegisterRead.bill = mocker.Mock()
    MockRegisterRead.present_date = dt

    mocker.patch('chellow.views.render_template', autospec=True)

    chellow.views.read_add_get(bill_id)


def test_view_supplier_contract(client, sess):
    sess.execute(
        "INSERT INTO market_role (code, description) "
        "VALUES ('X', 'Supplier')")
    sess.execute(
        "INSERT INTO participant (code, name) "
        "VALUES ('FUSE', 'Fusion')")
    sess.execute(
        "INSERT INTO party (market_role_id, participant_id, name, "
        "valid_from, valid_to, dno_code) "
        "VALUES (2, 2, 'Fusion Energy', '2000-01-01', null, null)")
    sess.execute(
        "INSERT INTO contract (name, charge_script, properties, "
        "state, market_role_id, party_id, start_rate_script_id, "
        "finish_rate_script_id) VALUES ('2020 Fusion', '{}', '{}', '{}', "
        "2, 2, null, null)")
    sess.execute(
        "INSERT INTO rate_script (contract_id, start_date, finish_date, "
        "script) VALUES (2, '2000-01-03', null, '{}')")
    sess.execute(
        "UPDATE contract set start_rate_script_id = 2, "
        "finish_rate_script_id = 2 where id = 2;")
    sess.commit()

    response = client.get('/supplier_contracts/2')

    patterns = [
        r'<tr>\s*'
        r'<th>Start Date</th>\s*'
        r'<td>2000-01-03 00:00</td>\s*'
        r'</tr>\s*'
        r'<tr>\s*'
        r'<th>Finish Date</th>\s*'
        r'<td>Ongoing</td>\s*'
        r'</tr>\s*'
    ]
    match(response, 200, patterns)


def test_supplier_contract_add_rate_script(client, sess):
    sess.execute(
        "INSERT INTO market_role (code, description) "
        "VALUES ('X', 'Supplier')")
    sess.execute(
        "INSERT INTO participant (code, name) "
        "VALUES ('FUSE', 'Fusion')")
    sess.execute(
        "INSERT INTO party (market_role_id, participant_id, name, "
        "valid_from, valid_to, dno_code) "
        "VALUES (2, 2, 'Fusion Energy', '2000-01-01', null, null)")
    sess.execute(
        "INSERT INTO contract (name, charge_script, properties, "
        "state, market_role_id, party_id, start_rate_script_id, "
        "finish_rate_script_id) VALUES ('2020 Fusion', '{}', '{}', '{}', "
        "2, 2, null, null)")
    sess.execute(
        "INSERT INTO rate_script (contract_id, start_date, finish_date, "
        "script) VALUES (2, '2000-01-03', null, '{}')")
    sess.execute(
        "UPDATE contract set start_rate_script_id = 2, "
        "finish_rate_script_id = 2 where id = 2;")
    sess.commit()

    data = {
        'start_year': "2020",
        'start_month': "02",
        'start_day': "06",
        'start_hour': "01",
        'start_minute': "00",
        'script': "{}"
    }
    response = client.post('/supplier_contracts/2/add_rate_script', data=data)

    match(response, 303, [r'/supplier_rate_scripts/3'])

    contract = Contract.get_supplier_by_id(sess, 2)

    start_rate_script = contract.start_rate_script
    finish_rate_script = contract.finish_rate_script

    assert start_rate_script.start_date == utc_datetime(2000, 1, 3)
    assert finish_rate_script.finish_date is None
