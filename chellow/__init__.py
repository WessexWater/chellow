import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
app = Flask(__name__)
handler = RotatingFileHandler('chellow.log')
handler.setLevel(logging.WARNING)
app.logger.addHandler(handler)

import chellow.views

