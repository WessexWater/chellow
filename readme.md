## Chellow Manual


###  Licence

Chellow is released under the [GPL v3](http://www.gnu.org/licenses/gpl.html).


###  Introduction

Chellow is a web application for checking UK electricity bills. It's designed
for organizations with high electricity consumption. The software is hosted at
 https://bitbucket.org/ww_tlocke/chellow)

### Installation

####  Requirements

1. [Download](https://bitbucket.org/ww_tlocke/chellow/downloads) the latest version of Chellow.
2.  Make sure the following are installed: 
    * PostgreSQL 9.1 with the JDBC4 PostgreSQL Driver, Version 9.2-1002
    * OpenJDK 1.7.0_25 (in server mode)
    * Apache Tomcat 7.0.39

####  Brand New Installation 

Environment variables:

PGUSER default `postgres`.
PGPASSWORD default `postgres`
PGPORT default `5432`
PGDATABASE default `chellow`
PGHOST default `localhost`



1.  Create a PostgreSQL database called `chellow`. If you're upgrading, the
    database will already exist, so skip this step.
2.  In your Tomcat, configure a JNDI JDBC data source called jdbc/chellow.
    1. Add the following snippet to the `context.xml` file in the Tomcat configuration directory: 

        <Resource name="jdbc/chellow" auth="Container"
            type="javax.sql.DataSource" username="postgres" password="hello"
    	    driverClassName="org.postgresql.Driver"
            url="jdbc:postgresql://localhost:5432/chellow" maxActive="8" maxIdle="4"
            accessToUnderlyingConnectionAllowed="true" defaultTransactionIsolation="8"
            readOnly="true" />
            
        <Parameter name="db.username" value="postgres"/>
        <Parameter name="db.password" value="hello"/>

    2.  Put the [JDBC driver](http://jdbc.postgresql.org/download/postgresql-9.2-1002.jdbc4.jar) in the Tomcat `/lib/` directory.
3.  Deploy the file chellow.war to Tomcat.

####  Upgrading From A Previous Installation

1.  Deploy the file chellow.war to Tomcat.


####  Regression Plan

If the upgrade fails:

1.   Shut down Tomcat.
2.   Restore the database from the latest backup.
3.   Install the previous chellow.war
4.   Restart Tomcat.


###  Getting Started

This is a brief guide to setting things up after you've installed Chellow.

#### View the Chellow home page

Assuming you've installed Chellow correctly, you should be able to open your
browser, type in the URL of the Chellow application, and see the Chellow home
page.


#### Users

Before any users are added, if you access Chellow from `localhost` you'll have
read / write access. Once users are added, you have to log in as one of those
users. Users are added from the 'users' page.

Default users can be automatically assigned to requests from certain IP
addresses. To associate an IP address to a user, go to the non-core contract
`configuration` and add a line to the 'properties' field similar to the
following:

  {
    'ips': {'127.0.0.1': 'implicit-user@localhost'}
  }

Note that multiple IP addresses can be mapped to the same user.

#### Add Sites

Sites can be added by hand from the the 'sites' link on the home page. If
you've got a lot to enter, then you can import them using a CSV file.

#### Add Supplier Contracts

Click on 'supplier contracts' link and then fill out the 'Add a contract'
form. For the Charge Script field enter:

    
    
    def virtual_bill(data_source):
        data_source.supplier_bill['net-gbp'] = 0

This is the simplest possible virtual bill. To help with debugging you can
print things out to the CSV file:

    
    
    def virtual_bill(data_source):
        data_source.pw.println('The start date is ' +
	     str(data.source.start_date))
        data_source.supplier_bill['net-gbp'] = 0

To use half-hourly data to generate a bill based on a day / night tariff, you
can write:

    
    
    from net.sf.chellow.billing import NonCoreContract
    
    def virtual_bill(data_source):
        bill = data_source.supplier_bill 
    
        for hh in data_source.hh_data:
            if 0 < hh['utc-decimal-hour'] < 8:
                bill['night-kwh'] += hh['msp-kwh']
                bill['night-gbp'] += hh['msp-kwh'] * 0.05
            else:
                bill['day-kwh'] += hh['msp-kwh']
                bill['day-gbp'] += hh['msp-kwh'] * 0.1
    
        bill['net-gbp'] = sum(v for k, v in bill.iteritems() if k[-4:] == '-gbp')

For documentation on the languages that Chellow uses, see the Extending
Chellow section.

#### Add HHDC Contracts

In the Properties text area you can set up a process that will check an FTP
server every hour and download any new HH data files. Here's an example:

    
    
    has.importer=yes
    file.type=.bg.csv
    hostname=data.example.com
    username=auser
    password=apassword
    directory0=.
    mpan.map=searchtext>replacetext

####  Add Supplies

Supplies are imported in a similar way to sites above.

  * Source - Where the supply gets its electricity from. 

net

    The DNO's network.
gen

     Generator that's embedded within the site, so that the electricity generated displaces the electricity that would otherwise have to be imported from the DNO's network. 

lm

    Load management generator
chp

    Combined heat and power.
turb

    Water turbine.
gen-net

    Generator that's directly connected to the DNO's network, so everything generated is exported to the network, and all parasitic electricity (imported by the generator) is imported from the network. Cf the source 'gen'. The generator types are the same as those available for the source 'gen'.
sub

    general sub-meter used for energy management.
3rd-party

    Where the electricity is from (or to) a party that is not the DNO.
3rd-party-reverse

    As 3rd-party, but where the meter's import is measuring the export to the 3rd party.

#### Import HH data

HH data can be imported in a variety of formats. Chellow can also be set up to
import files automatically from an FTP server.

#### Virtual Bills

To see the virtual bills for a supplier contract, go to the contract page and
follow the Virtual Bills link.

####  Example Site

To set up an example site, insert a HHDC called 'IMSERV HH' with provider UKDC
starting at 2010-06-01 and insert a supplier contract called 'SSE HH' with
provider SOUT starting at 2010-05-01. Then save the General Import Format text
below as a file with the extension '.csv' and then import it using the General
Imports form. It'll insert a site with a CHP supply and a supply from the
network. It'll also put in some HH data for the beginning of October 2010.

    
    
    		
    "insert","site",78342,"Stowford Manor"
    "insert","supply",78342,"net",,"Main","_L","2010-10-01",,,,"IMSERV HH",2,"TRUE","TRUE","TRUE","TRUE","PO98881",0,845,5,,"22 0000 0000 111",520,200,"SSE HH",933,"22 00000000120",521,80,"SSE HH",45
    "insert","hh-datum","22 0000 0000 111","2010-10-01","TRUE","TRUE","22,A,0,A,59,A,105,A,0,A,0,A,8,A,114,A,0,A,52,A,0,A,7,A,23,A,23,A,36,A,112,A,0,A,0,A,0,A,24,A,0,A,7,A,57,A,48,A,0,A,96,A,57,A,66,A,0,A,85,A,0,A,8,A,0,A,123,A,0,A,0,A,84,A,0,A,21,A,0,A,19,A,47,A,0,A,0,A,24,A,0,A,0,A,5,A,1,A,0,A,0,A,11,A,0,A,0,A,0,A,14,A,0,A,111,A,0,A,24,A,105,A,0,A,5,A,2,A,0,A,0,A,0,A,0,A,43,A,94,A,0,A,0,A,0,A,2,A,17,A,36,A,27,A,0,A,0,A,13,A",,,,,,,,,,,,,,,,,,,,,,,,,
    "insert","hh-datum","22 0000 0000 111","2010-10-01","FALSE","TRUE","0,A,57,A,0,A,0,A,45,A,81,A,0,A,0,A,54,A,0,A,114,A,0,A,0,A,0,A,0,A,0,A,54,A,29,A,126,A,0,A,2,A,0,A,0,A,0,A,33,A,0,A,0,A,0,A,88,A,0,A,72,A,0,A,55,A,0,A,19,A,8,A,0,A,0,A,0,A,34,A,0,A,0,A,37,A,92,A,0,A,73,A,118,A,0,A,0,A,64,A,83,A,0,A,14,A,103,A,20,A,0,A,57,A,0,A,58,A,0,A,0,A,32,A,0,A,0,A,8,A,12,A,88,A,82,A,0,A,0,A,55,A,31,A,74,A,0,A,0,A,0,A,0,A,99,A,44,A,0,A"
    "insert","supply",78342,"gen","chp","CHP","_L","2010-10-01",,,,"IMSERV HH",3,"TRUE","FALSE","TRUE","FALSE","PO6755",0,845,5,,"99 0000 0000 015",510,100,"SSE HH",6,,,80,"SSE HH",45
    "insert","Hh-datum","99 0000 0000 015","2010-10-01",TRUE,TRUE,"62,A,82,A,24,A,29,A,63,A,115,A,81,A,6,A,150,A,33,A,131,A,51,A,14,A,102,A,30,A,37,A,113,A,40,A,146,A,87,A,29,A,19,A,60,A,90,A,79,A,20,A,48,A,20,A,143,A,29,A,138,A,135,A,129,A,19,A,41,A,125,A,2,A,123,A,92,A,131,A,96,A,65,A,149,A,139,A,114,A,97,A,147,A,56,A,136,A,99,A,140,A,26,A,31,A,136,A,113,A,3,A,148,A,15,A,131,A,102,A,42,A,34,A,82,A,39,A,43,A,35,A,92,A,104,A,37,A,56,A,143,A,119,A,122,A,94,A,105,A,111,A,118,A,149,A,82,A,15,A"
    
    	

####  Data Model

  * Sites
  * Supplies 
    * Supply Generations 
      * Site
      * Supplier Contract
      * DC Contract
      * Channels 
        * HH Data
      * Profile Class
      * Import / Export 
        * Mpan Core
        * LLFC
        * Supply Capacity
  * Supplier Contracts (Same for DC and MOP) 
    * Rate Scripts
    * Batches 
      * Bills 
        * Supply
        * Register Reads
  * DNOs (Distribution Network Operators) 
    * LLFCs (Line Loss Factor Classes)

###  General Import Formats

#### Key points when importing

  * Lines beginning with the '#' character are comment lines.
  * You can import any number of lines, and mix actions and types in a single
    file.
  * When updating a record, if the field contains {no change}, then that field
    won't be updated.
  * A blank date field means 'ongoing'.



Action | Type
------|------|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--|--
*insert* | *site* | Site Code  | Site Name
*delete* | *site* | Site Code
*update* | *site* | Current Site Code  | New Site Code  | Site Name
*insert* | *supply* | Site Code | Source Code  | Generator Type  | Supply Name | GSP Group (geographic location)  | Start date (yyyy-MM-dd)  | Finish Date  | MOP Contract  | MOP Account  | HHDC Contract  | HHDC Account | Meter Serial Number  | Profile Class  | Meter Timeswitch Class  | CoP  | Standard Settlement Configuration (blank for HH supplies)  | Import MPAN Core  | Import LLFC  | Import Supply Capacity  | Import Supplier Contract  | Import Supplier Account  | Export MPAN Core  | Export LLFC  | Export Supply Capacity  | Export Supplier Contract  | Export Supplier Account
*update* | *supply* | MPAN Core | Source Code  | Generator Type  | Supply Name | GSP Group
*insert* | *era* | MPAN Core | Start date (yyyy-MM-dd)  | Site Code  | MOP Contract  | MOP Account  | HHDC Contract  | HHDC Account | Meter Serial Number  | Profile Class  | MTC  | CoP  | SSC  | Import MPAN Core  | Import LLFC  | Import Supply Capacity  | Import Supplier Contract  | Import Supplier Account  | Import ACTIVE? | Import REACTIVE_IMP? | Import REACTIVE_EXP? | Export MPAN Core  | Export LLFC  | Export Supply Capacity  | Export Supplier Contract  | Export Supplier Account | Export ACTIVE? | Export REACTIVE_IMP? | Export REACTIVE_EXP?
*update* | *era* | MPAN Core | Date  | Start date  | Finish date  | MOP Contract  | MOP Account  | HHDC Contract  | HHDC Account | Meter Serial Number  | Profile Class  | MTC  | CoP  | SSC  | Import MPAN Core  | Import LLFC  | Import Supply Capacity  | Import Supplier Contract  | Import Supplier Account  | Export MPAN Core  | Export LLFC  | Export Supply Capacity  | Export Supplier Contract  | Export Supplier Account
*delete* | *era* | MPAN Core | Date
*insert* | *channel* | MPAN Core | Date (yyyy-MM-dd hh:mm)  | Import Related?  | Channel Type ('active', 'reactive import', 'reactive export'
*delete* | *channel* | MPAN Core | Date  | Import Related?  | Channel Type ('active', 'reactive import', 'reactive export'
*insert* | *site_era* | Site Code | Core MPAN  | Era Start Date  | Is Physical?
*insert* | *hh_datum* | MPAN Core | Date  | Channel Type  | Value | Status
*insert* | *user* | Email Address | Password  | Password Digest  | User Role  | Participant Code  | Role Code
*update* | *user* | Current Email Address  | Email Address  | Password  | Password Digest  | User Role  | Participant Code  | Role Code
*insert* | *channel_snag_ignore* | MPAN Core  | Is Import?  | Is kWh?  | Description  | From  | To
*insert* | *site_snag_ignore* | Site Code  | Description  | From  | To
*insert* | *batch* | Role Name (hhdc, supplier or mop)  | Contract Name  | Reference  | Description
*update* | *batch* | Role Name (hhdc, supplier or mop)  | Contract Name  | Old Reference  | New Reference  | Description
*insert* | *bill* | Role Name(hhdc, supplier or mop)  | Contract Name  | Batch Reference  | Mpan Core  | Issue Date  | Start Date  | Finish Date  | Net  | Vat  | Gross  | Account Reference  | Reference  | Type  | Breakdown  | Kwh  | (Meter Serial Number  | Mpan  | Coefficient  | Units  | TPR  | Previous Date  | Previous Value  | Previous Type  | Present Date  | Present Value  | Present Type)*
*update* | *bill* | Chellow Id  | Account  | Reference  | Issue Date  | Start Date  | Finish Date  | kwh  | Net  | Vat  | Type  | Paid?  | Breakdown
*update* | *register_read* | Chellow Id  | TPR  | Coefficient  | Units  | Meter Serial Number  | MPAN  | Previous Date  | Previous Value  | Previous Type  | Present Date  | Present Value  | Present Type
*insert* | *llfc* | DNO Code | LLFC Code | LLFC Description | Voltage Level Code | Is Substation? | Is Import? | Valid From | Valid To
*delete* | *llfc* | DNO Code | LLFC Code | Date

###  HH Data Formats

Below are all the HH data formats accepted by Chellow. Chellow recognizes them
by their filename extension. The files may be compressed as zip files.

#### Stark DF2

File extension '.df2'.

The data file is of the form:

    
    
    		#F2
    #O 99 9999 9999 999
    #S 2
    27/07/05,00:30,95.4,A
    27/07/05,01:00,93.8,A
    27/07/05,01:30,91.9,A
    	
Values Of The Sensor Number 'S'

Number | Meaning
-------|-------------
1      | Import kWh
2      | Export kWh
3      | Import kVArh
4      | Export kVArh

and the status character on the end is optional.

#### CSV Simple

File extension '.simple.csv'.

A CSV file with the following columns

Name         | Description
-------------|----------------------------------------------------------------
MPAN Core    |
Channel Type | 'ACTIVE', 'REACTIVE_IMP' or 'REACTIVE_EXP'
Time         | Half-hour starting yyyy-MM-dd hh:mm
Value        | 
Status       | 'A' - actual, 'E' - estimate, 'C' - padding.
	
Here's an example:

    MPAN core, Is Import?, Is kWh?, Time, Value, Status
    99 9999 9999 999, ACTIVE, 2006-01-01T00:30Z, 218.4 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T01:00Z, 220.4 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T01:30Z, 221.8 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T02:00Z, 223.4 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T02:30Z, 224.6 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T03:00Z, 226.8 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T03:30Z, 203.8 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T04:00Z, 155.2 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T04:30Z, 169.0 , E
    99 9999 9999 999, ACTIVE, 2006-01-01T05:00Z, 171.0 , E


#### bGlobal CSV

File extension '.bg.csv'.

A CSV file with the following columns:

Name                | Description
--------------------|---------------
MPAN core           | 
Meter Serial Number | 
Date                | dd/MM/yy
HH 1                | kWh in 1st HH
HH 2                | kWh in 2nd HH
HH 3                | kWh in 3rd HH
...                 | ...
HH 48               | kWh in 48th HH

	
Here's an example:

    9999999999999,E04M00872,06/07/2008,0.262,0.26,0.252,0.246,0.249,0.251,0.25,0.249,0.244,0.239,0.255,0.255,0.286,0.289,0.356,0.489,0.576,0.585,0.496,0.411,0.457,0.463,0.436,0.447,0.436,0.431,0.439,0.396,0.455,0.453,0.377,0.314,0.341,0.338,0.418,0.45,0.446,0.442,0.464,0.366,0.314,0.386,0.395,0.444,0.346,0.288,0.263,0.255,0,0
    9999999999999,E04M00872,07/07/2008,0.247,0.216,0.211,0.227,0.237,0.233,0.229,0.204,0.225,0.267,0.301,0.324,0.466,0.471,0.475,0.546,0.505,0.382,0.362,0.434,0.387,0.395,0.35,0.378,0.348,0.356,0.301,0.34,0.337,0.396,0.386,0.388,0.369,0.325,0.356,0.36,0.367,0.429,0.427,0.466,0.404,0.403,0.319,0.359,0.299,0.294,0.264,0.29,0,0
    9999999999999,E04M00872,08/07/2008,0.312,0.31,0.254,0.237,0.222,0.226,0.218,0.211,0.225,0.263,0. 262,0.283,0.423,0.495,0.561,0.569,0.496,0.41,0.381,0.355,0.323,0.366,0.4,0.363,0.381,0.396, 0.392,0.369,0.317,0.301,0.378,0.311,0.391,0.345,0.344,0.382,0.436,0.384,0.353,0.34,0.335,0.352,0.388,0.394,0.389,0.346,0.284,0.258,0,0
    9999999999999,E04M00872,09/07/2008,0.246,0.246,0.257,0.266,0.251,0.24,0.229,0.236,0.232,0.245,0.268,0.289,0.424,0.46, 0.513,0.481,0.459,0.441,0.368,0.348,0.401,0.403,0.413,0.412,0.371,0.396,0.381,0.321,0.321,0.276,0.303,0.311,0.348,0.33,0.381,0.398,0.372,0.38,0.322,0.342,0.349,0.331,0.439,0.41,0.368,0.326,0.274,0.257,0,0
    9999999999999,E04M00872,10/07/2008,0.247,0.247,0.242,0.251,0.243,0.254,0.25,0.243,0.245,0.246,0.252,0.336,0.378,0.49,0.443, 0.467,0.544,0.467,0.375,0.387,0.403,0.347,0.415,0.404,0.422,0.42,0.375,0.385,0.371, 0.371,0.359,0.397,0.402,0.384,0.393,0.389,0.365,0.381,0.498,0.402,0.355,0.326,0.311,0.31,0.342,0.274,0.293,0.313,0,0
    9999999999999,E04M00872,11/07/2008,0.303,0.303,0.277,0.244,0.254,0.24,0.249,0.256,0.318,0.318,0.305, 0.299,0.421,0.529,0.547,0.452,0.458,0.423,0.433,0.377,0.344,0.401,0.417,0.392,0.364,0.373,0.367,0.376,0.387,0.378,0.521,0.525,0.413,0.42,0.377,0.42,0.367,0.371,0.336,0.341,0.336,0.4,0.413,0.401,0.407,0.376,0.353,0.338,0,0
    9999999999999,E04M00872,12/07/2008,0.324,0.319,0.31,0.31,0.312,0.282,0.232,0.244,0.246,0.252,0.268,0.286,0.329, 0.378,0.547,0.444,0.447,0.535,0.631,0.556,0.473,0.503,0.47,0.402,0.419,0.443,0.442, 0.409,0.378,0.366,0.384,0.392,0.403,0.406,0.481,0.541,0.486,0.405,0.366,0.364, 0.364,0.43,0.436,0.386,0.402,0.322,0.279,0.291,0,0
    9999999999999,E04M00872,13/07/2008,0.268,0.272,0.261,0.25,0.311,0.306,0.267,0.259,0.26,0.3,0.333,0.326,0.362, 0.37,0.448,0.458,0.567,0.664,0.781,0.609,0.529,0.566,0.464,0.366,0.388,0.423,0.357,0.41, 0.352,0.357,0.486,0.547,0.52,0.516,0.558,0.639,0.607,0.65,0.637,0.483,0.457,0.51,0.444,0.422,0.442,0.4,0.314,0.347,0,0
    9999999999999,E04M00872,14/07/2008,0.32,0.344,0.261,0.304,0.309,0.239,0.302,0.312,0.26,0.334,0.265,0.444,0.488, 0.552,0.543,0.58,0.599,0.501,0.497,0.48,0.334,0.376,0.409,0.405,0.314,0.303, 0.329,0.369,0.299,0.436,0.48,0.527,0.499,0.549,0.37,0.373,0.347,0.339,0.348, 0.412,0.425,0.385,0.423,0.376,0.373,0.353,0.281,0.27,0,0
    9999999999999,E04M00872,15/07/2008,0.314,0.309,0.298,0.29,0.291,0.236,0.244,0.24,0.239,0.246,0.265,0.308, 0.414,0.428,0.504,0.527,0.472,0.35,0.483,0.485,0.543,0.519,0.45,0.345,0.347, 0.375,0.455,0.509,0.498,0.469,0.304,0.329,0.413,0.397,0.445,0.534,0.506,0.405, 0.447,0.422,0.48,0.42,0.431,0.418,0.387,0.365,0.281,0.263,0,0
    9999999999999,E04M00872,16/07/2008,0.279,0.313,0.316,0.314,0.311,0.311,0.303,0.287,0.239,0.261,0.269, 0.342,0.446,0.491,0.445,0.556,0.503,0.463,0.412,0.407,0.472,0.445,0.417,0.394, 0.391,0.368,0.403,0.384,0.37,0.316,0.39,0.353,0.442,0.424,0.555,0.477,0.525, 0.476,0.39,0.464,0.465,0.399,0.427,0.432,0.428,0.371,0.333,0.269,0,0
    
    	

###  Importing Bills

To import bills for a particular contract, create a batch, and then upload the
bill file. The following electricity bill formats can be imported. Chellow
recognizes the format by the file extension.

Format                 | Extension
-----------------------|----------
EDF Energy Proprietary | mm
CSV                    | csv
BGB EDI File           | bgb.edi
SSE EDI File           | sse.edi
GDF CSV                | gdf.csv

#### CSV Format

CSV file with the following columns:

# Bill Type                           | Account Reference | Mpans | Invoice Reference | Issue Date       | Start Date       | Finish Date      | kWh | Net | VAT | Gross | Breakdown | R1 Meter Serial Number | R1 MPAN | R1 Coefficient | R1 Units              | R1 TPR             | R1 Previous Read Date | R1 Previous Read Value | R1 Previous Read Type | R1 Present Read Date | R1 Present Read Value | R1 Present Read Type
--------------------------------------|-------------------|-------|-------------------|------------------|------------------|------------------|-----|-----|-----|-------|-----------|------------------------|---------|----------------|-----------------------|--------------------|-----------------------|------------------------|-----------------------|----------------------|-----------------------|---------------------
N - Normal, W - Withdrawn or F -Final |                   |       |                   | YYYY-mm-dd HH:MM | YYYY-mm-dd HH:MM | YYYY-mm-dd HH:MM |     |     |     |       |           |                        |         |                | kWh, kW, kVA or kVArh | Blank if kW or kVA |                       |                        |                       |                      |                       |                     


#### Read Types

Chellow Code | Chellow Description | sse.edi Code | sse.edi Description                      | bgb.edi Code | bgb.edi Description
-------------|---------------------|--------------|------------------------------------------|--------------|-------------------------
N            | Normal              | 00           | Normal Reading                           | 00           | Normal Reading - Default
N3           | Normal 3rd Party    | 09           | Third Party Normal Reading               |              |
C            | Customer            | 04           | Customer's Own Reading                   | 04           | Customer's own reading
E            | Estimated           | 02           | Estimated (Computer) Reading             | 02           | Estimated (computer)
E3           | Estimated 3rd Party | 11           | Third Party Estimated (Computer) Reading |              |
EM           | Estimated Manual    | 01           | Estimated (manual)                       |              |
W            | Withdrawn           | 03           | Removed meter reading                    |              |
X            | Exchange            | 06           | Exchange Meter Reading                   | 06           | Exchange Meter Reading
CP           | Computer            | 05           | Computer Reading                         |              | 
IF           | Information         | 12           | Reading for Information only             |              |


###  Common Tasks

#### Merging Two Supplies

Say there are two supplies A and B, and you want to end up with just A. The
steps are:

  1. Back up the data by taking a snapshot of the database.
  2. Check that A and B have the same header data (LLFC, MTC etc).
  3. See if there are any overlapping channels, eg. do both A and B have import kVArh? If there are, then decide which one is going to be kept.
  4. Load the hh data for the required channels from the backup file. First take a copy of the file, then edit out the data you don't want, then further edit the file so that it loads into the new supply.
  5. Delete supply B.

###  Reports

Name                         | Description
-----------------------------|-------------------------------------------------------------------------------------------------------------
metered-import-*             | Uses HH data for HH and AMR supplies, and register reads	for dumb NHH supplies.
metered-import-estimated-kwh | For HH data, the kWh with the 'E' flag.
billed-import-*              | A daily rate is calculated for a bill, and applied to the number of days it covers of the month in question.


#### Supplies Monthly Duration

Here's how Chellow calculates the monthly consumption for dumb NHH supplies.
First it finds the closest normal reads. Let's assume there are just two for
simplicity. For each TPR, Chellow works out the (historical kWh / hh) = (kWh
between the two reads) / (number of HHs between the two reads). Then Chellow
finds the number of HHs between the beginning of the month and the end of the
month, and also the number of HHs that fall within the TPR, between the
beginning and and of the month. The kWh for each half hour in the month for
each TPR is (historical kWh / hh) * (month half-hours) / (month half-hours
within TPR).

#### Bills

A row for each bill that falls within the given period.

#### Local Reports

Core reports come with Chellow and have odd ids. User reports have even
numbers. You can display a link to a report of user reports by adding the
following line to the configuration:

    
    
    local.reports=82
    

replacing 82 with the id of the report of reports that you've created.

###  Extending Chellow

It's easiest to get started extending Chellow using reports. The core of
Chellow is written in Java. I work with the Java code, using:

  * [Eclipse](http://www.eclipse.org/)
  * Git
  * [Ant](http://ant.apache.org/), with a build.properties file containing 
    
    
    				
    catalina.home=/usr/share/tomcat7
    test.port=8080
    manager.username=xxx
    manager.password=xxx
    
    

  * Testing is done with [Imprimatur](https://imprimatur.wikispaces.com/).
  * 
  * Reports are written in [Python 2.5](http://www.python.org/). 
  * [HTML 5](http://www.w3.org/html/wg/drafts/html/master/Overview.html)

### Design Decisions

Why don't you use the +/- infinity values for timestamps? The problem is that it's not clear how this would translate into Python. So we currently use null for infinity, which naturally translates into None in Python. 
