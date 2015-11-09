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
        'Jinja2==2.6',
        'Flask==0.10.1',
        'Flask-SQLAlchemy==2.0',
        'SQLAlchemy==0.8.6',
        'pg8000==1.10.2',
        'python-dateutil==1.5',
        'pytz==2014.4',
        'xlrd==0.7.9',
        'ftputil==3.0',
        'requests==2.5.1',
        'simplejson==3.6.5',
        'pympler'],
    entry_points={
        'console_scripts': [
            'chellow_start = chellow.commands:chellow_start',
            'start_chellow_process = chellow.commands:start_chellow_process',
            'chellow_test_setup = chellow.commands:chellow_test_setup',
            'chellow_restart = chellow.commands:chellow_restart',
            'chellow_stop = chellow.commands:chellow_stop']})
