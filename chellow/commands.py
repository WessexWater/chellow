import shutil
import subprocess
import chellow
import os.path
import os
from pep3143daemon import DaemonContext, PidFile
import waitress
import argparse
import signal
import time


def chellow_test_setup():
    downloads_path = os.path.join(chellow.app.instance_path, 'downloads')
    if os.path.exists(downloads_path):
        shutil.rmtree(downloads_path)
    subprocess.Popen(["python", "test/ftp.py"])


def chellow_start(daemon):
    chellow_port = chellow.app.config['CHELLOW_PORT']
    daemon.open()
    waitress.serve(chellow.app, host='0.0.0.0', port=chellow_port)


def chellow_stop(pidfile_path):
    with open(pidfile_path) as pidfile:
        pid = int(pidfile.read())
        os.kill(pid, signal.SIGTERM)
    while os.path.exists(pidfile_path):
        time.sleep(1)


def chellow_command():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['start', 'stop', 'restart'])
    args = parser.parse_args()

    stdin = open('/dev/null', 'r')
    try:
        stdout = open('/dev/tty', 'w')
        stderr = open('/dev/tty', 'w')
    except OSError:
        stdout = stderr = open('/dev/null', 'w')

    try:
        os.makedirs(chellow.app.instance_path)
    except:
        pass
    pidfile_path = os.path.join(chellow.app.instance_path, 'chellow.pid')
    pidfile = PidFile(pidfile_path)
    daemon = DaemonContext(
        pidfile=pidfile, stdin=stdin, stderr=stderr, stdout=stdout)

    if args.action == 'start':
        chellow_start(daemon)
    elif args.action == 'stop':
        chellow_stop(pidfile_path)
    elif args.action == 'restart':
        chellow_stop(pidfile_path)
        chellow_start(daemon)
