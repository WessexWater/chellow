from net.sf.chellow.monad import Monad
from java.lang import System
import threading
import traceback
import csv
import datetime
import collections
import decimal
import tempfile
import dateutil
import dateutil.parser
import pytz
from sqlalchemy import or_
import datetime
from org.apache.commons.net.ftp import FTPClient, FTPFile, FTPReply
import StringIO
from java.io import InputStreamReader, BufferedReader


Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write', 'Site', 'Supply', 'Source', 'GeneratorType', 'GspGroup', 'Pc', 'Cop', 'Era', 'Mtc', 'Ssc', 'HhDatum', 'Snag', 'BillType', 'Tpr', 'ReadType', 'MarketRole'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'parse_hh_start', 'get_contract_func'],
        'templater': ['render']})

processes = collections.defaultdict(list)
tasks = {}

extensions = ['.df2', '.simple.csv', '.bg.csv']

class HhDataImportProcess(threading.Thread):

    def __init__(self, hhdc_contract_id, process_id, istream, file_name, file_size):
        super(HhDataImportProcess, self).__init__()
        self.messages = []
        self.istream = istream
        self.hhdc_contract_id = hhdc_contract_id
        self.id = process_id
        if file_size == 0:
            raise UserException("File has zero length")

        file_name = file_name.lower();
        self.conv_ext = [ext for ext in extensions if file_name.endswith(ext)]
        if len(self.conv_ext) == 0:
            raise UserException("The extension of the filename '" + file_name + "' is not one of the recognized extensions; " + str(extensions))

    def run(self):
        sess = None
        try:
            sess = session()
            contract = Contract.get_hhdc_by_id(sess, self.hhdc_contract_id)
            sess.rollback()
            properties = contract.make_properties()
            mpan_map = properties.get('mpan_map', {})
            parser_cont = Contract.get_non_core_by_name(sess, 'hh-parser-' + self.conv_ext[0][1:])

            gb = {}
            exec (parser_cont.charge_script, gb)
            create_parser = gb.get('create_parser')
            self.converter = create_parser(self.istream, mpan_map)
            sess.rollback()
            HhDatum.insert(sess, self.converter)
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
        return "No converter." if self.converter is None else self.converter.get_status()

def get_hh_import_processes(contract_id):
    return processes[contract_id]

def start_hh_import_process(hhdc_contract_id, istream, file_name, file_size):
    contract_processes = get_hh_import_processes(hhdc_contract_id)
    id = len(contract_processes)
    process = HhDataImportProcess(hhdc_contract_id, id, istream, file_name, file_size)
    contract_processes.append(process)
    process.start()
    return process



