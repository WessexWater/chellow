Chellow
=======

Web site: http://chellow.wikispaces.com/


License
-------
Chellow is released under the GPL.


Requirements
------------
PostgreSQL 8.4.2 with JDBC Driver PostgreSQL 8.4 JDBC4 (build 701)
OpenJDK 6b16
Apache Tomcat 6


Installation
------------
1. Create an SQL database called chellow.
2. In your Tomcat, configure a JNDI JDBC datasource called jdbc/chellow. See the
    file context.xml in the same directory as this file.
3. Deploy the file chellow.war on your servlet container.


Upgrade From Version 357
------------------------
1. Copy the report at the bottom of this file, and run it with the following parameters to export the user data:

/reports/<report number>/output/?is_core=false&has-reports=true&has-supplier-contracts=true&has-hhdc-contracts=true&has-sites=true&has-supplies=true&has-hh-data=true&has-users=true&has-configuration=true&has-channel-snag-ignorals=true&mpan-core=

2. Install Chellow afresh with a blank database.
3. Import the user data by going to General Imports section.