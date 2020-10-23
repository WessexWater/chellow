from datetime import datetime as Datetime
from io import BytesIO

import chellow.views
from chellow.models import Contract
from chellow.utils import utc_datetime

from flask import g

from utils import (
    insert_bill_types, insert_g_batch, insert_g_bill, insert_g_contract,
    insert_g_dn, insert_g_era, insert_g_exit_zone, insert_g_ldz,
    insert_g_read_types, insert_g_reading_frequencies, insert_g_supply,
    insert_g_units, match,
)

from werkzeug.exceptions import BadRequest


def test_dtc_meter_types(client):
    response = client.get('/dtc_meter_types')

    match(response, 200)


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
    match(response, 200, *patterns)


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

    match(response, 303, r'/supplier_rate_scripts/3')

    contract = Contract.get_supplier_by_id(sess, 2)

    start_rate_script = contract.start_rate_script
    finish_rate_script = contract.finish_rate_script

    assert start_rate_script.start_date == utc_datetime(2000, 1, 3)
    assert finish_rate_script.finish_date is None


def test_g_bill_get(client, sess):
    g_dn_id = insert_g_dn(sess)
    g_ldz_id = insert_g_ldz(sess, g_dn_id=g_dn_id)
    g_exit_zone_id = insert_g_exit_zone(sess, g_ldz_id)
    g_supply_id = insert_g_supply(sess, g_exit_zone_id=g_exit_zone_id)
    g_contract_id = insert_g_contract(sess)
    g_batch_id = insert_g_batch(sess, g_contract_id=g_contract_id)

    breakdown = {
        'units_consumed': 771
    }
    g_bill_id = insert_g_bill(
        sess, g_batch_id=g_batch_id, g_supply_id=g_supply_id,
        breakdown=breakdown)

    sess.commit()

    response = client.get(f'/g_bills/{g_bill_id}')

    regexes = [
        r'<tr>\s*'
        r'<td>units</td>\s*'
        r'<td>771</td>'
    ]

    match(response, 200, *regexes)


def test_g_bill_imports_post_full(mocker, app, client, sess):
    file_lines = (
        "STX=ANA:1+Marsh Gas:MARSH Gas Limited+BPAJA:Bill Paja 771+"
        "171023:867369+856123++UTLHDR'",
        "MHD=1+UTLHDR:3'",
        "TYP=0715'",
        "SDT=Marsh Gas+Marsh Gas Limited++818671845'",
        "CDT=BPAJA:BPAJA+Bill Paja Limited - BPAJA++1'",
        "FIL=1+1+171023'",
        "MTR=6'",
        "MHD=2+UTLBIL:3'",
        "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
        "BCD=171022+171022+7868273476++M+N++170601:170630'",
        "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
        "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
        "170601+170701'",
        "ADJ=1+1+CV:3930000'",
        "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++"
        "008521+8746000+170601+170631+008727+091'",
        "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+"
        "8746000+170601+170630+815510+9931'",
        "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+"
        "30000+170601+170630+86221004+9224'",
        "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+"
        "30000+170601+170630+8582284+941'",
        "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+"
        "30000+170601+170630+8993000+841'",
        "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++"
        "005337+4617800+170601+170630+006120+882'",
        "VAT=1+++L+7986+23885+331+86334'",
        "BTL=000+88772+332++77345'",
        "MTR=14'",
        "MHD=2+UTLBIL:3'",
        "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
        "BCD=171022+171022+7868273476++M+N++170601:170630'",
        "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
        "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
        "170601+170701'",
        "ADJ=1+1+CV:3930000'",
        "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++"
        "008521+8746000+170601+170631+008727+091'",
        "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+"
        "8746000+170601+170630+815510'",
        "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+"
        "30000+170601+170630+86221004+9224'",
        "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+"
        "30000+170601+170630+8582284+941'",
        "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+"
        "30000+170601+170630+8993000+841'",
        "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++005337+"
        "4617800+170601+170630+006120+882'",
        "VAT=1+++L+7986+23885+331+86334'",
        "BTL=000+88772+332++77345'",
        "MTR=14'",
        "END=288'",
    )

    g_dn_id = insert_g_dn(sess)
    g_ldz_id = insert_g_ldz(sess, g_dn_id=g_dn_id)
    g_exit_zone_id = insert_g_exit_zone(sess, g_ldz_id)
    g_contract_id = insert_g_contract(sess)
    g_batch_id = insert_g_batch(sess, g_contract_id=g_contract_id)
    insert_bill_types(sess)
    g_supply_id = insert_g_supply(
        sess, mprn='87614362', g_exit_zone_id=g_exit_zone_id)
    insert_g_units(sess)
    insert_g_reading_frequencies(sess)
    insert_g_read_types(sess)
    insert_g_era(sess, g_supply_id=g_supply_id, g_contract_id=g_contract_id)
    sess.commit()

    file_name = 'gas.engie.edi'
    file_bytes = '\n'.join(file_lines).encode('utf8')
    f = BytesIO(file_bytes)

    data = {
        'g_batch_id': str(g_batch_id),
        'import_file': (f, file_name)
    }

    response = client.post('/g_bill_imports', data=data)

    match(response, 303, '/g_bill_imports/0')

    response = client.get('/g_bill_imports/0')

    match(response, 200, r"successfully")

    res = sess.execute("select breakdown from g_bill where id = 2")
    assert '"units_consumed": 771,' in next(res)[0]


def test_g_bill_imports_post(mocker, app, client, sess):
    g_contract_id = insert_g_contract(sess)
    g_batch_id = insert_g_batch(sess, g_contract_id=g_contract_id)
    sess.commit()

    file_name = 'gas.engie.edi'
    file_bytes = b"edifile'"
    f = BytesIO(file_bytes)

    data = {
        'g_batch_id': str(g_batch_id),
        'import_file': (f, file_name)
    }

    import_id = 3

    mock_start_importer = mocker.patch(
        "chellow.views.chellow.g_bill_import.start_bill_importer",
        return_value=import_id)

    response = client.post('/g_bill_imports', data=data)
    mock_start_importer.assert_called_with(
        g.sess, g_batch_id, file_name, file_bytes)

    match(response, 303, '/g_bill_imports/3')
