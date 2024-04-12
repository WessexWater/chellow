import atexit
import ftplib
import importlib
import os
import tempfile
import threading
import traceback
from collections import defaultdict, deque
from datetime import datetime as Datetime, timedelta as Timedelta
from decimal import Decimal
from io import StringIO, TextIOWrapper
from pathlib import Path

import jinja2

from paramiko import AutoAddPolicy, RSAKey, SFTPError, SSHClient


import requests

from sqlalchemy import null, or_

from werkzeug.exceptions import BadRequest

from chellow.models import Contract, Era, HhDatum, MarketRole, Session
from chellow.utils import (
    HH,
    ct_datetime,
    ct_datetime_now,
    hh_format,
    hh_max,
    hh_min,
    to_ct,
    to_utc,
    utc_datetime,
    utc_datetime_now,
)


processes = defaultdict(list)
tasks = {}

extensions = [".df2", ".simple.csv", ".bg.csv"]


class HhDataImportProcess(threading.Thread):
    def __init__(self, dc_contract_id, process_id, istream, file_name, file_size):
        super().__init__(name=f"HH Manual Import: contract {dc_contract_id}")

        self.messages = []
        self.error = None
        self.istream = istream
        self.dc_contract_id = dc_contract_id
        self.id = process_id
        if file_size == 0:
            raise BadRequest("File has zero length")

        file_name = file_name.lower()
        self.conv_ext = [ext for ext in extensions if file_name.endswith(ext)]
        if len(self.conv_ext) == 0:
            raise BadRequest(
                f"The extension of the filename '{file_name}' is not one of the "
                f"recognized extensions; {extensions}"
            )
        self.converter = None

    def run(self):
        with Session() as sess:
            try:
                contract = Contract.get_dc_by_id(sess, self.dc_contract_id)
                sess.rollback()
                properties = contract.make_properties()
                mpan_map = properties.get("mpan_map", {})
                mod_name = self.conv_ext[0][1:].replace(".", "_")
                parser_module = importlib.import_module(
                    f"chellow.e.hh_parser_{mod_name}"
                )
                self.converter = parser_module.create_parser(
                    self.istream, mpan_map, self.messages
                )
                sess.rollback()
                HhDatum.insert(sess, self.converter, contract)
                sess.commit()
            except BadRequest as e:
                self.error = e.description
            except BaseException:
                self.error = f"Outer problem {traceback.format_exc()}"

    def get_status(self):
        return (
            "No converter." if self.converter is None else self.converter.get_status()
        )


def get_hh_import_processes(contract_id):
    return processes[contract_id]


def start_hh_import_process(dc_contract_id, istream, file_name, file_size):
    contract_processes = get_hh_import_processes(dc_contract_id)
    id = len(contract_processes)
    process = HhDataImportProcess(dc_contract_id, id, istream, file_name, file_size)
    contract_processes.append(process)
    process.start()
    return process


lock = threading.RLock()


