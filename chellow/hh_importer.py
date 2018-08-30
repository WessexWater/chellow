import threading
import traceback
from collections import defaultdict, deque
import tempfile
import ftplib
import os
from chellow.models import Contract, MarketRole, Session, HhDatum, Era
from io import TextIOWrapper
from werkzeug.exceptions import BadRequest
import importlib
import atexit
import paramiko
import pysftp
from chellow.utils import (
    utc_datetime_now, utc_datetime, HH, hh_format, hh_min, hh_max)
from datetime import timedelta as Timedelta
from sqlalchemy import or_, null
import jinja2
import requests


processes = defaultdict(list)
tasks = {}

extensions = ['.df2', '.simple.csv', '.bg.csv']


class HhDataImportProcess(threading.Thread):

    def __init__(
            self, dc_contract_id, process_id, istream, file_name, file_size):
        super(HhDataImportProcess, self).__init__(
            name="HH Manual Import: contract " + str(dc_contract_id))

        self.messages = []
        self.istream = istream
        self.dc_contract_id = dc_contract_id
        self.id = process_id
        if file_size == 0:
            raise BadRequest("File has zero length")

        file_name = file_name.lower()
        self.conv_ext = [ext for ext in extensions if file_name.endswith(ext)]
        if len(self.conv_ext) == 0:
            raise BadRequest(
                "The extension of the filename '" + file_name +
                "' is not one of the recognized extensions; " +
                str(extensions))
        self.converter = None

    def run(self):
        sess = None
        try:
            sess = Session()
            contract = Contract.get_dc_by_id(sess, self.dc_contract_id)
            sess.rollback()
            properties = contract.make_properties()
            mpan_map = properties.get('mpan_map', {})
            parser_module = importlib.import_module(
                'chellow.hh_parser_' + self.conv_ext[0][1:].replace('.', '_'))
            self.converter = parser_module.create_parser(
                self.istream, mpan_map)
            sess.rollback()
            HhDatum.insert(sess, self.converter, contract)
            sess.commit()
        except BadRequest as e:
            self.messages.append(e.description)
        except BaseException:
            self.messages.append("Outer problem " + traceback.format_exc())
        finally:
            if sess is not None:
                sess.close()

    def get_status(self):
        return "No converter." \
            if self.converter is None else self.converter.get_status()


def get_hh_import_processes(contract_id):
    return processes[contract_id]


def start_hh_import_process(dc_contract_id, istream, file_name, file_size):
    contract_processes = get_hh_import_processes(dc_contract_id)
    id = len(contract_processes)
    process = HhDataImportProcess(
        dc_contract_id, id, istream, file_name, file_size)
    contract_processes.append(process)
    process.start()
    return process


