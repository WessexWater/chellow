from flask import Flask
import os


app = Flask('chellow', instance_relative_config=True)
app.secret_key = os.urandom(24)
config = app.config
config.from_object('chellow.settings')

if 'RDS_HOSTNAME' in os.environ:
    for conf_name, rds_name in (
            ('PGDATABASE', 'RDS_DB_NAME'), ('PGUSER', 'RDS_USERNAME'),
            ('PGPASSWORD', 'RDS_PASSWORD'), ('PGHOST', 'RDS_HOSTNAME'),
            ('PGPORT', 'RDS_PORT')):
        config[conf_name] = os.environ[rds_name]

if 'CHELLOW_URL_PREFIX' in os.environ:
    config['APPLICATION_ROOT'] = os.environ['CHELLOW_URL_PREFIX']

for var_name in (
        'PGUSER', 'PGPASSWORD', 'PGHOST', 'PGPORT', 'PGDATABASE',
        'CHELLOW_PORT'):
    if var_name in os.environ:
        config[var_name] = os.environ[var_name]

config['CHELLOW_PORT'] = int(config['CHELLOW_PORT'])
config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
config['SQLALCHEMY_DATABASE_URI'] = ''.join(
    [
        "postgresql+pg8000://", config['PGUSER'], ":", config['PGPASSWORD'],
        "@", config['PGHOST'], ":", config['PGPORT'], "/",
        config['PGDATABASE']])

import chellow.views
__all__ = [chellow]

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
