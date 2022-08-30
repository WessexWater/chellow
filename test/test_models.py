import pytest

import sqlalchemy.exc

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Comm,
    Contract,
    Cop,
    EnergisationStatus,
    Era,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfc,
    MtcLlfcSsc,
    MtcLlfcSscPc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Pc,
    Scenario,
    Site,
    Source,
    Ssc,
    Supply,
    Tpr,
    VoltageLevel,
    _jsonize,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_Era_update(sess):
    """Successful"""
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, valid_from, None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, valid_from, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
        valid_from,
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, valid_from, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    imp_mpan_core = "22 7867 6232 781"
    supply = site.insert_e_supply(
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
        "e1msn",
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
        imp_mpan_core,
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
    era = supply.eras[0]
    msn = "e2msn"
    era.update(
        sess,
        era.start_date,
        None,
        mop_contract,
        "379540",
        dc_contract,
        "547yt",
        msn,
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
        imp_mpan_core,
        "510",
        imp_supplier_contract,
        "9745y6",
        361,
        None,
        None,
        None,
        None,
        None,
    )

    sess.commit()
    era = Era.get_by_id(sess, era.id)

    assert era.msn == msn


def test_Era_meter_category_dumb(sess):
    """Successful"""
    valid_from = utc_datetime(1996, 1, 1)
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "02", "nhh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, valid_from, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
        valid_from,
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
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)
    imp_mpan_core = "22 7867 6232 781"
    supply = site.insert_e_supply(
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
        "e1msn",
        pc,
        "845",
        cop,
        comm,
        ssc,
        energisation_status,
        {},
        imp_mpan_core,
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
    era = supply.eras[0]
    era.meter_category

    sess.commit()


def test_Mtc_find_by_code(sess):
    code = "034"
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    Mtc.insert(
        sess,
        code,
        False,
        True,
        valid_from,
        None,
    )
    sess.commit()

    mtc = Mtc.find_by_code(sess, "34", valid_from)
    assert mtc.code == code


def test_MtcParticipant_find_by_values(sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    code = "034"
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
    mtc = Mtc.insert(
        sess,
        code,
        False,
        True,
        valid_from,
        None,
    )
    MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "an mtc",
        False,
        True,
        meter_type,
        meter_payment_type,
        1,
        utc_datetime(2000, 1, 1),
        None,
    )
    sess.commit()

    mtc_participant = MtcParticipant.find_by_values(sess, mtc, participant, valid_from)
    assert mtc_participant.mtc.code == code


def test_MtcSSC_get_by_values(sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    code = "034"
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", valid_from, None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
    mtc = Mtc.insert(
        sess,
        code,
        False,
        True,
        valid_from,
        None,
    )
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "an mtc",
        False,
        True,
        meter_type,
        meter_payment_type,
        1,
        utc_datetime(2000, 1, 1),
        None,
    )
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
    sess.commit()

    with pytest.raises(
        BadRequest,
        match="For the participant CALB there isn't an MTC SSC with the MTC 034 and "
        "SSC 0001 at date 2000-01-01 00:00.",
    ):
        MtcSsc.get_by_values(sess, mtc_participant, ssc, valid_from)


def test_Era_init_llfc_valid_to(sess):
    """
    Error raised if LLFC finishes before the era
    """
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
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
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
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
    mtc = Mtc.insert(
        sess,
        "845",
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcParticipant.insert(
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(2000, 5, 1)),
        to_utc(ct_datetime(2010, 5, 1)),
    )
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    imp_mpan_core = "22 7867 6232 781"
    with pytest.raises(
        BadRequest,
        match="The imp line loss factor 510 is only valid until "
        "2010-05-01 00:00 but the era ends at 2011-01-01 00:00.",
    ):
        site.insert_e_supply(
            sess,
            source,
            None,
            "Bob",
            to_utc(ct_datetime(2002, 7, 1)),
            to_utc(ct_datetime(2011, 1, 1)),
            gsp_group,
            mop_contract,
            "773",
            dc_contract,
            "ghyy3",
            "e1msn",
            pc,
            "845",
            cop,
            comm,
            None,
            energisation_status,
            {},
            imp_mpan_core,
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


def test_Contract_get_next_batch_details(mocker):
    MockBatch = mocker.patch("chellow.models.Batch", autospec=True)
    MockBatch.contract = mocker.Mock()
    instance = mocker.Mock()

    batch_description = "A King"
    batch = mocker.Mock()
    batch.reference = "king-098"
    batch.description = batch_description

    returns = iter([batch])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def order_by(self, *args):
            return self

        def filter(self, *args):
            return self

        def first(self, *args):
            return next(returns)

    sess = Sess()
    ref, desc = Contract.get_next_batch_details(instance, sess)
    assert ref == "king-099"
    assert desc == batch_description


def test_Contract_get_next_batch_details__no_suffix(mocker):
    MockBatch = mocker.patch("chellow.models.Batch", autospec=True)
    MockBatch.contract = mocker.Mock()
    instance = mocker.Mock()

    batch_reference = "king"
    batch_description = "A King"
    batch = mocker.Mock()
    batch.reference = batch_reference
    batch.description = batch_description

    returns = iter([batch])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def order_by(self, *args):
            return self

        def filter(self, *args):
            return self

        def first(self, *args):
            return next(returns)

    sess = Sess()
    ref, desc = Contract.get_next_batch_details(instance, sess)
    assert ref == batch_reference
    assert desc == batch_description


def test_Tpr_get_by_code_not_found(sess):
    with pytest.raises(
        BadRequest,
        match="A TPR with code 'g' expanded to '0000g' can't be found.",
    ):
        Tpr.get_by_code(sess, "g")


def test_Tpr_get_by_code_found(sess):
    code = "00001"
    is_teleswitch = False
    is_gmt = True
    Tpr.insert(sess, code, is_teleswitch, is_gmt)
    sess.commit()

    tpr = Tpr.get_by_code(sess, code)
    assert tpr.code == code
    assert tpr.is_teleswitch == is_teleswitch
    assert tpr.is_gmt == is_gmt


def test_sql_insert_GExitZone(mocker, sess):
    with pytest.raises(
        sqlalchemy.exc.ProgrammingError,
        match='null value in column "g_ldz_id" violates not-null ' "constraint",
    ):
        sess.execute(
            "INSERT INTO g_exit_zone (id, code, g_ldz_id) VALUES "
            "(DEFAULT, 'E1', null)"
        )


def test_Supply_get_by_MPAN_core(sess):
    mpan_core = "22 1737 1873 221"

    with pytest.raises(
        BadRequest, match=f"The MPAN core {mpan_core} is not set up in Chellow."
    ):

        Supply.get_by_mpan_core(sess, mpan_core)


def test_Supply_insert_era_at(sess):
    """Where an era is inserted in the last HH of another era, check
    the template era is the one at the insertion date.
    """
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
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
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    era1_msn = "e1msn"
    imp_mpan_core = "22 7867 6232 781"
    supply = site.insert_e_supply(
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
        era1_msn,
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
        imp_mpan_core,
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
    era1 = supply.eras[0]
    era2_start_date = utc_datetime(2009, 7, 31, 23, 30)
    era2 = supply.insert_era_at(sess, era2_start_date)
    era2_msn = "e2msn"
    era2.update(
        sess,
        era2_start_date,
        None,
        mop_contract,
        "379540",
        dc_contract,
        "547yt",
        era2_msn,
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
        imp_mpan_core,
        "510",
        imp_supplier_contract,
        "9745y6",
        361,
        None,
        None,
        None,
        None,
        None,
    )

    sess.commit()

    start_date = utc_datetime(2009, 7, 31, 23, 00)
    era3 = supply.insert_era_at(sess, start_date)
    assert era3.msn == era1.msn


def test_Scenario_init(sess):
    name = "scenario_bau"
    properties = {
        "local_rates": {},
        "scenario_start_year": 2015,
        "scenario_start_month": 6,
        "scenario_duration": 1,
    }

    with pytest.raises(BadRequest, match="The 'local_rates' must be a list."):
        Scenario(name, properties)


def test_jsonize():
    val = {1, None}
    actual = _jsonize(val)
    assert actual == [1, None]
