import csv
from datetime import datetime as Datetime, timedelta as Timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from zipfile import ZipFile

# from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text

from werkzeug.exceptions import BadRequest

from chellow.models import Contract, Party
from chellow.rate_server import download
from chellow.utils import hh_after, to_ct, to_utc


def _process(sess, log, set_progress, file_like):
    zip_file = ZipFile(file_like)
    name_list = zip_file.namelist()
    if len(name_list) != 1:
        raise BadRequest("The zip archive must contain exactly one file.")
    stmt = text(
        """
INSERT INTO laf (llfc_id, timestamp, value) VALUES
(unnest(CAST(:llfc_ids AS INTEGER[])), unnest(CAST(:timestamps AS TIMESTAMPTZ[])),
unnest(CAST(:values AS NUMERIC[])))
ON CONFLICT ON CONSTRAINT laf_llfc_id_timestamp_key
DO UPDATE SET (llfc_id, timestamp, value) =
(EXCLUDED.llfc_id, EXCLUDED.timestamp, EXCLUDED.value)"""
    )
    fname = name_list[0]
    csv_file = StringIO(zip_file.read(fname).decode("utf-8"))
    csv_dt = to_utc(to_ct(Datetime.strptime(fname[-12:-4], "%Y%m%d")))
    for llfc_ids, timestamps, values in laf_days(
        sess, log, set_progress, csv_file, csv_dt
    ):
        sess.execute(
            stmt,
            params={"llfc_ids": llfc_ids, "timestamps": timestamps, "values": values},
        )
        sess.commit()


UTC_DATETIME_MIN = to_utc(Datetime.min)


def laf_days(sess, log, set_progress, csv_file, csv_dt):
    llfc_ids = []
    timestamps = []
    values = []
    llfc_code = line_dt_ct = dno = llfc_id = None
    llfc_valid_to = UTC_DATETIME_MIN
    timestamp_cache = {}

    for line_number, vals in enumerate(csv.reader(csv_file, delimiter="|")):
        set_progress(f"Reached line number {line_number}")
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
            if len(llfc_ids) > 0:
                yield llfc_ids, timestamps, values


LAF_START = "llf"
LAF_END = "ptf.zip"


def find_participant_entries(paths, laf_state):
    participant_entries = {}
    for path, url in paths:
        if len(path) == 4:
            year_str, utility, rate_type, file_name = path

            if utility == "electricity" and rate_type == "lafs":
                # File name llfetcl20220401ptf.zip
                if not file_name.startswith(LAF_START):
                    raise BadRequest(f"A laf file must begin with '{LAF_START}'")
                if not file_name.endswith(LAF_END):
                    raise BadRequest(f"A laf file must end with '{LAF_END}'")

                participant_code = file_name[3:7]
                timestamp = file_name[7:15]

                participant_state = laf_state.get(participant_code, "")
                if timestamp > participant_state:
                    try:
                        fl_entries = participant_entries[participant_code]
                    except KeyError:
                        fl_entries = participant_entries[participant_code] = {}
                    fl_entries[timestamp] = url
    return participant_entries


def rate_server_import(sess, log, set_progress, s, paths):
    log("Starting to check for new LAF files")
    conf = Contract.get_non_core_by_name(sess, "configuration")
    state = conf.make_state()

    try:
        laf_state = state["laf_importer"]
    except KeyError:
        laf_state = state["laf_importer"] = {}

    participant_entries = find_participant_entries(paths, laf_state)

    for participant_code, fl_entries in sorted(participant_entries.items()):
        log(f"Importing files for participant code {participant_code}")
        for timestamp, url in sorted(fl_entries.items()):
            log(f"Importing file with timestamp {timestamp}")

            fl = BytesIO(download(s, url))
            _process(sess, log, set_progress, fl)
            laf_state[participant_code] = timestamp
            conf.update_state(state)
            sess.commit()

    log("Finished LAF files")
    sess.commit()
