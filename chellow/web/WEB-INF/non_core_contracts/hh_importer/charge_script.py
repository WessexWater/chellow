from net.sf.chellow.monad import Monad
import threading
import traceback
import datetime
import collections
import tempfile
import pytz
import ftplib
import os
import db
import utils
import socket

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, MarketRole = db.Contract, db.MarketRole
UserException = utils.UserException
socket.setdefaulttimeout(120)

processes = collections.defaultdict(list)
tasks = {}

extensions = ['.df2', '.simple.csv', '.bg.csv']


class HhDataImportProcess(threading.Thread):

    def __init__(
            self, hhdc_contract_id, process_id, istream, file_name, file_size):
        super(HhDataImportProcess, self).__init__(
            name="HH Manual Import: contract " + str(hhdc_contract_id))

        self.messages = []
        self.istream = istream
        self.hhdc_contract_id = hhdc_contract_id
        self.id = process_id
        if file_size == 0:
            raise UserException("File has zero length")

        file_name = file_name.lower()
        self.conv_ext = [ext for ext in extensions if file_name.endswith(ext)]
        if len(self.conv_ext) == 0:
            raise UserException(
                "The extension of the filename '" + file_name +
                "' is not one of the recognized extensions; " +
                str(extensions))
        self.converter = None

    def run(self):
        sess = None
        try:
            sess = db.session()
            contract = Contract.get_hhdc_by_id(sess, self.hhdc_contract_id)
            sess.rollback()
            properties = contract.make_properties()
            mpan_map = properties.get('mpan_map', {})
            parser_cont = Contract.get_non_core_by_name(
                sess, 'hh-parser-' + self.conv_ext[0][1:])

            gb = {}
            exec (parser_cont.charge_script, gb)
            create_parser = gb.get('create_parser')
            self.converter = create_parser(self.istream, mpan_map)
            sess.rollback()
            db.HhDatum.insert(sess, self.converter)
            sess.commit()
        except UserException, e:
            self.messages.append(str(e))
        except:
            self.messages.append("Outer problem " + traceback.format_exc())
        finally:
            if sess is not None:
                sess.rollback()
                sess.close()

    def get_status(self):
        return "No converter." \
            if self.converter is None else self.converter.get_status()


def get_hh_import_processes(contract_id):
    return processes[contract_id]


def start_hh_import_process(hhdc_contract_id, istream, file_name, file_size):
    contract_processes = get_hh_import_processes(hhdc_contract_id)
    id = len(contract_processes)
    process = HhDataImportProcess(
        hhdc_contract_id, id, istream, file_name, file_size)
    contract_processes.append(process)
    process.start()
    return process


class HhImportTask(threading.Thread):

    def __init__(self, contract_id):
        super(HhImportTask, self).__init__(
            name="HH Automatic Import: contract " + str(contract_id))
        self.lock = threading.RLock()
        self.messages = collections.deque()
        self.contract_id = contract_id
        self.importer = None
        self.stopped = threading.Event()
        self.going = threading.Event()

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
        self.messages.appendleft(datetime.datetime.utcnow().replace(
            tzinfo=pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    def get_status(self):
        return 'No importer.' \
            if self.importer is None else str(self.importer.get_status())

    def import_now(self):
        if self.lock.acquire(False):
            try:
                found_new = True
                while found_new:
                    found_new = False
                    sess = None
                    ftp = None

                    try:
                        sess = db.session()
                        contract = Contract.get_hhdc_by_id(
                            sess, self.contract_id)
                        properties = contract.make_properties()

                        host_name = properties["hostname"]
                        user_name = properties["username"]
                        password = properties["password"]
                        try:
                            port = properties["port"]
                        except KeyError:
                            port = 21
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
                            "Connecting to ftp server at " + host_name +
                            ":" + str(port) + ".")
                        ftp = ftplib.FTP()
                        ftp.connect(host_name, port)
                        ftp.login(user_name, password)
                        home_path = ftp.pwd()

                        file = None

                        for directory in directories:
                            self.log(
                                "Checking the directory '" + directory + "'.")
                            try:
                                last_import_key = last_import_keys[directory]
                            except KeyError:
                                last_import_key = ''
                                last_import_keys[directory] = last_import_key

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

                                key = ftp.sendcmd(
                                    "MDTM " + fpath).split()[1] + '_' + fname
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

                            self.log("Treating files as type " + file_type)
                            f.seek(0, os.SEEK_END)
                            fsize = f.tell()
                            f.seek(0)
                            self.importer = HhDataImportProcess(
                                self.contract_id, 0, f, fpath + file_type,
                                fsize)

                            self.importer.run()
                            messages = self.importer.messages
                            self.importer = None
                            for message in messages:
                                self.log(message)

                            if len(messages) > 0:
                                raise UserException("Problem loading file.")

                            db.set_read_write(sess)
                            contract = Contract.get_hhdc_by_id(
                                sess, self.contract_id)
                            contract.update_state(state)
                            sess.commit()
                            self.log("Finished loading '" + fpath)
                            found_new = True
                    except UserException, e:
                        self.log("Problem " + str(e))
                        sess.rollback()
                    except Exception:
                        self.log("Unknown Exception " + traceback.format_exc())
                        sess.rollback()
                    finally:
                        try:
                            if sess is not None:
                                sess.close()
                        except:
                            self.log(
                                "Unknown Exception II" +
                                traceback.format_exc())
            except Exception:
                self.log("Outer Exception " + traceback.format_exc())
            finally:
                self.lock.release()

    def run(self):
        while not self.stopped.isSet():
            self.import_now()
            self.going.wait(30 * 60)
            self.going.clear()


def get_hh_import_task(contract):
    return tasks.get(contract.id)


def startup_contract(contract_id):
    task = HhImportTask(contract_id)
    tasks[contract_id] = task
    task.start()


def startup():
    sess = None

    try:
        sess = db.session()
        for procs in processes.values():
            for proc in procs:
                if proc.isAlive():
                    raise UserException(
                        "Can't start hh importer, there are still some " +
                        "hh imports running.")

        for contract in sess.query(Contract).join(MarketRole).filter(
                MarketRole.code == 'C').order_by(Contract.id):
            startup_contract(contract.id)
    finally:
        if sess is not None:
            sess.close()


def shutdown():
    for procs in processes.values():
        for proc in procs:
            if proc.isAlive():
                raise UserException(
                    "Can't shut down hh importer, there are still some hh "
                    "imports running.")

    for task in tasks.values():
        task.stop()

    for id, task in tasks.iteritems():
        if task.isAlive():
            raise UserException(
                "Can't shut down hh importer, the task " + str(task) +
                " with id " + str(id) + " is still running.")
