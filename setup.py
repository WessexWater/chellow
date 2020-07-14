#!/usr/bin/env python

from setuptools import setup
import versioneer
import time
import sys

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


if "--test" in sys.argv:
    versioneer.tstamp = str(int(time.time()))
    sys.argv.remove("--test")


setup(
    name='chellow',
    version=versioneer.get_version(),
    description='Web Application for checking UK utility bills.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tony Locke',
    author_email='tlocke@tlocke.org.uk',
    url='https://github.com/WessexWater/chellow',
    cmdclass=versioneer.get_cmdclass(),
    packages=[
        'chellow', 'chellow.reports'
    ],
    package_data={
        'chellow': [
            'non_core_contracts/*/*.zish',
            'non_core_contracts/*/rate_scripts/*.zish',
            'mdd/converted/*.csv',
            'templates/*.html',
            'templates/css/*.css',
            'templates/js/*.js',
            'templates/*.css',
            'static/images/**',
            'static/css/**',
            'static/js/**',
            'static/font-awesome-4.6.3/**',
            'static/font-awesome-4.6.3/css/**',
            'static/font-awesome-4.6.3/fonts/**',
            'static/font-awesome-4.6.3/less/**',
            'static/font-awesome-4.6.3/scss/**',
            'nationalgrid/*',
            'elexonportal/*',
            'rate_scripts/*/*.zish'
        ]
    },
    install_requires=[
        'odio==0.0.16',
        'pg8000==1.13.2',
        'Flask==1.1.2',
        'SQLAlchemy==1.3.3',
        'openpyxl==2.4.8',
        'python-dateutil==2.4.2',
        'pytz==2019.1',
        'ftputil==3.2',
        'requests==2.20.0',
        'waitress==1.4.3',
        'pep3143daemon==0.0.6',
        'pip>=9.0.1',
        'pysftp==0.2.9',
        'pympler==0.7',
        'psutil==5.6.6',
        'xlrd==0.9.4',
        'zish==0.1.8'
    ],
    data_files=[('config', ['config/chellow.conf'])],
    entry_points={
        'console_scripts': [
            'chellow = chellow.commands:chellow_command',
            'chellow_test_setup = chellow.commands:chellow_test_setup'
        ]
    },
    scripts=['bin/chellow_service_monitor.sh', 'bin/chellow_start.sh']
)
