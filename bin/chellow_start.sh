#!/bin/sh

source /home/chellow/.bashrc
source /var/www/chellow/venv/bin/activate

waitress-serve --host=0.0.0.0 --port=$CHELLOW_PORT --call chellow:create_app
