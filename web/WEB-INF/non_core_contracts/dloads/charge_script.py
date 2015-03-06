from net.sf.chellow.monad import Monad
import threading
import sys
import os

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

download_id = 0

lock = threading.Lock()

if sys.platform.startswith('java'):
    download_path = Monad.getContext().getRealPath("/downloads")
else:
    download_path = os.path.join(os.environ['CHELLOW_HOME'], 'downloads')


def make_names(base):
    global download_id
    try:
        lock.acquire()
        serial = str(download_id).zfill(3)
        download_id += 1
    finally:
        lock.release()

    names = tuple('_'.join((serial, v, base)) for v in ('RUNNING', 'FINISHED'))
    return tuple(os.path.join(download_path, name) for name in names)
