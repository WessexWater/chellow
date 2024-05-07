from io import StringIO

from sqlalchemy.orm.session import Session

from chellow.models import User, UserRole
from chellow.reports.report_41 import _make_eras, content
from chellow.utils import utc_datetime


def test_eras(mocker):
    """If there's a meter change, a pair can start after the end of the chunk.
    here we test the case for a pair before and after the chunk finish.
    """
    sess = Session()
    year_start = utc_datetime(2010, 4, 1)
    year_finish = utc_datetime(2011, 3, 31, 23, 30)
    supply_id = None
    eras = _make_eras(sess, year_start, year_finish, supply_id)
    desired = "".join(
        (
            "SELECT era.id AS era_id, era.supply_id AS era_supply_id, "
            "era.start_date AS era_start_date, "
            "era.finish_date AS era_finish_date, "
            "era.mop_contract_id AS era_mop_contract_id, "
            "era.mop_account AS era_mop_account, "
            "era.dc_contract_id AS era_dc_contract_id, "
            "era.dc_account AS era_dc_account, "
            "era.msn AS era_msn, "
            "era.pc_id AS era_pc_id, "
            "era.mtc_participant_id AS era_mtc_participant_id, "
            "era.cop_id AS era_cop_id, "
            "era.comm_id AS era_comm_id, "
            "era.ssc_id AS era_ssc_id, "
            "era.energisation_status_id AS era_energisation_status_id, "
            "era.dtc_meter_type_id AS era_dtc_meter_type_id, "
            "era.imp_mpan_core AS era_imp_mpan_core, "
            "era.imp_llfc_id AS era_imp_llfc_id, "
            "era.imp_supplier_contract_id AS era_imp_supplier_contract_id, "
            "era.imp_supplier_account AS era_imp_supplier_account, "
            "era.imp_sc AS era_imp_sc, "
            "era.exp_mpan_core AS era_exp_mpan_core, "
            "era.exp_llfc_id AS era_exp_llfc_id, "
            "era.exp_supplier_contract_id AS era_exp_supplier_contract_id, "
            "era.exp_supplier_account AS era_exp_supplier_account, "
            "era.exp_sc AS era_exp_sc \n"
            "FROM era JOIN supply ON supply.id = era.supply_id "
            "JOIN source ON source.id = supply.source_id "
            "JOIN pc ON pc.id = era.pc_id \n"
            "WHERE era.start_date <= :start_date_1 AND "
            "(era.finish_date IS NULL OR era.finish_date >= :finish_date_1) "
            "AND source.code IN (__[POSTCOMPILE_code_1]) AND pc.code = :code_2 "
            "ORDER BY supply.id"
        )
    )
    actual = str(eras)
    assert actual == desired


def test_content(mocker, sess):
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_41.open_file", return_value=mock_file)

    year = 2010
    supply_id = None
    user_id = user.id
    content(year, supply_id, user_id)

    actual = mock_file.getvalue()
    expected = [
        "Site Code",
        "Site Name",
        "Supply Name",
        "Source",
        "Generator Type",
        "Import MPAN Core",
        "Import T1 Date",
        "Import T1 MSP kW",
        "Import T1 Status",
        "Import T1 LAF",
        "Import T1 GSP kW",
        "Import T2 Date",
        "Import T2 MSP kW",
        "Import T2 Status",
        "Import T2 LAF",
        "Import T2 GSP kW",
        "Import T3 Date",
        "Import T3 MSP kW",
        "Import T3 Status",
        "Import T3 LAF",
        "Import T3 GSP kW",
        "Import GSP kW",
        "Import Rate GBP / kW",
        "Import GBP",
        "Export MPAN Core",
        "Export T1 Date",
        "Export T1 MSP kW",
        "Export T1 Status",
        "Export T1 LAF",
        "Export T1 GSP kW",
        "Export T2 Date",
        "Export T2 MSP kW",
        "Export T2 Status",
        "Export T2 LAF",
        "Export T2 GSP kW",
        "Export T3 Date",
        "Export T3 MSP kW",
        "Export T3 Status",
        "Export T3 LAF",
        "Export T3 GSP kW",
        "Export GSP kW",
        "Export Rate GBP / kW",
        "Export GBP",
    ]
    print(actual)
    assert actual == ",".join(expected) + "\n"