class HhImportTask(threading.Thread):
    def __init__(self, contract_id):
        super().__init__(name=f"HH Automatic Import: contract {contract_id}")
        self.messages = deque()
        self.contract_id = contract_id
        self.importer = None
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.is_error = False
        self.wait_seconds = 30 * 60

    def stop(self):
        self.stopped.set()
        self.going.set()

    def go(self):
        self.going.set()

    def is_locked(self):
        if lock.acquire(False):
            lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        )
        if len(self.messages) > 100:
            self.messages.pop()

    def get_status(self):
        return (
            "No importer." if self.importer is None else str(self.importer.get_status())
        )

    def import_file(self, sess):
        found_new = False

        try:
            contract = Contract.get_dc_by_id(sess, self.contract_id)
            properties = contract.make_properties()
            enabled = properties["enabled"]
            if enabled:
                protocol = properties["protocol"]
                self.log("Protocol is " + protocol)
                if protocol == "ftp":
                    found_new = self.ftp_handler(sess, properties, contract)
                elif protocol == "sftp":
                    found_new = self.sftp_handler(sess, properties, contract)
                elif protocol == "https":
                    found_new = https_handler(sess, self.log, properties, contract)
                else:
                    self.log(f"Protocol '{protocol}' not recognized.")
                self.wait_seconds = properties.get("check_minutes", 30) * 60
            else:
                self.log(
                    "Importer is disabled. To enable it, set the 'enabled' property "
                    "to 'True'."
                )
            self.is_error = False
        except BadRequest as e:
            self.log(f"Problem {e}")
            sess.rollback()
            self.is_error = True
        except BaseException:
            self.log(f"Unknown Exception {traceback.format_exc()}")
            sess.rollback()
            self.is_error = True
        return found_new

    def import_now(self):
        if lock.acquire(False):
            with Session() as sess:
                try:
                    while self.import_file(sess):
                        pass
                except Exception:
                    self.log(f"Outer Exception {traceback.format_exc()}")
                    self.is_error = True
                finally:
                    lock.release()

    def run(self):
        while not self.stopped.isSet():
            self.import_now()
            timeout = None if self.is_error else self.wait_seconds
            self.going.wait(timeout=timeout)
            self.going.clear()

    def ftp_handler(self, sess, properties, contract):
        host_name = properties["hostname"]
        user_name = properties["username"]
        password = properties["password"]
        try:
            port = properties["port"]
        except KeyError:
            port = None
        file_type = properties["file_type"]
        directories = properties["directories"]
        state = contract.make_state()

        try:
            last_import_keys = state["last_import_keys"]
        except KeyError:
            last_import_keys = {}
            state["last_import_keys"] = last_import_keys

        sess.rollback()
        self.log(f"Connecting to ftp server at {host_name}:{port}.")
        ftp = ftplib.FTP()
        if port is None:
            ftp.connect(host=host_name, timeout=120)
        else:
            ftp.connect(host=host_name, port=port, timeout=120)

        ftp.login(user_name, password)
        home_path = ftp.pwd()

        fl = None

        for directory in directories:
            self.log(f"Checking the directory '{directory}'.")
            try:
                last_import_key = last_import_keys[directory]
            except KeyError:
                last_import_key = last_import_keys[directory] = ""

            dir_path = home_path + "/" + directory
            ftp.chdir(dir_path)
            files = []
            for fname in ftp.listdir():
                fpath = dir_path + "/" + fname
                try:
                    ftp.chdir(fpath)
                    continue  # directory
                except ftplib.error_perm:
                    pass

                key = ftp.sendcmd("MDTM " + fpath).split()[1] + "_" + fname
                if key > last_import_key:
                    files.append((key, fpath))

            if len(files) > 0:
                fl = sorted(files)[0]
                last_import_keys[directory] = fl[0]
                break

        if fl is None:
            self.log("No new files found.")
            ftp.quit()
            self.log("Logged out.")
            return False
        else:
            key, fpath = fl
            self.log(f"Attempting to download {fpath} with key {key}.")
            f = tempfile.TemporaryFile()
            ftp.retrbinary(f"RETR {fpath}", f.write)
            self.log("File downloaded successfully.")
            ftp.quit()
            self.log("Logged out.")

            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            f.seek(0)
            self.log(f"File size is {fsize} bytes.")
            self.log(f"Treating files as type {file_type}")
            self.importer = HhDataImportProcess(
                self.contract_id, 0, TextIOWrapper(f, "utf8"), fpath + file_type, fsize
            )

            self.importer.run()
            for message in self.importer.messages:
                self.log(message)

            if self.importer.error is not None:
                raise BadRequest(f"Problem loading file. {self.importer.error}")

            contract = Contract.get_dc_by_id(sess, self.contract_id)
            contract.update_state(state)
            sess.commit()
            self.log(f"Finished loading '{fpath}'")
            return True

    def sftp_handler(self, sess, properties, contract):
        hostname = properties["hostname"]
        username = properties["username"]
        password = properties.get("password")
        private_key = properties.get("private_key")
        pkey = None
        if private_key is not None:
            pkf = StringIO(private_key)
            pkf.seek(0)
            pkey = RSAKey.from_private_key(pkf)

        port = properties.get("port", 22)
        file_type = properties["file_type"]
        directories = properties["directories"]
        known_hosts = properties["known_hosts"].strip()
        state = contract.make_state()

        try:
            last_import_keys = state["last_import_keys"]
        except KeyError:
            last_import_keys = state["last_import_keys"] = {}

        ct_now = ct_datetime_now()
        try:
            latest_imports = [
                (dt, fname)
                for dt, fname in state["latest_imports"]
                if (to_ct(dt).year, to_ct(dt).month, to_ct(dt).day)
                == (ct_now.year, ct_now.month, ct_now.day)
            ]
            state["latest_imports"] = latest_imports
        except KeyError:
            latest_imports = state["latest_imports"] = []

        sess.rollback()
        self.log(f"Connecting to sftp server at {hostname}:{port}.")

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy)

        client.connect(
            hostname,
            port=port,
            username=username,
            password=password,
            pkey=pkey,
            key_filename=None,
            timeout=120,
            banner_timeout=120,
            auth_timeout=120,
            channel_timeout=120,
            look_for_keys=False,
        )
        host_keys = client.get_host_keys()
        with tempfile.TemporaryDirectory() as tempdir:
            td = Path(tempdir)
            hfname = td / "hosts"
            host_keys.save(hfname)
            with hfname.open() as hf:
                host_keys_str = hf.read().strip()

        if host_keys_str != known_hosts:
            raise BadRequest(
                f"The returned host keys {host_keys_str} don't match the known "
                f"hosts {known_hosts} property"
            )

        ftp = client.open_sftp()

        f = None

        for directory in directories:
            self.log(f"Checking the directory '{directory}'.")
            try:
                last_import_key = last_import_keys[directory]
            except KeyError:
                last_import_key = last_import_keys[directory] = ""

            ftp.chdir(directory)
            files = []
            for attr in ftp.listdir_attr():
                fpath = f"{directory}/{attr.filename}"
                try:
                    ftp.chdir(fpath)
                    continue  # directory
                except SFTPError:
                    pass

                key = f"{attr.st_mtime}_{attr.filename}"
                if key > last_import_key:
                    files.append((key, fpath))

            if len(files) > 0:
                f = sorted(files)[0]
                last_import_keys[directory] = f[0]
                break

        if f is None:
            self.log("No new files found.")
            ftp.close()
            client.close()
            self.log("Logged out.")
            return False
        else:
            key, fpath = f
            latest_imports.append((utc_datetime_now(), fpath))
            self.log(f"Attempting to download {fpath} with key {key}.")
            f = tempfile.TemporaryFile()
            ftp.getfo(fpath, f)
            self.log("File downloaded successfully.")
            ftp.close()
            self.log("Logged out.")

            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            f.seek(0)
            self.log(f"File size is {fsize} bytes.")
            self.log(f"Treating files as type {file_type}")
            self.importer = HhDataImportProcess(
                self.contract_id, 0, TextIOWrapper(f, "utf8"), fpath + file_type, fsize
            )

            self.importer.run()
            messages = self.importer.messages
            for message in messages:
                self.log(message)

            if self.importer.error is not None:
                raise BadRequest(f"Problem loading file. {self.importer.error}")
            self.importer = None

            contract = Contract.get_dc_by_id(sess, self.contract_id)
            contract.update_state(state)
            sess.commit()
            self.log(f"Finished loading '{fpath}'")
            return True


