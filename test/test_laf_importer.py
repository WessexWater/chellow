from decimal import Decimal
from io import BytesIO, StringIO
from zipfile import ZipFile

import chellow.laf_import
from chellow.models import (
    Contract,
    MarketRole,
    Participant,
    VoltageLevel,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_laf_days(sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    participant_code = "IPNL"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", valid_from, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, valid_from, None, {})
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(
        sess, "500", "PC 5-8 & HH HV", voltage_level, False, True, valid_from, None
    )
    sess.commit()
    progress = {
        "file_number": None,
        "line_number": None,
    }
    csv_file = StringIO(
        """ZHD||D0265001|R|IPNL|G|CAPG|20210914142620||||OPER
DIS|IPNL
LLF|500
SDT|20210922
SPL|1|1.074
ZPT|40672767|423780412"""
    )
    csv_dt = utc_datetime(2021, 9, 1)
    actual = list(chellow.laf_import.laf_days(sess, progress, csv_file, csv_dt))
    expected = [([1], [utc_datetime(2021, 9, 21, 23, 0)], [Decimal("1.074")])]
    assert actual == expected


def test_process_empty_file(sess):
    progress = {
        "file_number": None,
        "line_number": None,
    }
    f = BytesIO()
    zf = ZipFile(f, mode="w")
    zf.writestr("llfipnl20210922.ptf", "")
    zf.close()
    f.seek(0)
    chellow.laf_import._process(sess, progress, f)


def test_process(sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    participant_code = "IPNL"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", valid_from, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, valid_from, None, {})
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(
        sess, "500", "PC 5-8 & HH HV", voltage_level, False, True, valid_from, None
    )
    sess.commit()
    progress = {
        "file_number": None,
        "line_number": None,
    }
    csv_str = """ZHD||D0265001|R|IPNL|G|CAPG|20210914142620||||OPER
DIS|IPNL
LLF|500
SDT|20210922
SPL|1|1.074
ZPT|40672767|423780412"""
    f = BytesIO()
    zf = ZipFile(f, mode="w")
    zf.writestr("llfipnl20210922.ptf", csv_str)
    zf.close()
    f.seek(0)
    chellow.laf_import._process(sess, progress, f)
