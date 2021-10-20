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
    Participant,
    Pc,
    Scenario,
    Site,
    Source,
    Supply,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
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
    pc.code = "00"
    mtc = mocker.Mock()
    cop = mocker.Mock()
    comm = mocker.Mock()
    ssc = None
    energisation_status = mocker.Mock()
    properties = {}
    imp_mpan_core = "22 3423 2442 127"
    imp_llfc_code = "110"
    imp_supplier_contract = mocker.Mock()
    imp_supplier_contract.start_date.return_value = start_date
    imp_supplier_contract.finish_date.return_value = None
    imp_supplier_account = "supplier account"
    imp_sc = 400
    exp_mpan_core = exp_llfc_code = exp_supplier_contract = None
    exp_supplier_account = exp_sc = None

    era = mocker.Mock()
    era.start_date = start_date
    era.finish_date = finish_date
    era.supply.dno.dno_code = "22"
    era.supply.dno.get_llfc_by_code().valid_to = finish_date
    era.supply.dno.get_llfc_by_code().is_import = True
    era.supply.find_era_at.return_value = None
    Era.update(
        era,
        sess,
        start_date,
        finish_date,
        mop_contract,
        mop_account,
        dc_contract,
        dc_account,
        msn,
        pc,
        mtc,
        cop,
        comm,
        ssc,
        energisation_status,
        properties,
        imp_mpan_core,
        imp_llfc_code,
        imp_supplier_contract,
        imp_supplier_account,
        imp_sc,
        exp_mpan_core,
        exp_llfc_code,
        exp_supplier_contract,
        exp_supplier_account,
        exp_sc,
    )
    assert era.msn == "yhlk"


def test_MTC_find_by_code(sess):
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    code = "034"
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    Mtc.insert(
        sess,
        dno,
        code,
        "an mtc",
        False,
        False,
        True,
        meter_type,
        meter_payment_type,
        1,
        utc_datetime(2000, 1, 1),
        None,
    )
    sess.commit()

    mtc = Mtc.find_by_code(sess, dno, "34", utc_datetime(2000, 1, 1))
    assert mtc.code == code


def test_update_Era_llfc_valid_to(mocker):
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
    cop = mocker.Mock()
    comm = mocker.Mock()
    ssc = mocker.Mock()
    energisation_status = mocker.Mock()
    properties = {}
    imp_mpan_core = "22 9877 3472 588"
    imp_llfc_code = "510"
    imp_supplier_contract = mocker.Mock()
    imp_supplier_contract.start_date.return_value = utc_datetime(2000, 1, 1)
    imp_supplier_contract.finish_date.return_value = None
    instance = mocker.Mock()
    instance.supply.dno.dno_code = "22"
    instance.supply.dno.get_llfc_by_code.return_value = llfc

    with pytest.raises(
        BadRequest,
        match="The imp line loss factor 510 is only valid until "
        "2010-05-01 01:00 but the era ends at 2011-01-01 00:00.",
    ):
        Era.update(
            instance,
            mocker.Mock(),
            start_date,
            finish_date,
            mocker.Mock(),
            mop_account,
            mocker.Mock(),
            dc_account,
            msn,
            mocker.Mock(),
            mtc_code,
            cop,
            comm,
            ssc,
            energisation_status,
            properties,
            imp_mpan_core,
            imp_llfc_code,
            imp_supplier_contract,
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
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
    mtc_845 = Mtc.insert(
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
        mtc_845,
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
