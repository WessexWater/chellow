from net.sf.chellow.monad import Monad
import os
import datetime
import templater
import dloads
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'dloads')
inv, template = globals()['inv'], globals()['template']

files = []

download_path = dloads.download_path

if inv.getRequest().getMethod() == 'POST':
    for fl in os.listdir(download_path):
        os.remove(os.path.join(download_path, fl))

for fl in sorted(os.listdir(download_path), reverse=True):
    statinfo = os.stat(os.path.join(download_path, fl))
    files.append(
        {
            'name': fl,
            'last_modified': datetime.datetime.utcfromtimestamp(
                statinfo.st_mtime),
            'size': statinfo.st_size,
            'creation_date': datetime.datetime.utcfromtimestamp(
                statinfo.st_ctime)})

templater.render(inv, template, {'files': files})
