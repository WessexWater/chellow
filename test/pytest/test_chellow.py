import chellow.bill_parser_csv
from chellow.utils import to_utc, ct_datetime, utc_datetime
from chellow.computer import PropDict
from pytz import utc
from datetime import datetime as Datetime
from chellow.models import Era
import pytest
from werkzeug.exceptions import BadRequest


def test_bill_parser_csv():
    '''
    Check bills have a UTC timezone
    '''

    with open('test/bills-nhh.csv', 'rb') as f:
        parser = chellow.bill_parser_csv.Parser(f)
        for bill in parser.make_raw_bills():
            for read in bill['reads']:
                for k in ('prev_date', 'pres_date'):
                    assert read[k].tzinfo is not None


def test_to_utc():
    dt_utc = to_utc(ct_datetime(2014, 9, 6, 1))
    assert dt_utc == Datetime(2014, 9, 6, 0, 0, tzinfo=utc)


def test_propdict_get():
    assert PropDict(
        'cont ' + str(Datetime(2017, 1, 1)), {}, []).get('akey') is None


def test_propdict():
    assert PropDict('', {'*': 5})[1] == 5


def test_propdict_nested():
    assert PropDict('', {1: {'*': 5}})[1][1] == 5


def test_update_era_llfc_valid_to(mocker):
    """
    Error raised if LLFC finishes before the era
    """
    llfc = mocker.Mock()
    llfc.valid_from = utc_datetime(2000, 1, 1)
    llfc.valid_to = utc_datetime(2010, 5, 1)

    start_date = utc_datetime(2010, 1, 1)
    finish_date = utc_datetime(2011, 1, 1)
    mop_account = "A mop account"
    dc_account = "A dc account"
    msn = "mtr001"
    mtc_code = "845"
    properties = {}
    imp_mpan_core = "22 9877 3472 588"
    imp_llfc_code = "510"
    imp_supplier_contract = mocker.Mock()
    imp_supplier_contract.start_date.return_value = utc_datetime(2000, 1, 1)
    imp_supplier_contract.finish_date.return_value = None
    instance = mocker.Mock()
    instance.supply.dno.dno_code = '22'
    instance.supply.dno.get_llfc_by_code.return_value = llfc

    with pytest.raises(
            BadRequest,
            match="The imp line loss factor 510 is only valid until "
            "2010-05-01 00:00 but the era ends at 2011-01-01 00:00."):
        Era.update(
            instance, mocker.Mock(), start_date, finish_date, mocker.Mock(),
            mop_account, mocker.Mock(), dc_account, msn, mocker.Mock(),
            mtc_code, mocker.Mock(), mocker.Mock(), properties, imp_mpan_core,
            imp_llfc_code, imp_supplier_contract, mocker.Mock(), mocker.Mock(),
            mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock(),
            mocker.Mock(), mocker.Mock())
