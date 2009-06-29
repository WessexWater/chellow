/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/
package net.sf.chellow.ui;

import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Properties;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.Logger;

import javax.naming.InitialContext;
import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import javax.sql.DataSource;

import net.sf.chellow.billing.DsoContract;
import net.sf.chellow.billing.NonCoreContract;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.hhimport.AutomaticHhDataImporters;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.MonadFormatter;
import net.sf.chellow.monad.MonadHandler;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.physical.ClockInterval;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.GeneratorType;
import net.sf.chellow.physical.GspGroup;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.MeasurementRequirement;
import net.sf.chellow.physical.MeterPaymentType;
import net.sf.chellow.physical.MeterType;
import net.sf.chellow.physical.Mtc;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.Pc;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.Ssc;
import net.sf.chellow.physical.Tpr;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.UserRole;
import net.sf.chellow.physical.VoltageLevel;

import org.hibernate.tool.hbm2ddl.SchemaUpdate;
import org.python.util.PythonInterpreter;

public class ContextListener implements ServletContextListener {
	private ServletContext context = null;

	private MonadContextParameters monadParameters;

	private Logger logger = Logger.getLogger("net.sf.chellow");

	public void contextInitialized(ServletContextEvent event) {
		context = event.getServletContext();
		Monad.setContext(context);
		try {
			LogManager.getLogManager().getLogger("").setLevel(Level.SEVERE);
			FileHandler fh = new FileHandler("%t/chellow.log");

			fh.setFormatter(new MonadFormatter());
			logger.addHandler(fh);
			monadParameters = new MonadContextParameters(context);
			logger.addHandler(new MonadHandler(monadParameters));
			context.setAttribute("monadParameters", monadParameters);
			InitialContext cxt = new InitialContext();
			if (cxt == null) {
				throw new Exception("Uh oh -- no context!");
			}

			DataSource ds = (DataSource) cxt
					.lookup("java:/comp/env/jdbc/chellow");

			if (ds == null) {
				throw new Exception("Data source not found!");
			}
			Connection con = ds.getConnection();
			Statement stmt = con.createStatement();

			// Find if DB has been created
			try {
				stmt.executeQuery("select properties from configuration;");
			} catch (SQLException sqle) {
				initializeDatabase(con);
				Hiber.close();
			} finally {
				con.close();
			}
			// Configuration config = Configuration.getConfiguration();
			/*
			 * String pythonPath = config .getChellowProperty("python.path");
			 */
			AutomaticHhDataImporters.start();
			Properties postProps = new Properties();
			// postProps.setProperty("python.path", pythonPath);
			PythonInterpreter.initialize(System.getProperties(), postProps,
					new String[] {});
		} catch (Throwable e) {
			logger.logp(Level.SEVERE, "ContextListener", "contextInitialized",
					"Can't initialize context. " + e.getMessage(), e);
		}
		Debug.print("Finished initializing context.");
	}

	public void contextDestroyed(ServletContextEvent event) {
	}

