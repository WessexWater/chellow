#!/usr/bin/env python

from setuptools import setup
import versioneer


def get_version():
    ver = versioneer.get_version()
    try:
        ver = ver[ver.index('.') + 1:]
        ver = ver[:ver.index('.')]
    except IndexError:
        pass

    return ver.replace('-', '.').replace('+', '.')


setup(
    name='chellow',
    version=get_version(),
    description='Web Application for checking UK utility bills.',
    author='Tony Locke',
    author_email='tlocke@tlocke.org.uk',
    url='https://github.com/WessexWater/chellow',
    cmdclass=versioneer.get_cmdclass(),
    packages=[
        'chellow', 'net', 'net.sf', 'net.sf.chellow', 'net.sf.chellow.monad',
        'utils', 'db', 'bank_holidays', 'scenario', 'computer', 'triad_rates',
        'duos', 'templater', 'general_import', 'hh_importer', 'bill_import',
        'edi_lib', 'dloads', 'triad', 'bsuos', 'system_price', 'rcrc', 'tlms',
        'odswriter', 'odswriter.v1_1', 'odswriter.v1_2'],
    package_data={'chellow': [
        'web/WEB-INF/bootstrap.py',
        'web/WEB-INF/reports/*/script.py',
        'web/WEB-INF/reports/*/template.txt',
        'web/WEB-INF/reports/*/meta.py',
        'web/WEB-INF/non_core_contracts/*/*.py',
        'web/WEB-INF/non_core_contracts/*/rate_scripts/*.py',
        'web/WEB-INF/dno_contracts/*/*.py',
        'web/WEB-INF/dno_contracts/*/rate_scripts/*.py',
        'web/WEB-INF/mdd/*.csv',
        'templates/*.html',
        'bmreports/sysprice/*.xml',
        'elexonportal/prices.xls']},
    install_requires=[
        'Jinja2==2.8',
        'Flask==0.10.1',
        'Flask-SQLAlchemy==2.0',
        'SQLAlchemy==1.0.9',
        'pg8000==1.10.2',
        'python-dateutil==2.4.2',
        'pytz==2015.6',
        'xlrd==0.9.4',
        'ftputil==3.2',
        'requests==2.8.1',
        'pympler'],
    entry_points={
        'console_scripts': [
            'chellow_start = chellow.commands:chellow_start',
            'chellow_db_init = chellow.commands:chellow_db_init',
            'chellow_db_upgrade = chellow.commands:chellow_db_upgrade',
            'start_chellow_process = chellow.commands:start_chellow_process',
            'chellow_test_setup = chellow.commands:chellow_test_setup',
            'chellow_watchdog_start = chellow.commands:chellow_watchdog_start',
            'chellow_stop = chellow.commands:chellow_stop']})
