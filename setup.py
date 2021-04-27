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
    packages=["chellow", "chellow.reports"],
    package_data={
        "chellow": [
            "non_core_contracts/*/*.zish",
            "non_core_contracts/*/rate_scripts/*.zish",
            "mdd/converted/*.csv",
            "templates/*.html",
            "templates/css/*.css",
            "templates/js/*.js",
            "templates/*.css",
            "static/images/**",
            "static/css/**",
            "static/js/**",
            "static/font-awesome-4.6.3/**",
            "static/font-awesome-4.6.3/css/**",
            "static/font-awesome-4.6.3/fonts/**",
            "static/font-awesome-4.6.3/less/**",
            "static/font-awesome-4.6.3/scss/**",
            "nationalgrid/*",
            "elexonportal/*",
            "rate_scripts/*/*.zish",
        ]
    },
    install_requires=[
        "odio==0.0.22",
        "pg8000==1.19.3",
        "Flask==1.1.2",
        "werkzeug==1.0.1",
        "SQLAlchemy==1.4.11",
        "openpyxl==2.4.8",
        "python-dateutil==2.8.1",
        "pytz==2020.1",
        "ftputil==4.0.0",
        "requests==2.25.1",
        "waitress==1.4.3",
        "pep3143daemon==0.0.6",
        "pip>=9.0.1",
        "pysftp==0.2.9",
        "pympler==0.9",
        "psutil==5.7.2",
        "xlrd==1.2.0",
        "zish==0.1.9",
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
