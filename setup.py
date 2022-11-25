#!/usr/bin/env python

import sys
import time
from os import path

from setuptools import setup

import versioneer

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


if "--test" in sys.argv:
    versioneer.tstamp = str(int(time.time()))
    sys.argv.remove("--test")


setup(
    name="chellow",
    version=versioneer.get_version(),
    description="Web Application for checking UK utility bills.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tony Locke",
    author_email="tlocke@tlocke.org.uk",
    url="https://github.com/WessexWater/chellow",
    cmdclass=versioneer.get_cmdclass(),
    packages=[
        "chellow",
        "chellow.reports",
        "chellow.gas",
        "chellow.e",
        "chellow.e.bill_parsers",
    ],
    package_data={
        "chellow": [
            "templates/*.html",
            "templates/*/*.html",
            "templates/*.css",
            "static/images/**",
            "static/css/**",
            "static/js/**",
        ]
    },
    install_requires=[
        "odio==0.0.22",
        "pg8000==1.29.3",
        "Flask==2.2.2",
        "SQLAlchemy==1.4.44",
        "flask-restx==1.0.3",
        "openpyxl==3.0.10",
        "python-dateutil==2.8.2",
        "pytz==2022.6",
        "requests==2.28.1",
        "waitress==2.1.2",
        "pep3143daemon==0.0.6",
        "pip>=9.0.1",
        "pysftp==0.2.9",
        "pympler==1.0.1",
        "psutil==5.9.4",
        "xlrd==2.0.1",
        "zish==0.1.10",
    ],
    data_files=[("config", ["config/chellow.conf"])],
    entry_points={
        "console_scripts": [
            "chellow = chellow.commands:chellow_command",
            "chellow_test_setup = chellow.commands:chellow_test_setup",
        ]
    },
    scripts=["bin/chellow_service_monitor.sh", "bin/chellow_start.sh"],
)
