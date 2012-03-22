import threading
import ftputil
from root.monad import UserException
import root.models

importers = {}
lock = threading.Lock()

def load_importer(importer_id):
    with lock:
        if importer_id in importers:
            raise UserException("The importer is already loaded.")
        else:
            importers[importer_id] = root.models.Importer.objects.get(id__exact=importer_id)
        
        
def unload_importer(importer_id):
    with lock:
        if importer_id in importers:
            del importers[importer_id]
        else:
            raise UserException("The importer isn't there to unload.")

        
def get_importer(importer_id):
    with lock:
        if importer_id in importers:
            return importers[importer_id]
        else:
            return None

'''

            
    def __init__(self, hhdc_contract_id, process_id, istream, file_name, file_size):
        self.messages = []
        self.halt = ArrayList()
        self.halt.add(False)
        self.hhdc_contract_id = hhdc_contract_id
        self.process_id = process_id
        if file_size == 0:
            raise UserException("File has zero length")

        file_name = file_name.lower();
        if file_name.endswith(".zip"):
            try:
                zin = ZipInputStream(BufferedInputStream(istream));
                entry = zin.getNextEntry()
                if entry is None:
                    raise UserException(None, "Can't find an entry within the zip file.")
                else:
                    istream = zin
                    file_name = entry.getName()
            except IOException, e:
                raise InternalException(e)

        conv_ext = [ext for ext in extensions if file_name.endswith(ext)]
        if len(conv_ext) == 0:
            raise UserException("The extension of the filename '" + file_name + "' is not one of the recognized extensions; " + str(extensions))
        hhdc_contract = HhdcContract.getHhdcContract(self.hhdc_contract_id)
        mpan_map_str = hhdc_contract.getProperty("mpan.map")
        mpan_map = {}
        if mpan_map_str is not None:
            for mpan_item in mpan_map_str.split(','):
                search_replace = mpan_item.split('>')
                mpan_map[search_replace[0]] = search_replace[1]

        self.converter = NonCoreContract.getNonCoreContract('hh-parser-' + conv_ext[0][1:]).callFunction('create_parser', [InputStreamReader(istream, "UTF-8"), self.messages, mpan_map])


    def run(self):
        try:
            HhDatum.insert(self.converter, self.halt)
            Hiber.close()
        except InternalException, e:
            self.messages.append("ProgrammerException : " + HttpException.getStackTraceString(e))
        except HttpException, e:
            self.messages.append(e.getMessage())
        except:
            e_info = sys.exc_info()
            tb = e_info[2]
            self.messages.append("Outer problem " + str(e_info[0]) + str(e_info[1]) + str(tb) + " line number " + str(tb.tb_lineno))
            ChellowLogger.getLogger().logp(Level.SEVERE,                    "HhDataImportProcessor", "run",    "Problem in run method " + e.getMessage(), e)
        finally:
            Hiber.rollBack()
            Hiber.close()
            try:
                self.converter.close()
            except InternalException, e:
                raise RuntimeException(e)

    def halt(self):
        halt[0] = True

    def status(self):
        return "Processing line number " + str(self.converter.lastLineNumber()) + "."

    def to_xml(self, doc):
        process_element = doc.createElement("hh-data-import")
        process_element.setAttribute("progress", self.status())
        process_element.setAttribute("id", str(self.process_id))
        return process_element


def create_import_process_from_item(hhdc_contract_id, id, item):
    try:
        return create_import_process(hhdc_contract_id, id, item.getInputStream(), item.getName(), item.getSize())
    except IOException, e:
        raise InternalException(e)


def create_import_process(hhdc_contract_id, id, istream, file_name, file_size):
    return HhDataImportProcess(hhdc_contract_id, id, istream, file_name, file_size)


def import_hh_data(task):
    ftp = None
    try:
        contract = HhdcContract.getHhdcContract(task.contract_id)
        host_name = contract.getProperty("hostname")
        user_name = contract.getProperty("username")
        password = contract.getProperty("password")
        file_type = contract.getProperty("file.type")

        directories = []
    
        while True:
            name = contract.getProperty("directory" + str(len(directories)))
            if name is None:
                break
            last_import_key_name = "lastImportKey" + str(len(directories))
            last_import_key = contract.getStateProperty(last_import_key_name)
            if last_import_key is None:
                last_import_key = unicode('')
            directories.append({'name': name, 'last-import-key-name': last_import_key_name, 'last-import-key': last_import_key})

        ftp = FTPClient()
        ftp.setDataTimeout(1000 * 60)
    
        ftp.connect(host_name)
        task.log("Connecting to ftp server at " + host_name + ".")
        task.log("Server replied with '" + ftp.getReplyString() + "'.")
        reply = ftp.getReplyCode()
        if not FTPReply.isPositiveCompletion(reply):
            raise UserException("FTP server refused connection.")

        task.log("Connected to server, now logging in.")
        ftp.login(user_name, password)
        task.log("Server replied with '" + ftp.getReplyString() + "'.")
        for directory in directories:
            task.log("Checking the directory '" + directory['name'] + "'.")

            files = [(str(MonadDate(file.getTimestamp().getTime())) + "_" + file.getName(), file) for file in ftp.listFiles(directory['name']) if file.getType() == FTPFile.FILE_TYPE]

            files = [(key, file) for key, file in files if key > directory['last-import-key']]

            for key, file in sorted(files):
                file_name = directory['name'] + "\\" + file.getName()
                if file.getSize() == 0:
                    task.log("Ignoring '" + file_name + "'because it has zero length")
                    continue
                task.log("Attempting to download '" + file_name
+ "'.")
                istr = ftp.retrieveFileStream(file_name)
                if istr is None:
                    reply = ftp.getReplyCode()
                    raise UserException("Can't download the file '" + file.getName() + "', server says: " + reply + ".")
                task.log("File stream obtained successfully.")
                task.importer = HhDataImportProcess(task.contract_id, 0, istr, file_name + file_type, file.getSize())
                task.importer.run()
                messages = task.importer.messages
                task.importer = None
                for message in messages:
                    task.log(message)

                if len(messages) > 0:
                    raise UserException("Problem loading file.")

                if not ftp.completePendingCommand():
                    raise UserException("Couldn't complete ftp transaction: " + ftp.getReplyString())
                contract = HhdcContract.getHhdcContract(task.contract_id)
                contract.setStateProperty(directory['last-import-key-name'], key)
                Hiber.commit()
            if len(files) == 0:
                task.log("No new files found.")
        ftp.logout()
        task.log("Logged out.")
    except UserException, e:
        task.log("Problem " + str(e))
    except:
        e_info = sys.exc_info()
        tb = e_info[2]
        task.log("Unknown Exception " + str(e_info[0]) + str(e_info[1]) + str(tb) + " line number " + str(tb.tb_lineno))
    finally:
        Hiber.close()
        if ftp is not None and ftp.isConnected():
            ftp.disconnect();
            task.log("Disconnected.")


class HhImportTask(TimerTask):

    def __init__(self, timer, contract):
        self.timer = timer
        self.lock = ReentrantLock()
        self.messages = []
        self.contract_id = contract.getId()
        self.importer = None
        self.date_formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss 'Z'")
        self.date_formatter.setCalendar(MonadDate.getCalendar())

    def log(self, message):
        self.messages.insert(0, self.date_formatter.format(Date()) + " - " + message)
        if len(self.messages) > 1000:
            del self.messages[-1]

    def get_status(self):
        if self.importer is None:
            return ''
        else:
            return self.importer.status()


    def is_locked(self):
        return self.lock.isLocked()


    def run(self):
        if self.lock.tryLock():
            try:
                import_hh_data(self)
            except:
                e_info = sys.exc_info()
                tb = e_info[2]
                task.log("Outer problem " + str(e_info[0]) + str(e_info[1]) + str(tb) + " line number " + str(tb.tb_lineno))
            finally:
                self.lock.unlock()


def _importer_task_key(contract):
    return "net.sf.chellow.hh_importer_task_" + str(contract.getId())


def get_hh_importer_task(ctx, contract):
    return ctx.getAttribute(_importer_task_key(contract))


def start_hh_importer_task(ctx, contract):
    existing_task = get_hh_importer_task(ctx, contract)
    if existing_task is None:
        timer = Timer("HH Importer Timer For " + str(contract.getId()), True)
        hh_importer_task = HhImportTask(timer, contract)
        timer.schedule(hh_importer_task, 0, 60 * 60 * 1000)
        ctx.setAttribute(_importer_task_key(contract), hh_importer_task)
    else:
        raise UserException("There's already an importer task for this contract")

def remove_hh_importer_task(ctx, contract):
    existing_task = get_hh_importer_task(ctx, contract)
    if existing_task is None:
        raise UserException("There isn't an importer task for this contract.")
    existing_task.cancel()
    existing_task.timer.cancel()
    if existing_task.is_locked():
        raise UserException("There's an import currently in progress.")
    
    ctx.setAttribute(_importer_task_key(contract), None)

class BglobalImporter():
    def __init__(self, props):
        self.props = props
        lock = threading.lock()        

 def __init__(self, hhdc_contract_id, process_id, istream, file_name, file_size):
        self.messages = []
        self.halt = ArrayList()
        self.halt.add(False)
        self.hhdc_contract_id = hhdc_contract_id
        self.process_id = process_id
        if file_size == 0:
            raise UserException("File has zero length")

        file_name = file_name.lower();
        if file_name.endswith(".zip"):
            try:
                zin = ZipInputStream(BufferedInputStream(istream));
                entry = zin.getNextEntry()
                if entry is None:
                    raise UserException(None, "Can't find an entry within the zip file.")
                else:
                    istream = zin
                    file_name = entry.getName()
            except IOException, e:
                raise InternalException(e)

        conv_ext = [ext for ext in extensions if file_name.endswith(ext)]
        if len(conv_ext) == 0:
            raise UserException("The extension of the filename '" + file_name + "' is not one of the recognized extensions; " + str(extensions))
        hhdc_contract = HhdcContract.getHhdcContract(self.hhdc_contract_id)
        mpan_map_str = hhdc_contract.getProperty("mpan.map")
        mpan_map = {}
        if mpan_map_str is not None:
            for mpan_item in mpan_map_str.split(','):
                search_replace = mpan_item.split('>')
                mpan_map[search_replace[0]] = search_replace[1]

        self.converter = NonCoreContract.getNonCoreContract('hh-parser-' + conv_ext[0][1:]).callFunction('create_parser', [InputStreamReader(istream, "UTF-8"), self.messages, mpan_map])


    def run(self):
        try:
            HhDatum.insert(self.converter, self.halt)
            Hiber.close()
        except InternalException, e:
            self.messages.append("ProgrammerException : " + HttpException.getStackTraceString(e))
        except HttpException, e:
            self.messages.append(e.getMessage())
        except:
            e_info = sys.exc_info()
            tb = e_info[2]
            self.messages.append("Outer problem " + str(e_info[0]) + str(e_info[1]) + str(tb) + " line number " + str(tb.tb_lineno))
            ChellowLogger.getLogger().logp(Level.SEVERE,                    "HhDataImportProcessor", "run",    "Problem in run method " + e.getMessage(), e)
        finally:
            Hiber.rollBack()
            Hiber.close()
            try:
                self.converter.close()
            except InternalException, e:
                raise RuntimeException(e)

    def halt(self):
        halt[0] = True


    def status(self):
        return "Processing line number " + str(self.converter.lastLineNumber()) + "."


    def to_xml(self, doc):
        process_element = doc.createElement("hh-data-import")
        process_element.setAttribute("progress", self.status())
        process_element.setAttribute("id", str(self.process_id))
        return process_element
'''