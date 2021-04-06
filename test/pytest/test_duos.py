import chellow.duos
from chellow.utils import ct_datetime, to_utc
import os
from collections import defaultdict


def test_duos_availability_from_to(mocker):
    mocker.patch("chellow.utils.root_path", "chellow")
    mocker.patch("chellow.utils.url_root", "chellow")
    print(os.getcwd())
    month_from = to_utc(ct_datetime(2019, 2, 1))
    month_to = to_utc(ct_datetime(2019, 2, 28, 23, 30))
    ds = mocker.Mock()
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=[])
    ds.caches = {"dno": {"22": {}}}

    hh = {
        "start-date": ct_datetime(2019, 2, 28, 23, 30),
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "imp-msp-kvarh": 0,
        "exp-msp-kvarh": 0,
    }
    chellow.duos.datum_2010_04_01(ds, hh)

    ds.get_data_sources.assert_called_with(month_from, month_to)
