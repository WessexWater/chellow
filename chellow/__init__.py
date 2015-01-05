import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
import os


app = Flask('chellow')
handler = RotatingFileHandler('chellow.log')
handler.setLevel(logging.WARNING)
app.logger.addHandler(handler)
app.config.from_object('chellow.settings')

if 'RDS_HOSTNAME' in os.environ:
    for conf_name, rds_name in (
            ('PGDATABASE', 'RDS_DB_NAME'), ('PGUSER', 'RDS_USERNAME'),
            ('PGPASSWORD', 'RDS_PASSWORD'), ('PGHOST', 'RDS_HOSTNAME'),
            ('PGPORT', 'RDS_PORT')):
        app.config[conf_name] = os.environ[rds_name]

app.config['SQLALCHEMY_DATABASE_URI'] = \
    "postgresql+pg8000://" + app.config['PGUSER'] + ":" + \
    app.config['PGPASSWORD'] + "@" + app.config['PGHOST'] + ":" + \
    app.config['PGPORT'] + "/" + app.config['PGDATABASE']

from chellow.models import Contract

webinf_path = os.path.join(os.environ['CHELLOW_HOME'], 'web', 'WEB-INF')
f = open(os.path.join(webinf_path, 'bootstrap.py'), 'rb')
exec(
    f,
    {
        'webinf_path': webinf_path,
        'user_name': app.config['PGUSER'],
        'password': app.config['PGPASSWORD'],
        'host_name': app.config['PGHOST'],
        'db_name': app.config['PGDATABASE']})
startup_contract = Contract.get_non_core_by_name('startup')
ns = {}
exec(startup_contract.charge_script, ns)
ns['on_start_up'](None)

import chellow.views
__all__ = [chellow]
