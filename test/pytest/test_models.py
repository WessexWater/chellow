from chellow.models import Era, Mtc
from chellow.utils import utc_datetime


def test_Era_update(mocker):
    sess = mocker.Mock()
    start_date = utc_datetime(2019, 1, 1)
    finish_date = utc_datetime(2019, 1, 10)
    mop_contract = mocker.Mock()
    mop_contract.start_date.return_value = start_date
    mop_contract.finish_date.return_value = finish_date
    mop_account = "mop account"
    dc_contract = mocker.Mock()
    dc_contract.start_date.return_value = start_date
    dc_contract.finish_date.return_value = finish_date
    dc_account = "dc account"
    msn = " yhlk "
    pc = mocker.Mock()
    mtc = mocker.Mock()
    cop = mocker.Mock()
    ssc = mocker.Mock()
    properties = {}
    imp_mpan_core = '22 3423 2442 127'
    imp_llfc_code = '110'
    imp_supplier_contract = mocker.Mock()
    imp_supplier_contract.start_date.return_value = start_date
    imp_supplier_contract.finish_date.return_value = None
    imp_supplier_account = 'supplier account'
    imp_sc = 400
    exp_mpan_core = exp_llfc_code = exp_supplier_contract = None
    exp_supplier_account = exp_sc = None

    era = mocker.Mock()
    era.start_date = start_date
    era.finish_date = finish_date
    era.supply.dno.dno_code = '22'
    era.supply.dno.get_llfc_by_code().valid_to = finish_date
    era.supply.dno.get_llfc_by_code().is_import = True
    era.supply.find_era_at.return_value = None
    Era.update(
        era, sess, start_date, finish_date, mop_contract, mop_account,
        dc_contract, dc_account, msn, pc, mtc, cop, ssc, properties,
        imp_mpan_core, imp_llfc_code, imp_supplier_contract,
        imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
        exp_supplier_contract, exp_supplier_account, exp_sc)
    assert era.msn == 'yhlk'


def test_MTC_find_by_code(mocker):
    q_mock = mocker.Mock()
    q_mock.filter_by = mocker.Mock(return_value=mocker.Mock())
    sess = mocker.Mock()
    sess.query.return_value = q_mock
    dno = mocker.Mock()
    code = '34'

    Mtc.find_by_code(sess, dno, code)
    q_mock.filter_by.assert_called_with(dno=dno, code='034')
