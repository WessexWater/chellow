import csv
import threading
import traceback
from datetime import datetime as Datetime, timedelta as Timedelta
from decimal import Decimal
from io import StringIO
from zipfile import ZipFile

# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from werkzeug.exceptions import BadRequest

from chellow.models import Contract, Party, Session
from chellow.utils import hh_after, to_ct, to_utc


process_id = 0
process_lock = threading.Lock()
processes = {}


class LafImporter(threading.Thread):
    def __init__(self, zips):
        threading.Thread.__init__(self)
        self.progress = {
            "file_number": None,
            "line_number": None,
        }
        self.zips = zips
        self.rd_lock = threading.Lock()
        self.error_message = None

    def get_fields(self):
        progress = self.progress
        ln = progress["line_number"]
        return {
            "progress": f"Processing file number {progress['file_number'] + 1} "
            + ("" if ln is None else f" line number {ln:,}"),
            "error_message": self.error_message,
        }

    def run(self):
        sess = None
        try:
            sess = Session()
            for file_number, zfile in enumerate(self.zips):
                self.progress["file_number"] = file_number
                _process(sess, self.progress, zfile)

        except BadRequest as e:
            sess.rollback()
            with self.rd_lock:
                self.error_message = e.description

        except BaseException:
            sess.rollback()
            with self.rd_lock:
                self.error_message = traceback.format_exc()
        finally:
            if sess is not None:
                sess.close()


def start_process(zips):
    global process_id
    with process_lock:
        proc_id = process_id
        process_id += 1

    process = LafImporter(zips)
    processes[proc_id] = process
    process.start()
    return proc_id


def get_process_ids():
    with process_lock:
        return processes.keys()


def get_process(id):
    with process_lock:
        return processes[id]


def _process(sess, progress, file_like):
    zip_file = ZipFile(file_like)
    name_list = zip_file.namelist()
    if len(name_list) != 1:
        raise BadRequest("The zip archive must contain exactly one file.")
    stmt = text(
        """
INSERT INTO laf (llfc_id, timestamp, value) VALUES
(unnest(:llfc_ids), unnest(:timestamps), unnest(:values))
ON CONFLICT ON CONSTRAINT laf_llfc_id_timestamp_key
DO UPDATE SET (llfc_id, timestamp, value) =
(EXCLUDED.llfc_id, EXCLUDED.timestamp, EXCLUDED.value)"""
    )
    fname = name_list[0]
    csv_file = StringIO(zip_file.read(fname).decode("utf-8"))
    csv_dt = to_utc(to_ct(Datetime.strptime(fname[-12:-4], "%Y%m%d")))
    for llfc_ids, timestamps, values in laf_days(sess, progress, csv_file, csv_dt):
        sess.execute(
            stmt,
            params={"llfc_ids": llfc_ids, "timestamps": timestamps, "values": values},
        )
        sess.commit()


UTC_DATETIME_MIN = to_utc(Datetime.min)


def laf_days(sess, progress, csv_file, csv_dt):
    llfc_ids = []
    timestamps = []
    values = []
    llfc_code = line_dt_ct = dno = llfc_id = None
    llfc_valid_to = UTC_DATETIME_MIN
    timestamp_cache = {}

    for line_number, vals in enumerate(csv.reader(csv_file, delimiter="|")):
        progress["line_number"] = line_number
        code = vals[0]

        if code == "DIS":
            participant_code = vals[1]
            dno = Party.get_by_participant_code_role_code(
                sess, participant_code, "R", csv_dt
            )

        elif code == "LLF":
            llfc_code = vals[1]
            llfc_valid_to = UTC_DATETIME_MIN

            if len(llfc_ids) > 0:
                yield llfc_ids, timestamps, values
                llfc_ids = []
                timestamps = []
                values = []

        elif code == "SDT":
            line_dt_str = vals[1]
            line_dt_ct = to_ct(Datetime.strptime(line_dt_str, "%Y%m%d"))

        elif code == "SPL":
            period, value = vals[1:]

            try:
                timestamp = timestamp_cache[line_dt_ct][period]
            except KeyError:
                try:
                    day_cache = timestamp_cache[line_dt_ct]
                except KeyError:
                    day_cache = timestamp_cache[line_dt_ct] = {}

                timestamp = day_cache[period] = to_utc(
                    line_dt_ct + Timedelta(minutes=30 * (int(period) - 1))
                )

            if hh_after(timestamp, llfc_valid_to):
                llfc = dno.find_llfc_by_code(sess, llfc_code, timestamp)
                if llfc is None:
                    continue

                llfc_id, llfc_valid_to = llfc.id, llfc.valid_to
            llfc_ids.append(llfc_id)
            timestamps.append(timestamp)
            values.append(Decimal(value))

        elif code == "ZPT":
            earliest_list = sorted(timestamp_cache.keys())
            if len(earliest_list) > 0:
                conf = Contract.get_non_core_by_name(sess, "configuration")
                props = conf.make_properties()
                try:
                    laf_importer = props["laf_importer"]
                except KeyError:
                    laf_importer = props["laf_importer"] = {}

                laf_importer[dno.participant.code] = min(earliest_list)
                conf.update_properties(props)
                sess.commit()
            if len(llfc_ids) > 0:
                yield llfc_ids, timestamps, values
