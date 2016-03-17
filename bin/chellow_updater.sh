if [[ $* == *--test* ]] ; then
	if pip list --outdated --extra-index-url https://testpypi.python.org/pypi | grep chellow ; then
		echo "Found a new Chellow version."

		echo "Stopping Chellow"
		chellow stop

		echo "Doing a pip upgrade of Chellow."
		eval pip install chellow --upgrade --extra-index-url https://testpypi.python.org/pypi

		echo "Starting Chellow"
		chellow start
	else
		echo "No new version found."
	fi
else
	if pip list --outdated | grep chellow ; then
		echo "Found a new Chellow version."

		echo "Stopping Chellow"
		chellow stop

		echo "Doing a pip upgrade of Chellow."
		eval pip install chellow --upgrade

		echo "Starting Chellow"
		chellow start
	else
		echo "No new version found."
	fi
fi
