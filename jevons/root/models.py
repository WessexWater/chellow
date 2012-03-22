from django.db import models
from root.monad import UserException
import threading
import stat
import tempfile
import datetime
import ftputil
import os
import sys

class Asset(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', null=True)
    start_date = models.DateTimeField()
    finish_date = models.DateTimeField(null=True)
    properties = models.TextField()

    class Meta:
        db_table = 'asset'

    def parents(self):
        parent_list = []
        
        cand_parent = self.parent
        
        while True:
            if cand_parent is None:
                break
            else:
                parent_list.append(cand_parent)
                cand_parent = cand_parent.parent
                
        return parent_list

    def assets(self):
        return Asset.objects.filter(parent=self)


class Logger():
    
    def __init__(self):
        self.lock = threading.Lock()
        self.messages = []
        
    def log(self, message):
        with self.lock:
            self.messages.append(message)
        
    def get_log(self):
        with self.lock:
            return '\n'.join(self.messages)


class Advance(models.Model):
    '''
    @staticmethod
    def insert(data):
        for datum in data:
            asset_code = datum['asset_code']
            MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
        SupplyGeneration generation = mpanCore.getSupply().getGeneration(
                datum.getStartDate());
        if (generation == null) {
            throw new UserException(
                    "This datum is either before or after the supply: "
                            + datum.toString() + ".");
        }
        long previousDate = datum.getStartDate().getDate().getTime();
        boolean isImport = datum.getIsImport();
        boolean isKwh = datum.getIsKwh();
        Channel channel = generation.getChannel(isImport, isKwh);
        if (channel == null) {
            throw new UserException("There is no channel for the datum: "
                    + datum.toString() + ".");
        }
        HhStartDate genFinishDate = generation.getFinishDate();
        List<HhDatumRaw> data = new ArrayList<HhDatumRaw>();
        data.add(datum);
        // HhDatumRaw firstDatum = datum;
        if (!rawData.hasNext()) {
            // batchSize = data.size();
            channel.addHhData(data);
        }
        while (rawData.hasNext() && !halt.get(0)) {
            datum = rawData.next();
            Date startDate = datum.getStartDate().getDate();
            if (data.size() > 1000
                    || !(mpanCoreStr.equals(datum.getMpanCore())
                            && datum.getIsImport() == isImport
                            && datum.getIsKwh() == isKwh && startDate.getTime() == HhStartDate
                            .getNext(cal, previousDate))
                    || (genFinishDate != null && genFinishDate.getDate()
                            .before(startDate))) {
                // batchSize = data.size();
                channel.addHhData(data);
                Hiber.close();
                data.clear();
                mpanCoreStr = datum.getMpanCore();
                mpanCore = MpanCore.getMpanCore(mpanCoreStr);
                generation = mpanCore.getSupply().getGeneration(
                        datum.getStartDate());
                if (generation == null) {
                    throw new UserException(
                            "This datum is either before or after the supply: "
                                    + datum.toString() + ".");
                }
                isImport = datum.getIsImport();
                isKwh = datum.getIsKwh();
                channel = generation.getChannel(isImport, isKwh);
                if (channel == null) {
                    throw new UserException(
                            "There is no channel for the datum: "
                                    + datum.toString() + ".");
                }
                genFinishDate = generation.getFinishDate();
            }
            data.add(datum);
            previousDate = startDate.getTime();
        }
        if (!data.isEmpty()) {
            channel.addHhData(data);
        }
        Hiber.close();
    }
    
    '''
    asset = models.ForeignKey('Asset')
    start_date = models.DateTimeField()
    value = models.FloatField()

    class Meta:
        db_table = 'advance'
        unique_together = (('asset', 'start_date'),)
        

class Importer(models.Model):
    name = models.CharField(max_length=100, unique=True)
    properties = models.TextField()
    state = models.TextField()
    
    logger = Logger()
    lock = threading.Lock()
    
    class Meta:
        db_table = 'importer'
        
    def validate(self):
        try:
            self.get_props()
        except SyntaxError, detail:
            raise UserException("Problem parsing properties " + str(detail))
        except NameError, detail:
            raise UserException("Problem parsing properties " + str(detail))
        
        try:
            self.get_state()
        except SyntaxError, detail:
            raise UserException("Problem parsing state " + str(detail))
        except NameError, detail:
            raise UserException("Problem parsing state " + str(detail))

    def get_props(self):
        return eval(self.properties, {})
    
    def set_props(self, props):
        self.properties = str(props)
        self.validate()
        
    def get_state(self):
        return eval(self.state, {})
    
    
    def set_state(self, state_dict):
        self.state = str(state_dict)
        self.validate()
        
    def ftp_process(self):
        if self.lock.acquire(False):
            try:
                props = self.get_props()
                host_name = props['ftp_host_name']
                user_name = props['ftp_user_name']
                password = props['ftp_password']
                directories = []
                state_dict = self.get_state()
            
                while True:
                    try:
                        name = props['directory_' + str(len(directories))]
                    except KeyError:
                        break
                
                    last_import_key_name = "last_import_key_" + str(len(directories))
                    try:
                        last_import_key = state_dict[last_import_key_name]
                    except KeyError:
                        last_import_key = unicode('')
                    
                    directories.append({'name': name, 'last-import-key-name': last_import_key_name, 'last-import-key': last_import_key})


                    self.logger.log("Connecting to ftp server at " + host_name + " ...")
                    with ftputil.FTPHost(host_name, user_name, password) as ftp:
                        self.logger.log("Server replied with '" + ftp.getwelcome() + "'.")
                        for directory in directories:
                            self.logger.log("Checking the directory '" + directory['name'] + "'.")

                            files = []
                            for fname in ftp.listdir(directory['name']):
                                fstat = ftp.stat(directory['name'] + '/' + fname)
                                if fstat[stat.ST_MODE] != stat.S_IFREG:
                                    continue
                                key = datetime.datetime.fromtimestamp(file[stat.ST_MTIME]).isoformat() + "_" + fname
                                if key <= directory['last-import-key']:
                                    continue
                                
                                if fstat[stat.ST_SIZE] == 0:
                                    self.logger.log("Ignoring '" + fname + "'because it has zero length")
                                    continue
                                
                                files.append((key, fname))

                            for key, fname in sorted(files):
                                file_name = directory['name'] + "\\" + fname
                                self.logger.log("Attempting to download '" + file_name + "'.")
                                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                                    tmp_file_name = tmp_file.name 

                                try:
                                
                                    ftp.download(file_name, tmp_file_name, mode="b")
                                    self.logger.log("Downloaded " + file_name + ".")

                                    with open(tmp_file_name) as tmp_file:
                                        self.import_file(tmp_file)
                                        
                                    state_dict[directory['last-import-key-name']] = key 
                                    self.set_state(state_dict)
                                    self.save()
                                finally:
                                    os.remove(tmp_file_name)

                    
                            if len(files) == 0:
                                self.logger.log("No new files found.")
                            self.logger.log("Logged out.")
            except:
                e_info = sys.exc_info()
                tb = e_info[2]
                self.logger.log("Unknown Exception " + str(e_info[0]) + str(e_info[1]) + str(tb) + " line number " + str(tb.tb_lineno))
            finally:
                self.lock.release()
        else:
            self.logger.log("An import is already in progress")
        
    def import_file(self, ifile):
        pass
