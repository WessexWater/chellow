from io import StringIO

from chellow.models import (
    Comm,
    Contract,
    Cop,
    EnergisationStatus,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfc,
    MtcParticipant,
    Participant,
    Pc,
    Site,
    Source,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_149 import _process, content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_content_blank(mocker, client):
    supply_id = None
    start_date = to_utc(ct_datetime(2022, 1, 1))
    finish_date = to_utc(ct_datetime(2022, 1, 31, 23, 30))
    user = None
    mpan_cores = None
    content(supply_id, start_date, finish_date, user, mpan_cores)


def test_process_blank(sess, mocker):
    supply_id = None
    start_date = to_utc(ct_datetime(2022, 1, 1))
    finish_date = to_utc(ct_datetime(2022, 1, 31, 23, 30))
    f = StringIO()
    caches = {}
    mpan_cores = None
    _process(sess, caches, f, start_date, finish_date, supply_id, mpan_cores)
    expected = [
        "era_start",
        "era_finish",
        "supply_id",
        "supply_name",
        "source",
        "generator_type",
        "site_code",
        "site_name",
        "associated_site_codes",
        "from",
        "to",
        "pc",
        "mtc",
        "cop",
        "ssc",
        "energisation_status",
        "properties",
        "mop_contract",
        "mop_account",
        "dc_contract",
        "dc_account",
        "normal_reads",
        "type",
        "supply_start",
        "supply_finish",
        "import_llfc",
        "import_mpan_core",
        "import_supply_capacity",
        "import_supplier",
        "import_msp_kwh",
        "import_non_actual_msp_kwh",
        "import_gsp_kwh",
        "import_md_kw",
        "import_md_kw_date",
        "import_md_kva",
        "import_md_kva_date",
        "import_bad_hhs",
        "export_llfc",
        "export_mpan_core",
        "export_supply_capacity",
        "export_supplier",
        "export_msp_kwh",
        "export_non_actual_msp_kwh",
        "export_gsp_kwh",
        "export_md_kw",
        "export_md_kw_date",
        "export_md_kva",
        "export_md_kva_date",
        "export_bad_hhs",
    ]
    assert f.getvalue() == ",".join(expected) + "\n"


def test_process(sess, mocker):
    start_date = to_utc(ct_datetime(2022, 1, 1))
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)

    mop_charge_script = ""
    mop_contract = Contract.insert_mop(
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

    dc_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]

        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))

    ds.dc_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""

    dc_contract = Contract.insert_dc(
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['sum-msp-kwh'] = hh['msp-kwh']
        bill_hh['sum-msp-gbp'] = hh['msp-kwh'] * 0.1
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        supplier_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "HH COP5 And Above With Comms",
        False,
        True,
        meter_type,
        meter_payment_type,
        0,
        utc_datetime(1996, 1, 1),
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )

    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        None,
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
        "22 7867 6232 781",
        "510",
        imp_supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )

    sess.commit()

    supply_id = None
    f = StringIO()
    caches = {}
    mpan_cores = None
    _process(sess, caches, f, start_date, start_date, supply_id, mpan_cores)
    expected = [
        [
            "era_start",
            "era_finish",
            "supply_id",
            "supply_name",
            "source",
            "generator_type",
            "site_code",
            "site_name",
            "associated_site_codes",
            "from",
            "to",
            "pc",
            "mtc",
            "cop",
            "ssc",
            "energisation_status",
            "properties",
            "mop_contract",
            "mop_account",
            "dc_contract",
            "dc_account",
            "normal_reads",
            "type",
            "supply_start",
            "supply_finish",
            "import_llfc",
            "import_mpan_core",
            "import_supply_capacity",
            "import_supplier",
            "import_msp_kwh",
            "import_non_actual_msp_kwh",
            "import_gsp_kwh",
            "import_md_kw",
            "import_md_kw_date",
            "import_md_kva",
            "import_md_kva_date",
            "import_bad_hhs",
            "export_llfc",
            "export_mpan_core",
            "export_supply_capacity",
            "export_supplier",
            "export_msp_kwh",
            "export_non_actual_msp_kwh",
            "export_gsp_kwh",
            "export_md_kw",
            "export_md_kw_date",
            "export_md_kva",
            "export_md_kva_date",
            "export_bad_hhs",
        ],
        [
            "2000-01-01 00:00",
            "",
            "1",
            "Bob",
            "net",
            "",
            "CI017",
            "Water Works",
            "",
            "2009-08-01 00:00",
            "2009-08-01 00:00",
            "00",
            "845",
            "5",
            "",
            "E",
            "{}",
            "Fusion Mop Contract",
            "773",
            "Fusion DC 2000",
            "ghyy3",
            "0",
            "hh",
            "2000-01-01 00:00",
            "",
            "510",
            "22 7867 6232 781",
            "361",
            "Fusion Supplier 2000",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
    ]
    print(f.getvalue())
    expected_str = "\n".join(",".join(line) for line in expected) + "\n"
    assert f.getvalue() == expected_str
