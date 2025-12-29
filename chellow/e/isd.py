import atexit
import collections
import csv
import threading
import traceback
from datetime import datetime as Datetime, timedelta
from io import StringIO

import requests

from sqlalchemy import select

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Contract,
    MarketRole,
    Party,
    Session,
)
from chellow.utils import ct_datetime_now, hh_format, utc_datetime_now


importer = None

# https://bscdocs.elexon.co.uk/guidance-notes/isd-data-store-technical-specification

"""
def db_upgrade_52_to_53(sess, root_path):
    sess.execute(text("ALTER TABLE party ADD code CHARACTER VARYING;"))
    sess.execute(text("UPDATE party SET code = (name || cast(id as text));"))
    sess.execute(text("ALTER TABLE party ALTER code SET NOT NULL;"))
    sess.execute(
        text(
            "ALTER TABLE party ADD CONSTRAINT code_valid_from_key "
            "UNIQUE (code, valid_from);"
        )
    )

    sess.execute(text("ALTER TABLE market_role ADD mdd_code VARCHAR(4);"))
    sess.execute(text("UPDATE market_role SET mdd_code = code"))
    sess.execute(text("ALTER TABLE market_role ALTER COLUMN code TYPE VARCHAR(4);"))
"""


def _fetch_csv(s, entity_id):
    url = "https://datastore.helix.elexon.co.uk/api/ISD"
    params = {"filter": entity_id}
    res = s.get(url, params=params)
    res.raise_for_status()

    csv_file = StringIO(res.text)

    reader = csv.reader(csv_file)
    eid, entity_name, version_str, changed = next(reader)
    next(reader)
    assert entity_id == eid
    version = int(version_str)
    return reader, version


def _process_MarketRole(sess, log, reader):
    # DIP Market Role
    # DIP Role Description
    # Market Participant Role Code
    # Effective From Date {DIPRole}
    # Effective To Date {DIPRole}

    for values in reader:
        code = values[0]
        description = values[1]
        mdd_code = values[2]
        from_date_str = values[3]
        from_date = Datetime.fromisoformat(from_date_str)
        to_date_str = values[4]
        if to_date_str != "":
            raise BadRequest("Mapping finished")

        role = MarketRole.find_by_code(sess, code, from_date)
        if role is None:
            role = sess.scalars(
                select(MarketRole).where(MarketRole.mdd_code == mdd_code)
            ).one_or_none()
            if role is None:
                role = MarketRole.insert(sess, code, description, from_date, None)
            else:
                role.code = code
                sess.flush()
        else:
            if role.description != description:
                role.description = description
                sess.flush()


def _process_Party(sess, log, reader):
    # Market Participant ID String (4) Y
    # Market Participant Role Code String (1) N
    # DIP Participant ID String (10) Y
    # DIP Role Code String (5) Y
    # Effective From Date {MP2DPM} Date Y
    # Effective To Date {MP2DPM} Date N
    # Changed Int N

    for values in reader:
        participant_code = values[0]
        market_role_code = values[1]
        party_code = values[2]
        from_date_str = values[4]
        from_date = Datetime.fromisoformat(from_date_str)
        to_date_str = values[5]
        if to_date_str != "":
            raise BadRequest("Mapping finished")
        party = Party.get_by_participant_code_role_code(
            sess, participant_code, market_role_code, from_date
        )
        if party.code != party_code:
            log(f"Updating {party.code} with {party_code}.")


ENTITY_FUNCS = {
    "ISDEntityM18": _process_MarketRole,
    "ISDEntityM16": _process_Party,
}


def run_import(sess, log, set_progress, cur_version, s):
    log("Starting to import the ISD from Elexon Helix")
    version = 0
    return version
    for entity_code in ("ISDEntityM18", "ISDEntityM16"):
        reader, version = _fetch_csv(s, entity_code)
        if cur_version >= version:
            return cur_version
        ENTITY_FUNCS[entity_code](sess, log, reader)
    rows = [
        [
            "CIDC",
            "R",
            "01/01/2000",
            "",
            "Virtual",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "88",
        ],
        [
            "CROW",
            "R",
            "01/04/1996",
            "",
            "Non-settlement",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "99",
        ],
    ]
    _process_Party(sess, rows)

    return version


GLOBAL_ALERT = "There's a problem with an <a href='/e/isd'>ISD import</a>."
ISD_STATE_KEY = "isd"
LAST_RUN_KEY = "last_run"
VERSION_KEY = "version"
DELAY_DAYS = 1


class Isd(threading.Thread):
    def __init__(self):
        super().__init__(name="Industry Standing Data")
        self.messages = collections.deque(maxlen=500)
        self.progress = ""
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.global_alert = None

    def stop(self):
        self.stopped.set()
        self.going.set()
        self.join()

    def go(self):
        self.going.set()

    def log(self, message):
        self.messages.appendleft(
            f"{ct_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        )

    def set_progress(self, progress):
        self.progress = progress

    def run(self):
        while not self.stopped.is_set():
            with Session() as sess:
                try:
                    config = Contract.get_non_core_by_name(sess, "configuration")
                    state = config.make_state()
                    isd_state = state.get(ISD_STATE_KEY, {})
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = GLOBAL_ALERT
                    sess.rollback()

            last_run = isd_state.get(LAST_RUN_KEY)
            if last_run is None or utc_datetime_now() - last_run > timedelta(
                days=DELAY_DAYS
            ):
                self.going.set()

            if self.going.is_set():
                self.global_alert = None
                with Session() as sess:
                    try:
                        config = Contract.get_non_core_by_name(sess, "configuration")
                        state = config.make_state()
                        try:
                            isd_state = state[ISD_STATE_KEY]
                        except KeyError:
                            isd_state = state[ISD_STATE_KEY] = {}

                        isd_state[LAST_RUN_KEY] = utc_datetime_now()
                        config.update_state(state)
                        sess.commit()
                        version = isd_state.get("version", 0)
                        s = requests.Session()
                        s.headers.update({"User-Agent": "Chellow"})

                        new_version = run_import(
                            sess, self.log, self.set_progress, version, s
                        )
                        isd_state["version"] = new_version
                        config.update_state(state)
                        sess.commit()
                    except BaseException as e:
                        msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                        self.log(f"{msg}{traceback.format_exc()}")
                        self.global_alert = GLOBAL_ALERT
                        sess.rollback()
                    finally:
                        self.going.clear()
                        self.log("Finished importing ISD.")

            else:
                self.log(
                    f"The importer was last run at {hh_format(last_run)}. There will "
                    f"be another import when {DELAY_DAYS} days have elapsed since the "
                    f"last run."
                )
                self.going.wait(60 * 60)


def get_importer():
    return importer


def startup():
    global importer
    importer = Isd()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
