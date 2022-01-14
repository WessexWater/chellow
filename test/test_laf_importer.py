from io import BytesIO, StringIO
from zipfile import ZipFile

import chellow.laf_import
from chellow.models import MarketRole, Participant
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_laf_days(sess):
    participant_code = "IPNL"
    participant = Participant.insert(sess, participant_code, "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
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
SPL|1|1.074"""
    )
    csv_dt = utc_datetime(2021, 9, 1)
    list(chellow.laf_import.laf_days(sess, progress, csv_file, csv_dt))


def test_process(sess):
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
