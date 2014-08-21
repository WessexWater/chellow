import os

CHELLOW_HOME = os.environ['CHELLOW_HOME']

bind = '127.0.0.1:8000'
pidfile = CHELLOW_HOME + '/gunicorn/pid'
daemon = True
errorlog = CHELLOW_HOME + '/gunicorn/errors'
