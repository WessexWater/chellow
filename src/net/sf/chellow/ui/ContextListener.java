package net.sf.chellow.ui;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Properties;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.naming.InitialContext;
import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import javax.sql.DataSource;

import net.sf.chellow.billing.Provider;
import net.sf.chellow.hhimport.stark.StarkAutomaticHhDataImporters;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.MonadFormatter;
import net.sf.chellow.monad.MonadHandler;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.ClockInterval;
import net.sf.chellow.physical.DatabaseVersion;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.MeasurementRequirement;
import net.sf.chellow.physical.MpanTop;
import net.sf.chellow.physical.Mtc;
import net.sf.chellow.physical.MeterType;
import net.sf.chellow.physical.MeterPaymentType;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.Pc;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.Role;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.Ssc;
import net.sf.chellow.physical.Tpr;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.VoltageLevel;

import org.hibernate.tool.hbm2ddl.SchemaUpdate;
import org.python.util.PythonInterpreter;

public class ContextListener implements ServletContextListener {
	static final private String CONFIG_DIR_PARAM_NAME = "chellow.configuration_directory";

	private ServletContext context = null;

	private MonadContextParameters monadParameters;

	private Logger logger = Logger.getLogger("net.sf.chellow");

	@SuppressWarnings("unchecked")
	public void contextInitialized(ServletContextEvent event) {
		context = event.getServletContext();
		Monad.setContext(context);
		try {

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

			// Find database version
			try {
				ResultSet rs;
				ResultSet schemaRs = stmt
						.executeQuery("SELECT nspname FROM pg_namespace where nspname = 'main';");
				if (schemaRs.next()) {
					rs = stmt
							.executeQuery("select version from main.database_version;");
				} else {
					rs = stmt
							.executeQuery("select version from database_version;");
				}
				schemaRs.close();
				if (rs.next()) {
					switch (rs.getInt("version")) {
					case 0:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 1:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 2:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 3:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 4:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 5:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 6:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 7:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 8:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 9:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 10:
						throw new UserException(
								"Database version too old to upgrade with this version.");
					case 11:
						Debug.print("It's version 11");
						upgrade11to12(con);
						break;
					}
				}
			} catch (SQLException sqle) {
				initializeDatabase(con);
				Hiber.close();
			} finally {
				con.close();
			}

			String configDirStr = context
					.getInitParameter(CONFIG_DIR_PARAM_NAME);
			if (configDirStr == null) {
				throw new DeployerException("The init parameter '"
						+ CONFIG_DIR_PARAM_NAME + "'. hasn't been set.");
			}
			ChellowConfiguration.setConfigurationDirectory(context,
					configDirStr);
			StarkAutomaticHhDataImporters.start();
			ChellowProperties chellowProperties = new ChellowProperties(
					new MonadUri("/"), "chellow.properties");
			Properties postProps = new Properties();
			postProps.setProperty("python.path", chellowProperties
					.getProperty("python.path"));
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
					.execute("ALTER TABLE service ALTER COLUMN charge_script TYPE text;");
			stmt
					.execute("ALTER TABLE rate_script ALTER COLUMN script TYPE text;");

			stmt
					.execute("create index date_resolved_idx on snag (date_resolved)");
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
					.execute("CREATE INDEX hh_datum__end_date ON hh_datum (end_date)");
		} catch (SQLException e) {
			throw new InternalException(e);
		}
		DatabaseVersion.setDatabaseVersion(12);
		Hiber.close();
		ReadType.loadFromCsv(context);
		Pc.loadFromCsv(context);
		MarketRole.loadFromCsv(context);
		Participant.loadFromCsv(context);
		Provider.loadFromCsv(context);
		VoltageLevel.insertVoltageLevels();
		Llfc.loadFromCsv(context);
		MeterType.loadFromCsv(context);
		MeterPaymentType.loadFromCsv(context);
		Mtc.loadFromCsv(context);
		Tpr.loadFromCsv(context);
		ClockInterval.loadFromCsv(context);
		Ssc.loadFromCsv(context);
		MeasurementRequirement.loadFromCsv(context);
		MpanTop.loadFromCsv(context);
		Role basicUserRole = Role.insertRole(null, "basic-user");
		Hiber.flush();
		basicUserRole.insertPermission(null, basicUserRole.getUri(), Arrays
				.asList(Invocation.HttpMethod.GET));
		basicUserRole.insertPermission(null, new MonadUri("/"), Arrays
				.asList(Invocation.HttpMethod.GET));
		basicUserRole.insertPermission(null, new MonadUri("/orgs/"),
				new ArrayList<Invocation.HttpMethod>());
		basicUserRole.insertPermission(null, new MonadUri("/users/"),
				new ArrayList<Invocation.HttpMethod>());
		basicUserRole.insertPermission(null,
				new MonadUri("/users/implicit-me/"), Arrays
						.asList(Invocation.HttpMethod.GET));
		basicUserRole.insertPermission(null,
				new MonadUri("/users/explicit-me/"), Arrays
						.asList(Invocation.HttpMethod.GET));
		basicUserRole.insertPermission(null, new MonadUri("/roles/"),
				new ArrayList<Invocation.HttpMethod>());

		EmailAddress adminUserEmailAddress = new EmailAddress(
				"administrator@localhost");
		User adminUser = User.findUserByEmail(adminUserEmailAddress);
		if (adminUser == null) {
			adminUser = User.insertUser(null, adminUserEmailAddress,
					"administrator");

			Role adminRole = Role.insertRole(null, "administrator");
			adminRole.insertPermission(null, new MonadUri("/"), Arrays.asList(
					Invocation.HttpMethod.GET, Invocation.HttpMethod.POST,
					Invocation.HttpMethod.DELETE));
			adminUser.addRole(null, adminRole);
		}
		EmailAddress basicUserEmailAddress = new EmailAddress(
				"basic-user@localhost");
		User basicUser = User.findUserByEmail(basicUserEmailAddress);
		if (basicUser == null) {
			basicUser = User.insertUser(null, basicUserEmailAddress,
					"basic-user");
			Hiber.flush();
			// basicUserRole.insertPermission("/participants/",
			// new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
		}
		Hiber.commit();
		Source.insertSource("net", "Public distribution system.");
		Source.insertSource("chp", "Combined heat and power generator");
		Source.insertSource("lm", "Load management generator");
		Source.insertSource("turb", "Water turbine");
		Source.insertSource("sub", "Sub meter");
		Hiber.commit();
	}

