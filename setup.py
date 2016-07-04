#!/usr/bin/env python

from setuptools import setup
import versioneer
import time
import sys


if "--test" in sys.argv:
    versioneer.tstamp = str(int(time.time()))
    sys.argv.remove("--test")


setup(
    name='chellow',
    version=versioneer.get_version(),
    description='Web Application for checking UK utility bills.',
    author='Tony Locke',
    author_email='tlocke@tlocke.org.uk',
    url='https://github.com/WessexWater/chellow',
    cmdclass=versioneer.get_cmdclass(),
    packages=[
        'chellow', 'chellow.reports', 'odswriter', 'odswriter.v1_1',
        'odswriter.v1_2', 'pg8000'],
    package_data={'chellow': [
        'non_core_contracts/*/*.py',
        'non_core_contracts/*/rate_scripts/*.py',
        'dno_contracts/*/*.py',
        'dno_contracts/*/rate_scripts/*.py',
        'mdd/*.csv',
        'templates/*.html',
        'templates/css/*.css',
        'templates/js/*.js',
        'templates/*.css',
        'static/fonts/*.ttf',
        'nationalgrid/*',
        'elexonportal/*']},
    install_requires=[
        'Flask==0.11.1',
        'SQLAlchemy==1.0.14',
        'python-dateutil==2.4.2',
        'pytz==2015.6',
        'xlrd==0.9.4',
        'ftputil==3.2',
        'requests==2.10.0',
        'waitress==0.9.0',
        'pep3143daemon==0.0.6',
        'pip>=8.1.1',
        'pympler'],
    data_files=[('config', ['config/chellow.conf'])],
    entry_points={
        'console_scripts': [
            'chellow = chellow.commands:chellow_command',
            'chellow_test_setup = chellow.commands:chellow_test_setup']},
    scripts=['bin/chellow_service_monitor.sh', 'bin/chellow_start.sh'])