def meniscus_parser(log_f, result, properties, mpan_core):
    if isinstance(result, dict):
        result_data = result["Data"]
    elif isinstance(result, list):
        result_data = result
    else:
        raise BadRequest(
            f"Expecting a JSON object at the top level, but instead got {result}"
        )
    raw_data = []
    for jdatum in result_data:
        raw_data.append(
            dict(
                mpan_core=mpan_core,
                start_date=utc_datetime(1, 1, 1)
                + Timedelta(seconds=jdatum["Time"] / 10000000),
                channel_type="ACTIVE",
                value=jdatum["Value"],
                status="A",
            )
        )
    return raw_data


def solaredge_meters_parser(log_f, result, properties, mpan_core):
    meters = result["meterEnergyDetails"]["meters"]
    meter = None
    if mpan_core in properties["generated_mpan_cores"]:
        meter_type = "FeedIn"
    elif mpan_core in properties["parasitic_mpan_cores"]:
        meter_type = "Purchased"
    else:
        raise BadRequest(
            f"Can't find the MPAN core {mpan_core} in either the generated_mpan_cores "
            f"or parasitic_mpan_cores lists in the DC properties."
        )
    for m in meters:
        if m["meterType"] == meter_type:
            meter = m
            break

    if meter is None:
        raise BadRequest(
            f"Can't find the meter type '{meter_type}' in the list of meters."
        )

    raw_data = {}
    prev_read = None
    for val in meter["values"]:
        if "value" in val:
            d_ct = to_ct(Datetime.strptime(val["date"], "%Y-%m-%d %H:%M:%S"))
            read = Decimal(val["value"])
            if prev_read is not None:
                value = (read - prev_read) / Decimal("1000")
                if d_ct.minute > 30:
                    date_ct_minute = 30
                else:
                    date_ct_minute = 0

                date_ct = ct_datetime(
                    d_ct.year, d_ct.month, d_ct.day, d_ct.hour, date_ct_minute
                )

                try:
                    raw_datum = raw_data[date_ct]
                except KeyError:
                    raw_datum = raw_data[date_ct] = {
                        "mpan_core": mpan_core,
                        "start_date": to_utc(date_ct),
                        "channel_type": "ACTIVE",
                        "value": Decimal(0),
                        "status": "A",
                    }

                raw_datum["value"] += value
            prev_read = read

    return [v for _, v in sorted(raw_data.items())]