	@SuppressWarnings("unchecked")
	private void upgrade11to12(Connection con) throws HttpException {
		try {
			Statement stmt = con.createStatement();
			stmt
					.execute("COMMENT ON SCHEMA public IS 'Standard public schema'");
			stmt.execute("drop LANGUAGE plpgsql");
			
			
			
			stmt.execute("delete * from account");
			stmt.execute("alter table account drop organization_id");
			stmt.execute("alter table account drop provider_id");
			stmt.execute("alter table account add contract_id bigint not null");
			
			stmt.execute("alter table account_snag rename service_id to contract_id");

			/*
			 * stmt .execute("update meter_timeswitch set description = 'HH Code
			 * 5 and above (with Comms)', is_unmetered = false where code =
			 * '845'"); stmt .execute("update meter_timeswitch set description =
			 * 'HH Code 5 and above (without Comms)', is_unmetered = false where
			 * code = '846'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 A (with Comms)', is_unmetered = false
			 * where code = '847'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 B (with Comms)', is_unmetered = false
			 * where code = '848'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 C (with Comms)', is_unmetered = false
			 * where code = '849'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 D (with Comms)', is_unmetered = false
			 * where code = '850'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 A (without Comms)', is_unmetered = false
			 * where code = '851'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 B (without Comms)', is_unmetered = false
			 * where code = '852'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 C (without Comms)', is_unmetered = false
			 * where code = '853'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 6 D (without Comms)', is_unmetered = false
			 * where code = '854'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 7 (with Comms)', is_unmetered = false
			 * where code = '855'"); stmt .execute("update meter_timeswitch set
			 * description = 'HH Code 7 (without Comms)', is_unmetered = false
			 * where code = '856'");
			 */
			/*
			 * stmt .execute("CREATE TABLE site_supply_generation (id bigint NOT
			 * NULL, supply_generation_id bigint NOT NULL, site_id bigint NOT
			 * NULL, is_physical boolean NOT NULL);"); stmt .execute("CREATE
			 * SEQUENCE site_supply_generation_id_sequence INCREMENT BY 1 NO
			 * MAXVALUE NO MINVALUE CACHE 1;"); stmt .execute("ALTER TABLE ONLY
			 * site_supply_generation ADD CONSTRAINT site_supply_generation_pkey
			 * PRIMARY KEY (id);"); stmt .execute("ALTER TABLE ONLY
			 * site_supply_generation ADD CONSTRAINT
			 * fkey_site_supply_generation_site FOREIGN KEY (site_id) REFERENCES
			 * site(id);"); stmt .execute("ALTER TABLE ONLY
			 * site_supply_generation ADD CONSTRAINT
			 * fkey_site_supply_generation_supply_generation FOREIGN KEY
			 * (supply_generation_id) REFERENCES supply_generation(id);");
			 * ResultSet srs = stmt .executeQuery("select site_supply.site_id as
			 * site_id, supply_generation.id as supply_generation_id,
			 * site_supply.is_physical as is_physical from site_supply,
			 * supply_generation where site_supply.supply_id =
			 * supply_generation.supply_id"); PreparedStatement
			 * siteSupplyGenerationInsert = con .prepareStatement("insert into
			 * site_supply_generation (id, site_id, supply_generation_id,
			 * is_physical) values (?, ?, ?, ?)"); long siteSupplyGenerationId =
			 * 1; while (srs.next()) { long siteId = srs.getLong("site_id");
			 * long supplyGenerationId = srs.getLong("supply_generation_id");
			 * boolean isPhysical = srs.getBoolean("is_physical");
			 * siteSupplyGenerationInsert.setLong(1, siteSupplyGenerationId);
			 * siteSupplyGenerationInsert.setLong(2, siteId);
			 * siteSupplyGenerationInsert.setLong(3, supplyGenerationId);
			 * siteSupplyGenerationInsert.setBoolean(4, isPhysical);
			 * siteSupplyGenerationInsert.execute(); siteSupplyGenerationId++; }
			 * srs.close(); stmt.execute("drop table site_supply");
			 * stmt.execute("drop sequence site_supply_id_sequence"); stmt
			 * .executeQuery("select
			 * setval('site_supply_generation_id_sequence', max(id)) from
			 * site_supply_generation"); stmt.close();
			 */
		} catch (SQLException e) {
			e.printStackTrace();
		}
		Debug.print("Finished upgrading.");
		// dataDelta(con);
	}
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