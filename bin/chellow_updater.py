#!/usr/bin/env python

import json
import urllib.request
import chellow
from distutils.version import LooseVersion
import argparse
import subprocess
import logging

parser = argparse.ArgumentParser()
parser.add_argument('--test', action='store_true')
parser.add_argument('--log')
args = parser.parse_args()

loglevel = getattr(logging, args.log.upper())
logging.basicConfig(format='%(asctime)s %(message)s', level=loglevel)

pip_args = ['pip', 'install', 'chellow', '--upgrade']

if args.test:
    prefix = 'test'
    pip_args.extend(
        [
            '--extra-index-url', 'https://testpypi.python.org/pypi',
            '--no-cache-dir'])
else:
    prefix = ''

pypi_url = 'https://' + prefix + 'pypi.python.org/pypi/chellow/json'
with urllib.request.urlopen(pypi_url) as f:
    pypi_j = json.loads(f.read().decode('utf8'))

latest_ver = LooseVersion(pypi_j['info']['version'])
current_ver = LooseVersion(chellow.__version__)
logging.info(
    "Latest version is " + str(latest_ver) + " and current version is " +
    str(current_ver))
if latest_ver > current_ver:
    logging.info("About to upgrade: " + ' '.join(pip_args))
    subprocess.run(pip_args)
    logging.info("About to restart")
    subprocess.run(['chellow', 'restart'])
else:
    logging.info("No action taken.")