class HhImportTask(threading.Thread):

    def __init__(self, contract_id):
        super(HhImportTask, self).__init__(
            name="HH Automatic Import: contract " + str(contract_id))
        self.lock = threading.RLock()
        self.messages = deque()
        self.contract_id = contract_id
        self.importer = None
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.is_error = False

    def stop(self):
        self.stopped.set()
        self.going.set()

    def go(self):
        self.going.set()

    def is_locked(self):
        if self.lock.acquire(False):
            self.lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    def get_status(self):
        return 'No importer.' \
            if self.importer is None else str(self.importer.get_status())

    def import_file(self, sess):
        found_new = False

        try:
            contract = Contract.get_dc_by_id(sess, self.contract_id)
            properties = contract.make_properties()
            enabled = properties["enabled"]
            if enabled:
                protocol = properties["protocol"]
                self.log("Protocol is " + protocol)
                if protocol == 'ftp':
                    found_new = self.ftp_handler(sess, properties, contract)
                elif protocol == 'sftp':
                    found_new = self.sftp_handler(sess, properties, contract)
                elif protocol == 'https':
                    found_new = self.https_handler(sess, properties, contract)
                else:
                    self.log("Protocol '" + protocol + "' not recognized.")
            else:
                self.log(
                    "Importer is disabled. To enable it, set " +
                    "the 'enabled' property to 'True'.")
            self.is_error = False
        except BadRequest as e:
            self.log("Problem " + str(e))
            sess.rollback()
            self.is_error = True
        except Exception:
            self.log("Unknown Exception " + traceback.format_exc())
            sess.rollback()
            self.is_error = True
        return found_new

    def import_now(self):
        if self.lock.acquire(False):
            sess = None
            try:
                sess = Session()
                while self.import_file(sess):
                    pass
            except Exception:
                self.log("Outer Exception " + traceback.format_exc())
                self.is_error = True
            finally:
                if sess is not None:
                    sess.close()
                self.lock.release()

    def run(self):
        while not self.stopped.isSet():
            self.import_now()
            self.going.wait(30 * 60)
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
        directories = properties['directories']
        state = contract.make_state()

        try:
            last_import_keys = state['last_import_keys']
        except KeyError:
            last_import_keys = {}
            state['last_import_keys'] = last_import_keys

        sess.rollback()
        self.log(
            "Connecting to ftp server at " + host_name + ":" + str(port) + ".")
        ftp = ftplib.FTP()
        if port is None:
            ftp.connect(host=host_name, timeout=120)
        else:
            ftp.connect(host=host_name, port=port, timeout=120)

        ftp.login(user_name, password)
        home_path = ftp.pwd()

        file = None

        for directory in directories:
            self.log(
                "Checking the directory '" +
                directory + "'.")
            try:
                last_import_key = last_import_keys[directory]
            except KeyError:
                last_import_key = last_import_keys[directory] = ''

            dir_path = home_path + "/" + directory
            ftp.cwd(dir_path)
            files = []
            for fname in ftp.nlst():
                fpath = dir_path + "/" + fname
                try:
                    ftp.cwd(fpath)
                    continue  # directory
                except ftplib.error_perm:
                    pass

                key = ftp.sendcmd("MDTM " + fpath).split()[1] + '_' + fname
                if key > last_import_key:
                    files.append((key, fpath))

            if len(files) > 0:
                file = sorted(files)[0]
                last_import_keys[directory] = file[0]
                break

        if file is None:
            self.log("No new files found.")
            ftp.quit()
            self.log("Logged out.")
            return False
        else:
            key, fpath = file
            self.log(
                "Attempting to download " + fpath +
                " with key " + key + ".")
            f = tempfile.TemporaryFile()
            ftp.retrbinary("RETR " + fpath, f.write)
            self.log("File downloaded successfully.")
            ftp.quit()
            self.log("Logged out.")

            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            f.seek(0)
            self.log("File size is " + str(fsize) + " bytes.")
            self.log(
                "Treating files as type " + file_type)
            self.importer = HhDataImportProcess(
                self.contract_id, 0, TextIOWrapper(f, 'utf8'),
                fpath + file_type, fsize)

            self.importer.run()
            for message in self.importer.messages:
                self.log(message)

            if len(self.importer.messages) > 0:
                raise BadRequest("Problem loading file.")

            contract = Contract.get_dc_by_id(sess, self.contract_id)
            contract.update_state(state)
            sess.commit()
            self.log("Finished loading '" + fpath)
            return True

    def sftp_handler(self, sess, properties, contract):
        host_name = properties["hostname"]
        user_name = properties["username"]
        password = properties["password"]
        try:
            port = properties["port"]
        except KeyError:
            port = None
        file_type = properties["file_type"]
        directories = properties['directories']
        state = contract.make_state()

        try:
            last_import_keys = state['last_import_keys']
        except KeyError:
            last_import_keys = state['last_import_keys'] = {}

        sess.rollback()
        self.log(
            "Connecting to sftp server at " + host_name + ":" +
            str(port) + ".")
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        ftp = pysftp.Connection(
            host_name, username=user_name, password=password, cnopts=cnopts)
        ftp.timeout = 120
        home_path = ftp.pwd

        f = None

        for directory in directories:
            self.log(
                "Checking the directory '" +
                directory + "'.")
            try:
                last_import_key = last_import_keys[directory]
            except KeyError:
                last_import_key = last_import_keys[directory] = ''

            dir_path = home_path + "/" + directory
            ftp.cwd(dir_path)
            files = []
            for attr in ftp.listdir_attr():
                fpath = dir_path + "/" + attr.filename
                try:
                    ftp.cwd(fpath)
                    continue  # directory
                except paramiko.SFTPError:
                    pass

                key = str(attr.st_mtime) + '_' + attr.filename
                if key > last_import_key:
                    files.append((key, fpath))

            if len(files) > 0:
                f = sorted(files)[0]
                last_import_keys[directory] = f[0]
                break

        if f is None:
            self.log("No new files found.")
            ftp.close()
            self.log("Logged out.")
            return False
        else:
            key, fpath = f
            self.log(
                "Attempting to download " + fpath + " with key " + key + ".")
            f = tempfile.TemporaryFile()
            ftp.getfo(fpath, f)
            self.log("File downloaded successfully.")
            ftp.close()
            self.log("Logged out.")

            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            f.seek(0)
            self.log("File size is " + str(fsize) + " bytes.")
            self.log("Treating files as type " + file_type)
            self.importer = HhDataImportProcess(
                self.contract_id, 0, TextIOWrapper(f, 'utf8'),
                fpath + file_type, fsize)

            self.importer.run()
            messages = self.importer.messages
            self.importer = None
            for message in messages:
                self.log(message)

            if len(messages) > 0:
                raise BadRequest("Problem loading file.")

            contract = Contract.get_dc_by_id(sess, self.contract_id)
            contract.update_state(state)
            sess.commit()
            self.log("Finished loading '" + fpath)
            return True

    def https_handler(self, sess, properties, contract):
        url_template_str = properties['url_template']
        url_values = properties.get('url_values', {})
        download_days = properties['download_days']
        now = utc_datetime_now()
        window_finish = utc_datetime(now.year, now.month, now.day) - HH
        window_start = utc_datetime(
            now.year, now.month, now.day) - Timedelta(days=download_days)
        self.log("Window start: " + hh_format(window_start))
        self.log("Window finish: " + hh_format(window_finish))
        env = jinja2.Environment(
            autoescape=True, undefined=jinja2.StrictUndefined)
        url_template = env.from_string(url_template_str)
        for era in sess.query(Era).filter(
                Era.dc_contract == contract,
                Era.start_date <= window_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= window_start)).distinct():
            chunk_start = hh_max(era.start_date, window_start)
            chunk_finish = hh_min(era.finish_date, window_finish)
            if era.imp_mpan_core is None:
                mpan_core = era.exp_mpan_core
            else:
                mpan_core = era.imp_mpan_core

            self.log(
                "Looking at MPAN core {mpan_core}.".format(
                    mpan_core=mpan_core))

            vals = {
                'chunk_start': chunk_start,
                'chunk_finish': chunk_finish}
            vals.update(url_values.get(mpan_core, {}))
            try:
                url = url_template.render(vals)
            except jinja2.exceptions.UndefinedError as e:
                raise BadRequest(
                    "Problem rendering the URL template: " + url_template_str +
                    ". The problem is: " + str(e) + ". This can be fixed by " +
                    "editing the properties of this contract.")

            self.log("Retrieving data from {url}.".format(url=url))
            res = requests.get(url)
            res.raise_for_status()
            result = requests.get(url).json()
            if isinstance(result, dict):
                result_data = result['DataPoints']
            elif isinstance(result, list):
                result_data = result
            else:
                raise BadRequest(
                    "Expecting a JSON object at the top level, but instead " +
                    "got " + str(result))
            raw_data = []
            for jdatum in result_data:
                raw_data.append(
                    dict(
                        mpan_core=mpan_core,
                        start_date=utc_datetime(1, 1, 1) + Timedelta(
                            seconds=jdatum['Time'] / 10000000),
                        channel_type='ACTIVE',
                        value=jdatum['Value'],
                        status='A'))
            HhDatum.insert(sess, raw_data, contract)
            sess.commit()
        self.log("Finished loading.")
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
            if proc.isAlive():
                raise BadRequest(
                    "Can't start hh importer, there are still some " +
                    "hh imports running.")

    sess = None
    try:
        sess = Session()
        for contract in sess.query(Contract).join(MarketRole).filter(
                MarketRole.code == 'C').order_by(Contract.id):
            startup_contract(contract.id)
    finally:
        if sess is not None:
            sess.close()


@atexit.register
def shutdown():
    for task in tasks.values():
        task.stop()

    for task in tasks.values():
        task.join()

    for procs in processes.values():
        for proc in procs:
            proc.join()
