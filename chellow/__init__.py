from flask import Flask
import os
import pg8000

pg8000.dbapi = pg8000


app = Flask('chellow', instance_relative_config=True)
config = app.config
config.from_object('chellow.settings')

if 'RDS_HOSTNAME' in os.environ:
    for conf_name, rds_name in (
            ('PGDATABASE', 'RDS_DB_NAME'), ('PGUSER', 'RDS_USERNAME'),
            ('PGPASSWORD', 'RDS_PASSWORD'), ('PGHOST', 'RDS_HOSTNAME'),
            ('PGPORT', 'RDS_PORT')):
        config[conf_name] = os.environ[rds_name]

for var_name in (
        'PGUSER', 'PGPASSWORD', 'PGHOST', 'PGPORT', 'PGDATABASE',
        'CHELLOW_FIRST_EMAIL', 'CHELLOW_FIRST_PASSWORD', 'CHELLOW_PORT'):
    if var_name in os.environ:
        config[var_name] = os.environ[var_name]
    print(var_name, config[var_name])

config['CHELLOW_PORT'] = int(config['CHELLOW_PORT'])
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
