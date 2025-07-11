from decimal import Decimal
from io import BytesIO, StringIO
from zipfile import BadZipFile, ZipFile

import pytest

from chellow.e.lafs import _process, find_participant_entries, laf_days
from chellow.models import (
    Contract,
    MarketRole,
    Participant,
    VoltageLevel,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_laf_days(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    participant_code = "IPNL"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(sess, "500", "PC 5-8 & HH HV", voltage_level, False, True, vf, None)
    sess.commit()
    csv_file = StringIO(
        """ZHD||D0265001|R|IPNL|G|CAPG|20210914142620||||OPER
DIS|IPNL
LLF|500
SDT|20210922
SPL|1|1.074
ZPT|40672767|423780412"""
    )
    csv_dt = utc_datetime(2021, 9, 1)
    log = mocker.Mock()
    set_progress = mocker.Mock()
    actual = list(laf_days(sess, log, set_progress, csv_file, csv_dt))
    expected = [([1], [utc_datetime(2021, 9, 21, 23, 0)], [Decimal("1.074")])]
    assert actual == expected


def test_process_empty_file(mocker, sess):
    log = mocker.Mock()
    set_progress = mocker.Mock()
    f = BytesIO()
    zf = ZipFile(f, mode="w")
    zf.writestr("llfipnl20210922.ptf", "")
    zf.close()
    f.seek(0)
    _process(sess, log, set_progress, f)


def test_process(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    participant_code = "IPNL"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(sess, "500", "PC 5-8 & HH HV", voltage_level, False, True, vf, None)
    sess.commit()
    log = mocker.Mock()
    set_progress = mocker.Mock()
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
    _process(sess, log, set_progress, f)


def test_laf_import_error(mocker, sess):
    file_lines = ("",)

    file_bytes = "\n".join(file_lines).encode("utf8")
    f = BytesIO(file_bytes)

    log = mocker.Mock()
    set_progress = mocker.Mock()

    with pytest.raises(BadZipFile, match="File is not a zip file"):
        _process(sess, log, set_progress, f)


def test_find_participant_entries_empty():
    paths = []
    laf_cache = {}
    actual_entries = find_participant_entries(paths, laf_cache)
    expected_entries = {}
    assert actual_entries == expected_entries


def test_find_participant_entries_single():
    paths = [(("2023", "electricity", "lafs", "llfipnl20210922.ptf.zip"), "url")]
    laf_cache = {}
    actual_entries = find_participant_entries(paths, laf_cache)
    expected_entries = {"ipnl": {"20210922": "url"}}
    assert actual_entries == expected_entries


def test_find_participant_entries_single_in_state():
    paths = [(("2023", "electricity", "lafs", "llfipnl20210922.ptf.zip"), "url")]
    laf_cache = {"ipnl": "20210922"}
    actual_entries = find_participant_entries(paths, laf_cache)
    expected_entries = {}
    assert actual_entries == expected_entries
