import traceback
from chellow.utils import utc_datetime_now
import collections
import threading
import os
import os.path
import time
import atexit

download_id = 0
lock = threading.Lock()

download_path = None
SERIAL_DIGITS = 4


def startup(instance_path):
    global file_deleter
    global download_id
    global download_path
    file_deleter = FileDeleter()
    file_deleter.start()

    download_path = os.path.join(instance_path, 'downloads')

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    files = sorted(os.listdir(download_path), reverse=True)
    if len(files) > 0:
        download_id = int(files[0][:SERIAL_DIGITS]) + 1


def make_names(base, user):
    global download_id

    base = base.replace('/', '').replace(' ', '')
    try:
        lock.acquire()
        if len(os.listdir(download_path)) == 0:
            download_id = 0
        serial = str(download_id).zfill(SERIAL_DIGITS)
        download_id += 1
    finally:
        lock.release()

    if user is None:
        uname = ''
    else:
        addr = user.email_address
        uname = addr.replace('@', '').replace('.', '').replace('\\', '')

    names = tuple(
        '_'.join((serial, v, uname, base)) for v in ('RUNNING', 'FINISHED'))
    return tuple(os.path.join(download_path, name) for name in names)


mem_id = 0
mem_lock = threading.Lock()
mem_vals = {}


def reset():
    global mem_id
    global mem_vals
    with mem_lock:
        mem_id = 0
        mem_vals = {}

    for fl in sorted(os.listdir(download_path)):
        os.remove(os.path.join(download_path, fl))


def get_mem_id():
    global mem_id
    with mem_lock:
        mid = mem_id
        mem_id += 1
        mem_vals[mid] = None
    return mid


def put_mem_val(mem_id, val):
    with mem_lock:
        mem_vals[mem_id] = val


def get_mem_val(mem_id):
    with mem_lock:
        val = mem_vals.get(mem_id)
    return val


def get_mem_items():
    with mem_lock:
        return mem_vals.copy()


def remove_item(mem_id):
    with mem_lock:
        if mem_id in mem_vals:
            del mem_vals[mem_id]


file_deleter = None
MAX_AGE = 60 * 60 * 24 * 7


class FileDeleter(threading.Thread):
    def __init__(self):
        super(FileDeleter, self).__init__(name="File Deleter")
        self.lock = threading.RLock()
        self.messages = collections.deque()
        self.stopped = threading.Event()
        self.going = threading.Event()

    def stop(self):
        self.stopped.set()
        self.going.set()
        self.join()

    def go(self):
        self.going.set()

    def is_locked(self):
        if self.lock.acquire(False):
            self.lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                try:
                    cur_time = time.time()
                    for file_name in sorted(os.listdir(download_path)):
                        file_path = os.path.join(download_path, file_name)
                        if cur_time - os.path.getmtime(file_path) > MAX_AGE:
                            os.remove(file_path)
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                finally:
                    self.lock.release()
                    self.log("Finished deleting files.")

            self.going.wait(24 * 60 * 60)
            self.going.clear()


def get_file_deleter():
    return file_deleter


@atexit.register
def shutdown():
    if file_deleter is not None:
        file_deleter.stop()
