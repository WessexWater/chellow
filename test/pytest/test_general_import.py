import chellow.general_import
import chellow.models
from decimal import Decimal
from chellow.utils import utc_datetime, hh_format


def test_general_import_g_batch(mocker):
    sess = mocker.Mock()
    action = 'insert'
    vals = ['CH4U', 'batch 8883', 'Apr 2019']
    args = []
    chellow.general_import.general_import_g_batch(sess, action, vals, args)


def test_general_import_g_bill(mocker):
    c = mocker.patch('chellow.general_import.GContract', autospec=True)
    c.get_by_name.return_value = chellow.general_import.GContract(
        'CH4U', '{}', '{}')

    mocker.patch('chellow.models.GBatch', autospec=True)
    batch = chellow.models.GBatch(1, 2, 3, 4)
    batch.g_contract = chellow.general_import.GContract('CH4U', '{}', '{}')
    c.get_g_batch_by_reference.return_value = batch

    sess = mocker.Mock()
    action = 'insert'
    vals = [
        'CH4U', 'batch 8883', '759288812', '2019-09-08 00:00',
        '2019-10-01 00:00', '2019-10-31 23:30', '0.00', '0.00', '0.00',
        '77hwgtlll', '7876hrwlju', 'N', '{}', '0']
    args = []
    chellow.general_import.general_import_g_bill(sess, action, vals, args)


def test_general_import_g_bill_reads(mocker):
    c = mocker.patch('chellow.general_import.GContract', autospec=True)
    contract = chellow.general_import.GContract('CH4U', '{}', '{}')
    c.get_by_name.return_value = contract

    mocker.patch('chellow.models.GBatch', autospec=True)
    batch = chellow.models.GBatch('CH4U', '{}', '{}', 4)
    contract.get_g_batch_by_reference.return_value = batch

    mocker.patch('chellow.models.GBill', autospec=True)
    bill = chellow.models.GBill(
        mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock(),
        mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock(),
        mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock(),
        mocker.Mock(), mocker.Mock())
    batch.insert_g_bill.return_value = bill

    sess = mocker.Mock()
    msn = '88hgkdshjf'
    g_unit_code = 'M3'
    g_unit_class = mocker.patch('chellow.general_import.GUnit', autospec=True)
    g_unit = chellow.general_import.GUnit(g_unit_code, '', 1)
    g_unit_class.get_by_code.return_value = g_unit
    correction_factor = Decimal('1')
    calorific_value = Decimal('39')
    prev_value = Decimal('988')
    prev_date = utc_datetime(2019, 10, 1)
    prev_type_code = 'E'
    pres_value = Decimal('1200')
    pres_date = utc_datetime(2019, 10, 31, 23, 30)
    pres_type_code = 'A'

    g_read_type_class = mocker.patch(
        'chellow.general_import.GReadType', autospec=True)
    prev_type = chellow.general_import.GReadType(prev_type_code, '')
    pres_type = chellow.general_import.GReadType(pres_type_code, '')
    g_read_type_class.get_by_code.side_effect = [prev_type, pres_type]

    action = 'insert'
    vals = [
        'CH4U', 'batch 8883', '759288812', '2019-09-08 00:00',
        '2019-10-01 00:00', '2019-10-31 23:30', '0.00', '0.00', '0.00',
        '77hwgtlll', '7876hrwlju', 'N', '{}', '0', msn, g_unit_code,
        str(correction_factor), str(calorific_value), hh_format(prev_date),
        str(prev_value), prev_type_code, hh_format(pres_date), str(pres_value),
        pres_type_code]
    args = []
    chellow.general_import.general_import_g_bill(sess, action, vals, args)
    bill.insert_g_read.assert_called_with(
        sess, msn, g_unit, correction_factor, calorific_value, prev_value,
        prev_date, prev_type, pres_value, pres_date, pres_type)
