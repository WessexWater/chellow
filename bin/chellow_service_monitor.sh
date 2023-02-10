#!/usr/bin/env bash

if pip list --outdated --format=columns | grep chellow ; then
        echo "Found a new Chellow version."

        echo "Stopping Chellow"
        /usr/sbin/systemctl stop chellow

        echo "Doing a pip upgrade of Chellow."
        pip install chellow --upgrade

        echo "Starting Chellow"
        /usr/sbin/systemctl start chellow
else
        echo "No new version found."
fi
