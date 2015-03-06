import sys
from net.sf.chellow.monad import Monad
import os
import datetime
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
inv, template = globals()['inv'], globals()['template']

files = []

if sys.platform.startswith('java'):
    download_path = Monad.getContext().getRealPath("/downloads")
else:
    download_path = os.path.join(os.environ['CHELLOW_HOME'], 'downloads')

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