	private void initializeDatabase(Connection con) throws HttpException {
		SchemaUpdate su = new SchemaUpdate(Hiber.getConfiguration());
		su.execute(false, true);
		/*
		 * List<Exception> exceptions = su.getExceptions(); if
		 * (exceptions.size() > 0) { for (Exception exception : exceptions) {
		 * exception.printStackTrace(); } throw new ProgrammerException("Errors
		 * in schema generation."); }
		 */
		try {
			Statement stmt = con.createStatement();
			stmt
					.execute("ALTER TABLE contract ALTER COLUMN charge_script TYPE text;");
			stmt
					.execute("ALTER TABLE rate_script ALTER COLUMN script TYPE text;");
			stmt.execute("create index description_idx on snag (description)");
			stmt.execute("create index is_ignored_idx on snag (is_ignored)");
			stmt.execute("create index snag_id_idx on channel_snag (snag_id)");
			stmt
					.execute("create index channel_id_idx on channel_snag (channel_id)");
			stmt
					.execute("create index start_date_idx on channel_snag (start_date)");
			stmt
					.execute("create index finish_date_idx on channel_snag (finish_date)");
			stmt
					.execute("CREATE INDEX site_snag__finish_date ON site_snag (finish_date);");
			stmt
					.execute("CREATE INDEX site_snag__site_id ON site_snag (site_id);");
			stmt
					.execute("CREATE INDEX site_snag__snag_id_idx ON site_snag (snag_id);");
			stmt
					.execute("CREATE INDEX site_snag__start_date ON site_snag (start_date);");
			stmt
					.execute("CREATE UNIQUE INDEX channel_date ON hh_datum (channel_id, end_date);");
			stmt.execute("ALTER TABLE report ALTER COLUMN script TYPE text;");
			stmt.execute("ALTER TABLE report ALTER COLUMN template TYPE text;");

		} catch (SQLException e) {
			throw new InternalException(e);
		}
		Configuration.getConfiguration();
		Hiber.close();
		GspGroup.loadFromCsv(context);
		ReadType.loadFromCsv(context);
		Pc.loadFromCsv(context);
		MarketRole.loadFromCsv(context);
		Participant.loadFromCsv(context);
		Provider.loadFromCsv(context);
		DsoContract.loadFromCsv(context);
		VoltageLevel.insertVoltageLevels();
		Llfc.loadFromCsv(context);
		MeterType.loadFromCsv(context);
		MeterPaymentType.loadFromCsv(context);
		Mtc.loadFromCsv(context);
		Tpr.loadFromCsv(context);
		ClockInterval.loadFromCsv(context);
		Ssc.loadFromCsv(context);
		MeasurementRequirement.loadFromCsv(context);
		Report.loadReports(context);
		NonCoreContract.loadNonCoreContracts(context);
		Hiber.flush();
		UserRole.insertUserRole(UserRole.EDITOR);
		UserRole.insertUserRole(UserRole.PARTY_VIEWER);
		UserRole.insertUserRole(UserRole.VIEWER);
		User.insertUser(new EmailAddress("administrator@localhost"),
				"administrator", null, UserRole.getUserRole(UserRole.EDITOR),
				null);
		Hiber.commit();
		Source.insertSource(Source.NETWORK_CODE, "Public distribution system.");
		Source.insertSource(Source.SUBMETER_CODE, "Sub meter");
		Source.insertSource(Source.GENERATOR_NETWORK_CODE,
				"Generator connected directly to network.");
		Source.insertSource(Source.GENERATOR_CODE, "Generator.");
		Source.insertSource(Source.THIRD_PARTY_CODE, "Third party supply.");
		Source.insertSource(Source.THIRD_PARTY_REVERSE_CODE,
				"Third party supply with import going out of the site.");
		GeneratorType.insertGeneratorType("chp", "Combined heat and power.");
		GeneratorType.insertGeneratorType("lm", "Load management.");
		GeneratorType.insertGeneratorType("turb", "Water turbine.");
		Hiber.commit();
	}
	/*
	 * @SuppressWarnings("unchecked") private void upgrade11to12(Connection con)
	 * throws HttpException { try { Statement stmt = con.createStatement(); stmt
	 * .execute("COMMENT ON SCHEMA public IS 'Standard public schema'");
	 * stmt.execute("drop LANGUAGE plpgsql");
	 * 
	 * 
	 * 
	 * stmt.execute("delete * from account"); stmt.execute("alter table account
	 * drop organization_id"); stmt.execute("alter table account drop
	 * provider_id"); stmt.execute("alter table account add contract_id bigint
	 * not null");
	 * 
	 * stmt.execute("alter table account_snag rename service_id to
	 * contract_id");
	 * 
	 * stmt.execute("alter table batch rename service_id to contract_id");
	 * 
	 * stmt.execute("alter table bill drop service_id");
	 * 
	 * stmt.execute("alter table bill_snag rename service_id to
	 * supplier_contract_id");
	 * 
	 * ResultSet srs = stmt.executeQuery("select supply.id as supply_id from
	 * supply"); long supply_id; while (srs.next()) { supply_id =
	 * srs.getLong("supply_id"); ResultSet sgrs = stmt.executeQuery("select
	 * supply_generation_id as supply_generation_id,
	 * supply_generation.start_date, supply_generation.finish_date"); }
	 * PreparedStatement siteSupplyGenerationInsert = con
	 * .prepareStatement("insert into site_supply_generation (id, site_id,
	 * supply_generation_id, is_physical) values (?, ?, ?, ?)"); long
	 * siteSupplyGenerationId = 1; while (srs.next()) { long siteId =
	 * srs.getLong("site_id"); long supplyGenerationId =
	 * srs.getLong("supply_generation_id"); boolean isPhysical =
	 * srs.getBoolean("is_physical"); siteSupplyGenerationInsert.setLong(1,
	 * siteSupplyGenerationId); siteSupplyGenerationInsert.setLong(2, siteId);
	 * siteSupplyGenerationInsert.setLong(3, supplyGenerationId);
	 * siteSupplyGenerationInsert.setBoolean(4, isPhysical);
	 * siteSupplyGenerationInsert.execute(); siteSupplyGenerationId++; }
	 * srs.close(); /* stmt .execute("update meter_timeswitch set description =
	 * 'HH Code 5 and above (with Comms)', is_unmetered = false where code =
	 * '845'"); stmt .execute("update meter_timeswitch set description = 'HH
	 * Code 5 and above (without Comms)', is_unmetered = false where code =
	 * '846'"); stmt .execute("update meter_timeswitch set description = 'HH
	 * Code 6 A (with Comms)', is_unmetered = false where code = '847'"); stmt
	 * .execute("update meter_timeswitch set description = 'HH Code 6 B (with
	 * Comms)', is_unmetered = false where code = '848'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 6 C (with Comms)',
	 * is_unmetered = false where code = '849'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 6 D (with Comms)',
	 * is_unmetered = false where code = '850'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 6 A (without Comms)',
	 * is_unmetered = false where code = '851'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 6 B (without Comms)',
	 * is_unmetered = false where code = '852'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 6 C (without Comms)',
	 * is_unmetered = false where code = '853'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 6 D (without Comms)',
	 * is_unmetered = false where code = '854'"); stmt .execute("update
	 * meter_timeswitch set description = 'HH Code 7 (with Comms)', is_unmetered =
	 * false where code = '855'"); stmt .execute("update meter_timeswitch set
	 * description = 'HH Code 7 (without Comms)', is_unmetered = false where
	 * code = '856'");
	 */
	/*
	 * stmt .execute("CREATE TABLE site_supply_generation (id bigint NOT NULL,
	 * supply_generation_id bigint NOT NULL, site_id bigint NOT NULL,
	 * is_physical boolean NOT NULL);"); stmt .execute("CREATE SEQUENCE
	 * site_supply_generation_id_sequence INCREMENT BY 1 NO MAXVALUE NO MINVALUE
	 * CACHE 1;"); stmt .execute("ALTER TABLE ONLY site_supply_generation ADD
	 * CONSTRAINT site_supply_generation_pkey PRIMARY KEY (id);"); stmt
	 * .execute("ALTER TABLE ONLY site_supply_generation ADD CONSTRAINT
	 * fkey_site_supply_generation_site FOREIGN KEY (site_id) REFERENCES
	 * site(id);"); stmt .execute("ALTER TABLE ONLY site_supply_generation ADD
	 * CONSTRAINT fkey_site_supply_generation_supply_generation FOREIGN KEY
	 * (supply_generation_id) REFERENCES supply_generation(id);"); ResultSet srs =
	 * stmt .executeQuery("select site_supply.site_id as site_id,
	 * supply_generation.id as supply_generation_id, site_supply.is_physical as
	 * is_physical from site_supply, supply_generation where
	 * site_supply.supply_id = supply_generation.supply_id"); PreparedStatement
	 * siteSupplyGenerationInsert = con .prepareStatement("insert into
	 * site_supply_generation (id, site_id, supply_generation_id, is_physical)
	 * values (?, ?, ?, ?)"); long siteSupplyGenerationId = 1; while
	 * (srs.next()) { long siteId = srs.getLong("site_id"); long
	 * supplyGenerationId = srs.getLong("supply_generation_id"); boolean
	 * isPhysical = srs.getBoolean("is_physical");
	 * siteSupplyGenerationInsert.setLong(1, siteSupplyGenerationId);
	 * siteSupplyGenerationInsert.setLong(2, siteId);
	 * siteSupplyGenerationInsert.setLong(3, supplyGenerationId);
	 * siteSupplyGenerationInsert.setBoolean(4, isPhysical);
	 * siteSupplyGenerationInsert.execute(); siteSupplyGenerationId++; }
	 * srs.close(); stmt.execute("drop table site_supply"); stmt.execute("drop
	 * sequence site_supply_id_sequence"); stmt .executeQuery("select
	 * setval('site_supply_generation_id_sequence', max(id)) from
	 * site_supply_generation"); stmt.close();
	 */
	/*
	 * } catch (SQLException e) { e.printStackTrace(); } Debug.print("Finished
	 * upgrading."); // dataDelta(con); }
	 */
	/*
	 * private void upgrade09to10(Connection con) throws ProgrammerException {
	 * try { Statement stmt = con.createStatement(); stmt .execute("CREATE TABLE
	 * site_supply_generation (id bigint NOT NULL, supply_generation_id bigint
	 * NOT NULL, site_id bigint NOT NULL, is_physical boolean NOT NULL);"); stmt
	 * .execute("CREATE SEQUENCE site_supply_generation_id_sequence INCREMENT BY
	 * 1 NO MAXVALUE NO MINVALUE CACHE 1;"); stmt .execute("ALTER TABLE ONLY
	 * site_supply_generation ADD CONSTRAINT site_supply_generation_pkey PRIMARY
	 * KEY (id);"); stmt .execute("ALTER TABLE ONLY site_supply_generation ADD
	 * CONSTRAINT fkey_site_supply_generation_site FOREIGN KEY (site_id)
	 * REFERENCES site(id);"); stmt .execute("ALTER TABLE ONLY
	 * site_supply_generation ADD CONSTRAINT
	 * fkey_site_supply_generation_supply_generation FOREIGN KEY
	 * (supply_generation_id) REFERENCES supply_generation(id);"); ResultSet srs =
	 * stmt .executeQuery("select site_supply.site_id as site_id,
	 * supply_generation.id as supply_generation_id, site_supply.is_physical as
	 * is_physical from site_supply, supply_generation where
	 * site_supply.supply_id = supply_generation.supply_id"); PreparedStatement
	 * siteSupplyGenerationInsert = con .prepareStatement("insert into
	 * site_supply_generation (id, site_id, supply_generation_id, is_physical)
	 * values (?, ?, ?, ?)"); long siteSupplyGenerationId = 1; while
	 * (srs.next()) { long siteId = srs.getLong("site_id"); long
	 * supplyGenerationId = srs.getLong("supply_generation_id"); boolean
	 * isPhysical = srs.getBoolean("is_physical");
	 * siteSupplyGenerationInsert.setLong(1, siteSupplyGenerationId);
	 * siteSupplyGenerationInsert.setLong(2, siteId);
	 * siteSupplyGenerationInsert.setLong(3, supplyGenerationId);
	 * siteSupplyGenerationInsert.setBoolean(4, isPhysical);
	 * siteSupplyGenerationInsert.execute(); siteSupplyGenerationId++; }
	 * srs.close(); stmt.execute("drop table site_supply"); stmt.execute("drop
	 * sequence site_supply_id_sequence"); stmt .executeQuery("select
	 * setval('site_supply_generation_id_sequence', max(id)) from
	 * site_supply_generation"); stmt.close(); } catch (SQLException e) {
	 * e.printStackTrace(); } Debug .print("Finished first part of upgrading,
	 * going on to initialize database..."); initializeDatabase(con); }
	 */
	/*
	 * private void upgrade08to09(Connection con) { // remove hhdce id in mpan
	 * table // in mpan table add the following boolean fields dceImportKwh, //
	 * dceImportKvarh;, dceExportKwh;, dceExportKvarh; // in mpan table add a
	 * reference to contract try { Statement stmt = con.createStatement(); stmt
	 * .execute("ALTER TABLE main.mpan ADD COLUMN contract_id bigint references
	 * main.contract (id);"); stmt .execute("update main.mpan set contract_id =
	 * (select contract_id from main.hhdce_channels where id =
	 * main.mpan.hhdce_channels_id)");
	 * 
	 * stmt .execute("ALTER TABLE main.mpan ADD COLUMN has_import_kwh
	 * boolean;"); stmt .execute("ALTER TABLE main.mpan ADD COLUMN
	 * has_import_kvarh boolean;"); stmt .execute("ALTER TABLE main.mpan ADD
	 * COLUMN has_export_kwh boolean;"); stmt .execute("ALTER TABLE main.mpan
	 * ADD COLUMN has_export_kvarh boolean;");
	 * 
	 * stmt .execute("update main.mpan set has_import_kwh = (select
	 * is_import_kwh from main.hhdce_channels where id =
	 * main.mpan.hhdce_channels_id)"); stmt .execute("update main.mpan set
	 * has_import_kwh = false where has_import_kwh is null");
	 * 
	 * stmt .execute("update main.mpan set has_import_kvarh = (select
	 * is_import_kvarh from main.hhdce_channels where id =
	 * main.mpan.hhdce_channels_id)"); stmt .execute("update main.mpan set
	 * has_import_kvarh = false where has_import_kvarh is null");
	 * 
	 * stmt .execute("update main.mpan set has_export_kwh = (select
	 * is_export_kwh from main.hhdce_channels where id =
	 * main.mpan.hhdce_channels_id)"); stmt .execute("update main.mpan set
	 * has_export_kwh = false where has_export_kwh is null");
	 * 
	 * stmt .execute("update main.mpan set has_export_kvarh = (select
	 * is_export_kvarh from main.hhdce_channels where id =
	 * main.mpan.hhdce_channels_id)"); stmt .execute("update main.mpan set
	 * has_export_kvarh = false where has_export_kvarh is null");
	 * 
	 * stmt .execute("ALTER TABLE main.mpan drop COLUMN hhdce_channels_id;");
	 * stmt.execute("ALTER TABLE main.mpan drop COLUMN mpan_id;");
	 * stmt.execute("ALTER TABLE main.site add COLUMN name varchar(250);");
	 * stmt.execute("drop table hhdce_channels cascade;");
	 * DatabaseVersion.setDatabaseVersion(9); } catch (SQLException e) { } }
	 */
}
