import argparse
import os.path
import signal
import sys
import time
from os import environ

from pep3143daemon import DaemonContext, PidFile

import waitress

from chellow import create_app

app = create_app()


def chellow_test_setup():
    """
    import subprocess
    import shutil
    downloads_path = os.path.join(app.instance_path, 'downloads')
    if os.path.exists(downloads_path):
        shutil.rmtree(downloads_path)
    subprocess.Popen(["python", "test/ftp.py"])
    """


def chellow_start(daemon):
    chellow_port = environ["CHELLOW_PORT"] if "CHELLOW_PORT" in environ else 80
    daemon.open()
    waitress.serve(app, host="0.0.0.0", port=chellow_port)


def chellow_stop(pidfile_path):
    with open(pidfile_path) as pidfile:
        pid = int(pidfile.read())
        os.kill(pid, signal.SIGTERM)
    while os.path.exists(pidfile_path):
        time.sleep(1)


def chellow_command():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "restart"])
    args = parser.parse_args()

    try:
        os.makedirs(app.instance_path)
    except BaseException:
        pass
    pidfile_path = os.path.join(app.instance_path, "chellow.pid")
    pidfile = PidFile(pidfile_path)
    daemon = DaemonContext(
        pidfile=pidfile, stdin=sys.stdin, stderr=sys.stderr, stdout=sys.stdout
    )

    if args.action == "start":
        chellow_start(daemon)
    elif args.action == "stop":
        chellow_stop(pidfile_path)
    elif args.action == "restart":
        chellow_stop(pidfile_path)
        chellow_start(daemon)
