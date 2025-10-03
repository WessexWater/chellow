#!/usr/bin/env bash

cd /var/www/chellow
source venv/bin/activate

if [[ $* == *--test* ]] ; then
	if pip list --outdated --extra-index-url https://test.pypi.org/simple/ | grep chellow ; then
		echo "Found a new Chellow version."

		echo "Stopping Chellow"
		/usr/bin/systemctl stop chellow

		echo "Doing a pip upgrade of Chellow."
		pip install chellow --upgrade --extra-index-url https://test.pypi.org/simple/

		echo "Starting Chellow"
		/usr/bin/systemctl start chellow
	else
		echo "No new version found."
	fi
else
	if pip list --outdated | grep chellow ; then
		echo "Found a new Chellow version."

		echo "Stopping Chellow"
		/usr/bin/systemctl stop chellow

		echo "Doing a pip upgrade of Chellow."
		pip install chellow --upgrade

		echo "Starting Chellow"
		/usr/bin/systemctl start chellow
	else
		echo "No new version found."
	fi
fi
