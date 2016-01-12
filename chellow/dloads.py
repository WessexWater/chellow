import traceback
import collections
import pytz
import threading
import sys
import os
import os.path
import time
import datetime
import chellow
from werkzeug.exceptions import BadRequest

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
            datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") +
            " - " + message)
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
                except:
                    self.log("Outer problem " + traceback.format_exc())
                finally:
                    self.lock.release()
                    self.log("Finished deleting files.")

            self.going.wait(24 * 60 * 60)
            self.going.clear()


def get_file_deleter():
    return file_deleter


def startup():
    global file_deleter
    file_deleter = FileDeleter()
    file_deleter.start()


def shutdown():
    if file_deleter is not None:
        file_deleter.stop()
        if file_deleter.isAlive():
            raise BadRequest(
                "Can't shut down file deleter, it's still running.")