class HhImportTask(threading.Thread):

    def __init__(self, contract_id):
        super(HhImportTask, self).__init__()
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
        self.messages.appendleft(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    def get_status(self):
        return 'No importer.' if self.importer is None else str(self.importer.get_status())

    def import_now(self):
        if self.lock.acquire(False):
            try:
                found_new = True
                while found_new:
                    found_new = False
                    sess = None
                    ftp = None

                    try:
                        sess = session()
                        contract = Contract.get_hhdc_by_id(sess, self.contract_id)
                        properties = contract.make_properties()
                        
                        host_name = properties["hostname"]
                        user_name = properties["username"]
                        password = properties["password"]
                        file_type = properties["file_type"]
                        directories = properties['directories']
                        state = contract.make_state()

                        if 'last_import_keys' not in state:
                            state['last_import_keys'] = {}

                        last_import_keys = state['last_import_keys']
                        sess.rollback()
                        ftp = FTPClient()
                        ftp.setDataTimeout(1000 * 60)
                        ftp.connect(host_name)
                        self.log("Connecting to ftp server at " + host_name + ".")
                        self.log("Server replied with '" + ftp.getReplyString() + "'.")
                        reply = ftp.getReplyCode()

                        if not FTPReply.isPositiveCompletion(reply):
                            raise UserException("FTP server refused connection.")

                        self.log("Connected to server, now logging in.")
                        ftp.login(user_name, password)
                        self.log("Server replied with '" + ftp.getReplyString() + "'.")
                        file_name = None

                        for directory in directories:
                            if directory not in last_import_keys:
                                last_import_keys[directory] = unicode('')

                            last_import_key = last_import_keys[directory] 
                            self.log("Checking the directory '" + directory + "'.")

                            files = [(datetime.datetime.fromtimestamp(file.getTimestamp().getTime().getTime() / 1000, pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + "_" + file.getName(), file) for file in ftp.listFiles(directory) if file.getType() == FTPFile.FILE_TYPE]
                            files = [(key, file) for key, file in files if key > last_import_key]

                            for key, file in sorted(files):
                                fname = directory + "/" + file.getName()

                                if file.getSize() == 0:
                                    self.log("Ignoring '" + fname + "'because it has zero length")
                                    continue

                                file_name = fname
                                break

                            if file_name is not None:
                                break

                        if file_name is None:
                            self.log("No new files found.")
                            ftp.logout()
                            self.log("Logged out.")
                            ftp.disconnect()
                            self.log("Disconnected.")
                        else:
                            self.log("Attempting to download '" + file_name
+ "'.")
                            istr = ftp.retrieveFileStream(file_name)
                            if istr is None:
                                reply = ftp.getReplyCode()
                                raise UserException("Can't download the file '" + file.getName() + "', server says: " + str(reply) + ".")
                            self.log("File stream obtained successfully.")
                            stream = BufferedReader(InputStreamReader(istr, 'utf-8'))
                            f = tempfile.TemporaryFile()
                            ln = stream.readLine()
                            while ln != None:
                                f.write(ln)
                                f.write('\n')
                                ln = stream.readLine()
                            f.seek(0)

                            if not ftp.completePendingCommand():
                                raise UserException("Couldn't complete ftp transaction: " + ftp.getReplyString())
                            ftp.logout()
                            self.log("Logged out.")
                            ftp.disconnect()
                            self.log("Disconnected.")

                            self.log("Treating files as type " + file_type)

                            self.importer = HhDataImportProcess(self.contract_id, 0, f, file_name + file_type, file.getSize())

                            self.importer.run()
                            messages = self.importer.messages
                            self.importer = None
                            for message in messages:
                                self.log(message)

                            if len(messages) > 0:
                                raise UserException("Problem loading file.")

                            last_import_keys[directory] = key
                            set_read_write(sess)
                            contract = Contract.get_hhdc_by_id(sess, self.contract_id)
                            contract.update_state(state)
                            sess.commit()
                            self.log("Finished loading '" + file.getName())
                            found_new = True
                    except UserException, e:
                        self.log("Problem " + str(e))
                        sess.rollback()
                    except:
                        self.log("Unknown Exception " + traceback.format_exc())
                        sess.rollback()
                    finally:
                        try:
                            if sess is not None:
                                sess.close()
                        except:
                            self.log("Unknown Exception II" + traceback.format_exc())
            finally:
                self.lock.release()

                    
    def run(self):
        while not self.stopped.isSet():
            self.import_now()
            self.going.wait(30 * 60)
            self.going.clear()


def get_hh_import_task(contract):
    return tasks.get(contract.id)

def startup():
    sess = None

    try:
        sess = session()
        for procs in processes.values():
            for proc in procs:
                if proc.isAlive():
                    raise UserException("Can't shut start hh importer, there are still some hh imports running.")

        for contract in sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'C').order_by(Contract.id):
            task = HhImportTask(contract.id)
            tasks[contract.id] = task
            task.start()
    finally:
        if sess is not None:
            sess.close()

def shutdown():
    for procs in processes.values():
        for proc in procs:
            if proc.isAlive():
                raise UserException("Can't shut down hh importer, there are still some hh imports running.")

    for task in tasks.values():
        task.stop()

    for id, task in tasks.iteritems():
        if task.isAlive():
            raise UserException("Can't shut down hh importer, the task " + str(task) + " with id " + str(id) + " is still running.")