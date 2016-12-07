#!/usr/bin/env bash

if [[ $* == *--test* ]] ; then
	if pip list --outdated --extra-index-url https://testpypi.python.org/pypi --format=columns | grep chellow ; then
		echo "Found a new Chellow version."

		echo "Stopping Chellow"
		/sbin/initctl stop chellow

		echo "Doing a pip upgrade of Chellow."
		pip install chellow --upgrade --extra-index-url https://testpypi.python.org/pypi

		echo "Starting Chellow"
		/sbin/initctl start chellow
	else
		echo "No new version found."
	fi
else
	if pip list --outdated --format=columns | grep chellow ; then
		echo "Found a new Chellow version."

		echo "Stopping Chellow"
		/sbin/initctl stop chellow

		echo "Doing a pip upgrade of Chellow."
		pip install chellow --upgrade

		echo "Starting Chellow"
		/sbin/initctl start chellow
	else
		echo "No new version found."
	fi
fi
