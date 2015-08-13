from net.sf.chellow.monad import Monad
import threading
import sys
import os

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

if sys.platform.startswith('java'):
    download_path = Monad.getContext().getRealPath("/downloads")
else:
    import chellow
    download_path = os.path.join(chellow.app.instance_path, 'downloads')

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


mem_id = 0
mem_lock = threading.Lock()
mem_vals = {}


def get_mem_id():
    global mem_id
    try:
        mem_lock.acquire()
        mid = mem_id
        mem_id += 1
        mem_vals[mid] = None
    finally:
        mem_lock.release()
    return mid


def put_mem_val(mem_id, val):
    try:
        mem_lock.acquire()
        mem_vals[mem_id] = val
    finally:
        mem_lock.release()


def get_mem_val(mem_id):
    try:
        mem_lock.acquire()
        if mem_id in mem_vals:
            val = mem_vals[mem_id]
            # del mem_vals[mem_id]
        else:
            val = None
    finally:
        mem_lock.release()
    return val


def get_mem_items():
    try:
        mem_lock.acquire()
        return mem_vals.copy()
    finally:
        mem_lock.release()


def remove_item(mem_id):
    try:
        mem_lock.acquire()
        if mem_id in mem_vals:
            del mem_vals[mem_id]
    finally:
        mem_lock.release()
