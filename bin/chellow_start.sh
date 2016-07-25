#!/bin/sh

source /home/chellow/.bashrc
source /var/www/chellow/venv/bin/activate

waitress-serve --host=0.0.0.0 --port=$CHELLOW_PORT chellow:app
