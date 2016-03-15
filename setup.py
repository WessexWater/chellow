#!/usr/bin/env python

from setuptools import setup
import versioneer
import time
import sys

is_test = False

if "--test" in sys.argv:
    is_test = True
    sys.argv.remove("--test")


def get_version():
    if is_test:
        return str(int(time.time()))
    else:
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
        'chellow', 'chellow.reports', 'odswriter', 'odswriter.v1_1',
        'odswriter.v1_2'],
    package_data={'chellow': [
        'non_core_contracts/*/*.py',
        'non_core_contracts/*/rate_scripts/*.py',
        'dno_contracts/*/*.py',
        'dno_contracts/*/rate_scripts/*.py',
        'mdd/*.csv',
        'templates/*.html',
        'static/*.css',
        'static/fonts/*.ttf',
        'bmreports/sysprice/*.xml',
        'elexonportal/prices.xls']},
    install_requires=[
        'Flask==0.10.1',
        'Flask-SQLAlchemy==2.1',
        'SQLAlchemy==1.0.11',
        'pg8000==1.10.5',
        'python-dateutil==2.4.2',
        'pytz==2015.6',
        'xlrd==0.9.4',
        'ftputil==3.2',
        'requests==2.8.1',
        'waitress==0.8.10',
        'pep3143daemon==0.0.6',
        'pip==8.10.0',
        'pympler'],
    entry_points={
        'console_scripts': [
            'chellow = chellow.commands:chellow_command',
            'chellow_test_setup = chellow.commands:chellow_test_setup']},
    scripts=['bin/chellow_updater.py'])
