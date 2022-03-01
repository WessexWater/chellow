from sqlalchemy.orm.session import Session

import chellow.reports.report_41
from chellow.utils import utc_datetime


def test_eras(mocker):
    """If there's a meter change, a pair can start after the end of the chunk.
    here we test the case for a pair before and after the chunk finish.
    """
    sess = Session()
    year_start = utc_datetime(2010, 4, 1)
    year_finish = utc_datetime(2011, 3, 31, 23, 30)
    supply_id = None
    eras = chellow.reports.report_41._make_eras(
        sess, year_start, year_finish, supply_id
    )
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
            "era.properties AS era_properties, "
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
    print(desired)
    assert str(eras) == desired
