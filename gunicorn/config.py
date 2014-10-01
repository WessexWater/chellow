import os

CHELLOW_HOME = os.environ['CHELLOW_HOME']

bind = '127.0.0.1:8080'
pidfile = CHELLOW_HOME + '/gunicorn/pid'
daemon = True
errorlog = CHELLOW_HOME + '/gunicorn/errors'