def solaredge_energy_details_parser(log_f, result, properties, mpan_core):
    meters = result["energyDetails"]["meters"]
    meter = None
    if mpan_core in properties["generated_mpan_cores"]:
        meter_key = "Production"
    elif mpan_core in properties["parasitic_mpan_cores"]:
        meter_key = "Consumption"
    else:
        raise BadRequest(
            f"Can't find the MPAN core {mpan_core} in either the generated_mpan_cores "
            f"or parasitic_mpan_cores lists in the DC properties."
        )
    for m in meters:
        if m["type"] == meter_key:
            meter = m
            break

    if meter is None:
        raise BadRequest(
            f"Can't find the meter type '{meter_key}' in the list of meters."
        )

    raw_data = []
    for val in meter["values"]:
        if "value" in val:
            date_ct = to_ct(Datetime.strptime(val["date"], "%Y-%m-%d %H:%M:%S"))
            value = Decimal(val["value"]) / Decimal("1000")
            if date_ct.minute in (0, 30):
                raw_data.append(
                    {
                        "mpan_core": mpan_core,
                        "start_date": to_utc(date_ct),
                        "channel_type": "ACTIVE",
                        "value": value,
                        "status": "A",
                    }
                )
            elif len(raw_data) > 0:
                raw_data[-1]["value"] += value

    return raw_data


PARSERS = {
    "meniscus": meniscus_parser,
    "solaredge_energy_details": solaredge_energy_details_parser,
    "solaredge_meters": solaredge_meters_parser,
}


def https_handler(sess, log_f, properties, contract, now=None):
    url_template_str = properties["url_template"]
    url_values = properties.get("url_values", {})
    download_days = properties["download_days"]
    parser_name = properties["parser"]

    if now is None:
        now = utc_datetime_now()
    window_finish = utc_datetime(now.year, now.month, now.day) - HH
    window_start = utc_datetime(now.year, now.month, now.day) - Timedelta(
        days=download_days
    )
    log_f(f"Window start: {hh_format(window_start)}")
    log_f(f"Window finish: {hh_format(window_finish)}")
    env = jinja2.Environment(autoescape=True, undefined=jinja2.StrictUndefined)
    url_template = env.from_string(url_template_str)
    for era in (
        sess.query(Era)
        .filter(
            Era.dc_contract == contract,
            Era.start_date <= window_finish,
            or_(Era.finish_date == null(), Era.finish_date >= window_start),
        )
        .distinct()
    ):
        chunk_start = hh_max(era.start_date, window_start)
        chunk_finish = hh_min(era.finish_date, window_finish)
        for mpan_core in (era.imp_mpan_core, era.exp_mpan_core):
            if mpan_core is None:
                continue

            log_f(f"Looking at MPAN core {mpan_core}.")

            vals = {"chunk_start": chunk_start, "chunk_finish": chunk_finish}
            vals.update(url_values.get(mpan_core, {}))
            try:
                url = url_template.render(vals)
            except jinja2.exceptions.UndefinedError as e:
                raise BadRequest(
                    f"Problem rendering the URL template: {url_template_str}. "
                    f"The problem is: {e}. This can be fixed by editing the "
                    f"properties of this contract."
                )

            log_f(f"Retrieving data from {url}.")

            sess.rollback()  # Avoid long transactions

            s = requests.Session()
            s.verify = False
            res = s.get(url, timeout=120)
            res.raise_for_status()

            raw_data = PARSERS[parser_name](log_f, res.json(), properties, mpan_core)
            HhDatum.insert(sess, raw_data, contract)
            sess.commit()
    log_f("Finished loading.")
    return False


def get_hh_import_task(contract):
    return tasks.get(contract.id)


def startup_contract(contract_id):
    task = HhImportTask(contract_id)
    tasks[contract_id] = task
    task.start()


def startup():
    for procs in processes.values():
        for proc in procs:
            if proc.is_alive():
                raise BadRequest(
                    "Can't start hh importer, there are still some hh imports running."
                )

    with Session() as sess:
        for contract in (
            sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == "C")
            .order_by(Contract.id)
        ):
            startup_contract(contract.id)


@atexit.register
def shutdown():
    for task in tasks.values():
        task.stop()

    for task in tasks.values():
        task.join()

    for procs in processes.values():
        for proc in procs:
            proc.join()
