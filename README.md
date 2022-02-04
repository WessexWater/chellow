# Chellow

A web application for checking UK electricity bills for organizations with
a large number of supplies and / or high consumption.

Website: https://www.chellow.org/


## Licence

Chellow is released under the [GPL v3](http://www.gnu.org/licenses/gpl.html).


## Introduction

Chellow is a web application for checking UK electricity bills. It's designed
for organizations with high electricity consumption. The software is hosted at
https://github.com/WessexWater/chellow.

[![Build Status](https://github.com/WessexWater/chellow/workflows/chellow/badge.svg)](https://github.com/WessexWater/chellow/workflows/chellow)


## Installation

Chellow is a Python web application (with a built-in webserver) that uses the
PostgreSQL database. To install Chellow, follow these steps:

* Install [PostgreSQL](http://www.postgresql.org/) 12
* Install Python 3.6 (tested on the [CPython 3.6.8](http://www.python.org/)
   interpreter)
* Create a PostgreSQL database: `createdb --encoding=UTF8 chellow`
* Install Chellow: `pip install chellow`
* Set up the following environment variables to configure Chellow:

| Name | Default | Description 
| ---- | ------- | -----------
| `PGUSER` | `postgres` | Postgres user name
| `PGPASSWORD` | `postgres` | Postgres password
| `PGHOST` | `localhost` | Postgres host name
| `PGPORT` | `5432` | Postgres port
| `PGDATABASE` | `chellow` | Postgres database name
| `CHELLOW_PORT` | `80` | Port that the Chellow webserver will listen on

In bash an environment variable can be set by doing:

`export CHELLOW_PORT=8080`

in Windows an environment variable can be set by doing:

`set CHELLOW_PORT=8080`

* Start Chellow by running `chellow start`.
* You should now be able to visit `http://localhost/` in a browser. You should
  be prompted to enter a username and password. Enter the admin user name
  `admin@example.com` and the password `admin`, and then the home page should
  appear. Change the admin password from the `users` page.
* Chellow can be stopped by running `chellow stop`.


### Manual Upgrading

To upgrade to the latest version of Chellow do: `pip install --upgrade chellow`


### Automatic Upgrading

On Unix, set up a cron job to regularly call the updater script by doing:

`crontab -e`

and entering the line:

`\* * * * * source /home/me/venv/bin/activate;chellow_updater.sh`


### Using A Different Webserver

Chellow comes bundled with the
[Waitress](http://docs.pylonsproject.org/projects/waitress/en/latest/)
webserver, but the is also a Python WSGI web application so Chellow can be used
with any WSGI compliant application server, eg Gunicorn. The WSGI app that
should be specified is `chellow.app`.


### Detailed Instructions For Installing On CentOS 6.7 64 bit For Development

Install PostgreSQL 9.5.2

Add the PostgreSQL repository:

`sudo rpm -ivh https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-6-x86_64/pgdg-centos95-9.5-2.noarch.rpm`

Install the PostgreSQL packages:

`sudo yum install postgresql95 postgresql95-server postgresql95-contrib`

Initialize the database:

`sudo service postgresql-9.5 initdb`

Make PostgreSQL start on boot:

`sudo chkconfig postgresql-9.5 on`

Edit PostgreSQL config file to accept all local connections:

`sudo vi /var/lib/pgsql/9.5/data/pg_hba.conf`

Find the lines:

`local   all    all                    peer`
`host    all    all    127.0.0.1/32    peer`

and change them to:

`local   all    all                    trust`
`host    all    all    127.0.0.1/32    trust`

start PostgreSQL:

`sudo service postgresql-9.5 start`

Install Python 3.5.1. Unfortunately there isn't an rpm for this so we have to
compile it:

`sudo yum groupinstall "Development tools"`
`sudo yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel wget`
`wget http://python.org/ftp/python/3.5.1/Python-3.5.1.tar.xz`
`tar xf Python-3.5.1.tar.xz`
`cd Python-3.5.1`
`./configure --prefix=/usr/local --enable-shared LDFLAGS="Wl,-rpath /usr/local/lib"`
`make`
`sudo make altinstall`

We need to tell Chellow which port to listen on, so:

`vi ~/.bashrc`

and add the line:

`export CHELLOW_PORT=8080`
`export PGUSER=postgres`

Clone the Chellow source from GitHub:

`git clone https://github.com/WessexWater/chellow.git`

Change directory to the 'chellow' directory:

`cd chellow`

Create a local `test` branch to track the remote `origin/test` branch:

`git branch --track test origin/test`

Check out the 'test' branch into the working directory:

`git checkout test`

Create a Python virtual environment:

`pyvenv-3.5 venv`

Activate the environment:

`source venv/bin/activate`

Make sure you're running a recent version of pip:

`pip install --upgrade pip`

Install tox:

`pip install tox`


Run tests:

`tox`

Old style tests: run\_tests\_0.sh run\_tests\_1.sh run\_tests\_2.sh
 

##  Getting Started

This is a brief guide to setting things up after you've installed Chellow. It
assumes that you have a basic knowledge of
[UK electricity billing](https://en.wikipedia.org/wiki/Electricity_billing_in_the_UK). It goes through the steps of adding a half-hourly (HH) metered supply,
and producing virtual bills for it, and then importing an actual bill and
running a bill check.

Chellow can handle non-half-hourly supplies as well as half-hourly, and it can
also deal with gas supplies, but we'll use a half-hourly electricity supply for
this example.


### View the Chellow home page

Assuming you've installed Chellow correctly, you should be able to open your
browser, type in the URL of the Chellow application, and see the Chellow home
page.


### Users

Before any users are added, if you access Chellow from `localhost` you'll have
read / write access. Once users are added, you have to log in as one of those
users. Users are added from the 'users' page.


### Add HHDC Contracts

Every supply must a have a data collector. Add in a new HHDC by going to the
'HHDC Contracts' page and then clicking on the 'Add' link. 


### Add MOP Contracts

Every supply must a have a meter operator. Add in a new MOP by going to the
'MOP Contracts' page and then clicking on the 'Add' link. For now just put in a
simple virtual bill for the MOP, so in the 'script' field enter:

```
    from chellow.utils import reduce_bill_hhs


    def virtual_bill_titles():
        return ['net-gbp']    

    
    def virtual_bill(data_source):
        for hh in data_source.hh_data:
						bill_hh = data_source.mop_bill_hhs[hh['start-date']]
            if hh['utc-is-month-end']:
                bill_hh['net-gbp'] = 10
        data_source.mop_bill = reduce_bills_hh(data_source.mop_bill_hhs)
```


### Add Supplier Contracts

Click on the 'supplier contracts' link and then fill out the 'Add a contract'
form. For the Charge Script field enter:

```
    from chellow.utils import reduce_bill_hhs

    def virtual_bill_titles():
        return ['net-gbp', 'day-kwh', 'day-gbp', 'night-kwh', 'night-gbp']    
    
    def virtual_bill(data_source):
        bill = data_source.supplier_bill 
    
        for hh in data_source.hh_data:
						bill_hh = data_source.supplier_bill_hhs[hh['start-date']]
            if 0 < hh['utc-decimal-hour'] < 8:
                bill_hh['night-kwh'] = hh['msp-kwh']
                bill_hh['night-gbp'] = hh['msp-kwh'] * 0.05
            else:
                bill_hh['day-kwh'] = hh['msp-kwh']
                bill_hh['day-gbp'] = hh['msp-kwh'] * 0.1
    
						bill_hh['net-gbp'] = sum(
								v for k, v in bill_hh.items() if k[-4:] == '-gbp')

				data_source.supplier_bill = reduce_bill_hhs(
						data_source.supplier_bill_hhs)
```

This will generate a simple virtual bill based on a day / night tariff.
Supplier contract scripts can be much more sophisticated than this, including
DUoS, TNUoS, BSUoS, RO and many other standard charges. These will be addressed
later on in this guide.

Also, don't worry about the 'properties' field for now.


### Add a Site

Go to the 'sites' link on the home page, and click 'add'. Fill out the form
and create the site.


### Add a Supply

To add a supply to a site, go to the site's page and click on 'edit'. Half-way
down the page there's an 'Insert an electricity supply' form. For a standard
electricity supply the 'source' is 'net'. Make sure the profile class (PC) is
'00' to indicate to Chellow that it's a half-hourly metered supply. The SSC
field is left blank for a half-hourly as they don't have an SSC.

A supply is formed from a series of eras. Each era has different
characteristics to capture the history of a supply.


### Run a Virtual Bill

At this stage it should be possible to run a virtual bill for the supply you've
added. Go to the supply's page and click on the 'Supplier Virtual Bill' link.
That should return a page showing the virtual bill for the supply.

Of course, the consumption will be zero because we haven't added in any
half-hourly data yet.


### Add Some HH Data

On the page of the supply you've created, you'll see that there's a 'channels'
link, with an 'add' link next to it. Add an active import channel for the
half-hourly data to be attached to.

Back on the supply page a link to the channel you just created will have
appeared. Click on this and fill out the form for adding a half-hour of data.

If you then re-run the virtual bill for the period in which you added the
half-hour, it should show up in the virtual bill.

It's tedious to add HH data one by one, so if you go to the page of the HHDC
contract that you've created, you'll see a 'HH Data Imports' link. Click on
this and there's a form for uploading HH data in bulk in a variety of formats.
Chellow can also be set up to import files automatically from an FTP server.


### Virtual Bills For A Contract

To see the virtual bills for a supplier contract, go to the contract page and
follow the Virtual Bills link.


###  Data Structure

  * Site
  * Supply
    * Supply Era
      * Site
      * MOP Contract
      * DC Contract
      * Profile Class
      * Imp / Exp Supplier Contract
      * Imp / Exp Mpan Core
      * Imp / Exp LLFC
      * Imp / Exp Supply Capacity
      * Imp / Exp Channels 
        * HH Data
  * Supplier Contracts (Same for DC and MOP) 
    * Rate Scripts
    * Batches 
      * Bills 
        * Supply
        * Register Reads
  * DNOs (Distribution Network Operators) 
    * LLFCs (Line Loss Factor Classes)


### General Imports

The menu has a link called 'General Import' which take you to a page for doing
bulk insert / update / delete operations on Chellow data (eg. Sites, Supplies,
LLFCs etc.) using a CSV file.


## Common Tasks

### Merging Two Supplies

Say there are two supplies A and B, and you want to end up with just A. The
steps are:

1. Back up the data by taking a snapshot of the database.
2. Check that A and B have the same header data (LLFC, MTC etc).
3. See if there are any overlapping channels, eg. do both A and B have import
   kVArh? If there are, then decide which one is going to be kept.
4. Load the hh data for the required channels from the backup file. First
   take a copy of the file, then edit out the data you don't want, then
   further edit the file so that it loads into the new supply.
5. Delete supply B.


### Local Reports

Core reports come with Chellow, but it's possible for users to create custom
reports. Reports are written in Python, and often use a Jinja2 template. You
can display a link to a report of user reports by adding the `local_reports_id`
to the `configuration` non-core contract.


#### Default users

Default users can be automatically assigned to requests from certain IP
addresses. To associate an IP address to a user, go to the non-core contract
`configuration` and add a line to the 'properties' field similar to the
following:

```
  {
    'ips': {'127.0.0.1': 'implicit-user@localhost'}
  }
```

Note that multiple IP addresses can be mapped to the same user.

It's also possible to use Microsoft Active Directory to authenticate users
with a reverse proxy server. Edit the `configuration` non-core contract and add
something like:

```
  {
    "ad_authentication": {
      "default_user": "readonly@example.com",
      "on": true
  }
```


## Design Decisions

Why don't you use the +/- infinity values for timestamps? The problem is that it's not clear how this would translate into Python. So we currently use null for infinity, which naturally translates into None in Python. 
