import atexit
import collections
import os
import os.path
import threading
import time
import traceback

from zipfile import ZIP_DEFLATED, ZipFile

from werkzeug.exceptions import BadRequest

from chellow.utils import utc_datetime_now


download_id = 0
lock = threading.Lock()

download_path = None
SERIAL_DIGITS = 5


def startup(instance_path, run_deleter=True):
    global file_deleter
    global download_id
    global download_path

    if run_deleter:
        file_deleter = FileDeleter()
        file_deleter.start()

    download_path = instance_path / "downloads"
    download_path.mkdir(parents=True, exist_ok=True)

    dirs = sorted(download_path.iterdir(), reverse=True)
    if len(dirs) > 0:
        download_id = int(dirs[0].name[:SERIAL_DIGITS]) + 1


class DloadFile:
    def __init__(self, running_name, finished_name, mode, newline, is_zip):
        self.running_name = running_name
        self.finished_name = finished_name
        if is_zip:
            self.f = ZipFile(running_name, mode=mode, compression=ZIP_DEFLATED)
        else:
            self.f = self.running_name.open(mode=mode, newline=newline)

    def _check_exists(self):
        if not self.running_name.exists():
            raise BadRequest("Output file has been deleted.")

    def flush(self, *args, **kwargs):
        self._check_exists()
        return self.f.flush(*args, **kwargs)

    def write(self, *args, **kwargs):
        self._check_exists()
        return self.f.write(*args, **kwargs)

    def seek(self, *args, **kwargs):
        self._check_exists()
        return self.f.seek(*args, **kwargs)

    def truncate(self, *args, **kwargs):
        self._check_exists()
        return self.f.truncate(*args, **kwargs)

    def writestr(self, *args, **kwargs):
        self._check_exists()
        return self.f.writestr(*args, **kwargs)

    def close(self):
        self.f.close()
        self._check_exists()
        self.running_name.rename(self.finished_name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def open_file(base, user, mode="r", newline=None, is_zip=False):
    global download_id

    base = base.replace("/", "").replace(" ", "")
    try:
        lock.acquire()
        if len(list(download_path.iterdir())) == 0:
            download_id = 0
        serial = str(download_id).zfill(SERIAL_DIGITS)
        download_id += 1
    finally:
        lock.release()

    if user is None:
        uname = ""
    else:
        if hasattr(user, "proxy_username"):
            un = user.proxy_username
        else:
            un = user.email_address
        uname = un.replace("@", "").replace(".", "").replace("\\", "")

    names = tuple("_".join((serial, v, uname, base)) for v in ("RUNNING", "FINISHED"))
    running_name, finished_name = tuple(download_path / name for name in names)
    return DloadFile(running_name, finished_name, mode, newline, is_zip)


mem_id = 0
mem_lock = threading.Lock()
mem_vals = {}


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
MAX_AGE = 60 * 60 * 24 * 14


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
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        )
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
