from io import StringIO

from chellow.models import (
    Contract,
    Cop,
    EnergisationStatus,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    Participant,
    Pc,
    Site,
    Source,
    VoltageLevel,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_ecoes_comparison import _process
from chellow.utils import utc_datetime


def test_process(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    dc_contract = Contract.insert_hhdc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
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
    Mtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
    dno.insert_llfc(
        sess,
        "521",
        "Export (HV)",
        voltage_level,
        False,
        False,
        utc_datetime(1996, 1, 1),
        None,
    )
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
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

    site.insert_e_supply(
        sess,
        source,
        None,
        "Dave",
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
        None,
        energisation_status,
        {},
        "22 7868 6232 789",
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
    f = StringIO()
    ecoes_lines = [
        "titles",
        ",".join(
            (
                "2278676232781",
                "address-line-1",
                "address-line-2",
                "address-line-3",
                "address-line-4",
                "address-line-5",
                "address-line-6",
                "address-line-7",
                "address-line-8",
                "address-line-9",
                "post-code",
                "supplier",
                "registration-from",
                "mtc",
                "mtc-date",
                "llfc",
                "llfc-from",
                "pc",
                "",
                "measurement-class",
                "energisation-status",
                "da",
                "dc",
                "mop",
                "mop-appoint-date",
                "gsp-group",
                "gsp-effective-from",
                "dno",
                "msn",
                "meter-install-date",
                "meter-type",
                "map-id",
            ),
        ),
        ",".join(
            (
                "2278686232789",
                "address-line-1",
                "address-line-2",
                "address-line-3",
                "address-line-4",
                "address-line-5",
                "address-line-6",
                "address-line-7",
                "address-line-8",
                "address-line-9",
                "post-code",
                "supplier",
                "registration-from",
                "mtc",
                "mtc-date",
                "llfc",
                "llfc-from",
                "pc",
                "",
                "measurement-class",
                "energisation-status",
                "da",
                "dc",
                "mop",
                "mop-appoint-date",
                "gsp-group",
                "gsp-effective-from",
                "dno",
                "msn",
                "meter-install-date",
                "meter-type",
                "map-id",
            ),
        ),
    ]
    exclude_mpan_cores = []
    ignore_mpan_cores_msn = []
    show_ignored = True

    _process(
        sess,
        ecoes_lines,
        exclude_mpan_cores,
        ignore_mpan_cores_msn,
        f,
        show_ignored,
    )
    expected = [
        [
            "MPAN Core",
            "MPAN Core No Spaces",
            "ECOES PC",
            "Chellow PC",
            "ECOES MTC",
            "Chellow MTC",
            "ECOES LLFC",
            "Chellow LLFC",
            "ECOES SSC",
            "Chellow SSC",
            "ECOES Energisation Status",
            "Chellow Energisation Status",
            "ECOES Supplier",
            "Chellow Supplier",
            "ECOES DC",
            "Chellow DC",
            "ECOES MOP",
            "Chellow MOP",
            "ECOES GSP Group",
            "Chellow GSP Group",
            "ECOES MSN",
            "Chellow MSN",
            "ECOES Meter Type",
            "Chellow Meter Type",
            "Ignored",
            "Problem",
        ],
        [
            "22 7867 6232 781",
            "2278676232781",
            "pc",
            "00",
            "mtc",
            "845",
            "llfc",
            "510",
            "",
            "",
            "energisation-status",
            "E",
            "supplier",
            "CALB",
            "dc",
            "CALB",
            "mop",
            "CALB",
            "gsp-group",
            "_L",
            "msn",
            "hgjeyhuw",
            "meter-type",
            "H",
            "False",
            "The energisation statuses don't match. Can't parse the PC. Can't parse "
            "the MTC. The LLFCs don't match. The supplier codes don't match. The DC "
            "codes don't match. The MOP codes don't match. The GSP group codes don't "
            "match. The meter serial numbers don't match. The meter types don't match. "
            "See https://dtc.mrasco.com/DataItem.aspx?ItemCounter=0483 ",
        ],
        [
            "22 7868 6232 789",
            "2278686232789",
            "pc",
            "00",
            "mtc",
            "845",
            "llfc",
            "510",
            "",
            "",
            "energisation-status",
            "E",
            "supplier",
            "CALB",
            "dc",
            "CALB",
            "mop",
            "CALB",
            "gsp-group",
            "_L",
            "msn",
            "hgjeyhuw",
            "meter-type",
            "H",
            "False",
            "The energisation statuses don't match. Can't parse the PC. Can't parse "
            "the MTC. The LLFCs don't match. The supplier codes don't match. The DC "
            "codes don't match. The MOP codes don't match. The GSP group codes don't "
            "match. The meter serial numbers don't match. The meter types don't match. "
            "See https://dtc.mrasco.com/DataItem.aspx?ItemCounter=0483 ",
        ],
    ]
    assert f.getvalue() == "\n".join(",".join(line) for line in expected) + "\n"
