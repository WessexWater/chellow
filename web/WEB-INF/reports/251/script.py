from net.sf.chellow.monad import Monad
import os
import datetime

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

files = []

download_path = Monad.getContext().getRealPath("/downloads")

for fl in os.listdir(download_path):
  statinfo = os.stat(os.path.join(download_path, fl))
  files.append({'name': fl, 'last_modified': datetime.datetime.utcfromtimestamp(statinfo.st_mtime), 'size': statinfo.st_size, 'creation_date': datetime.datetime.utcfromtimestamp(statinfo.st_ctime) })
render(inv, template, {'files': files})