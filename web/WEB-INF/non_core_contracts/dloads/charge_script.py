from net.sf.chellow.monad import Monad
import threading
import sys
import os

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

if sys.platform.startswith('java'):
    download_path = Monad.getContext().getRealPath("/downloads")
else:
    download_path = os.path.join(os.environ['CHELLOW_HOME'], 'downloads')

if not os.path.exists(download_path):
    os.makedirs(download_path)


download_id = 0

lock = threading.Lock()

files = sorted(os.listdir(download_path), reverse=True)
if len(files) > 0:
    download_id = int(files[0][:3]) + 1


def make_names(base, user):
    global download_id
    try:
        lock.acquire()
        if len(os.listdir(download_path)) == 0:
            download_id = 0
        serial = str(download_id).zfill(3)
        download_id += 1
    finally:
        lock.release()

    if user is None:
        uname = ''
    else:
        if sys.platform.startswith('java'):
            addr = str(user.getEmailAddress())
        else:
            addr = user.email_address
        uname = addr.replace('@', '').replace('.', '')

    names = tuple(
        '_'.join((serial, v, uname, base)) for v in ('RUNNING', 'FINISHED'))
    return tuple(os.path.join(download_path, name) for name in names)
