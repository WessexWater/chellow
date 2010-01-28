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
2. In your servlet container, configure a JNDI JDBC datasource called jdbc/chellow.
3. Deploy the file chellow.war on your servlet container.


Upgrade
-------
To upgrade from version 355, shut down Tomcat and install the new version of Chellow,
then restart Tomcat.