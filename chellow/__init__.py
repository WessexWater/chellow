import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
import os

app = Flask('chellow')
handler = RotatingFileHandler('chellow.log')
handler.setLevel(logging.WARNING)
app.logger.addHandler(handler)
app.config.from_object('chellow.settings')

from chellow.models import Contract

@app.before_first_request
def on_startup(*args, **kwargs):
    webinf_path = os.path.join(os.environ['CHELLOW_HOME'], 'web', 'WEB-INF')
    f = open(os.path.join(webinf_path, 'bootstrap.py'), 'rb')
    exec(
        f,
        {
            'webinf_path': webinf_path,
            'user_name': app.config['PGUSER'],
            'password': app.config['PGPASSWORD'],
            'host_name': app.config['PGHOST'],
            'db_name': app.config['PGDATABSE']})
    startup_contract = Contract.get_non_core_by_name('startup')
    ns = {}
    exec(startup_contract.charge_script, ns)
    ns['on_start_up'](None)

import chellow.views
