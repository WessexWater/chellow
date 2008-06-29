package net.sf.chellow.ui;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Properties;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.naming.InitialContext;
import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import javax.sql.DataSource;

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
import net.sf.chellow.physical.DatabaseVersion;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.Password;
import net.sf.chellow.physical.Pc;
import net.sf.chellow.physical.Role;
import net.sf.chellow.physical.Source;
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
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 1:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 2:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 3:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 4:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 5:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 6:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 7:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 8:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 9:
						throw new UserException
								("Database version too old to upgrade with this version.");
					case 10:
						Debug.print("It's version 10");
						upgrade10to11(con);
						break;
					}
				}
			} catch (SQLException sqle) {
				initializeDatabase(con);
				Hiber.close();
			} finally {
				con.close();
			}
			SchemaUpdate su = new SchemaUpdate(Hiber.getConfiguration());
			su.execute(false, true);
			con = ds.getConnection();
			try {
				stmt = con.createStatement();
				try {
					stmt
							.execute("create index date_resolved_idx on snag (date_resolved)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index description_idx on snag (description)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index is_ignored_idx on snag (is_ignored)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index contract_id_idx on snag (contract_id)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index snag_id_idx on snag_channel (snag_id)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index channel_id_idx on snag_channel (channel_id)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index start_date_idx on snag_channel (start_date)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("create index finish_date_idx on snag_channel (finish_date)");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("CREATE INDEX snag_site__finish_date ON snag_site USING btree (finish_date);");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("CREATE INDEX snag_site__site_id ON snag_site USING btree (site_id);");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("CREATE INDEX snag_site__snag_id_idx ON snag_site USING btree (snag_id);");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("CREATE INDEX snag_site__start_date ON snag_site USING btree (start_date);");
				} catch (SQLException e) {
				}
				try {
					stmt
							.execute("CREATE INDEX hh_datum__end_date ON hh_datum USING btree (end_date)");
				} catch (SQLException e) {
				}
			} finally {
				con.close();
			}

			/*
			 * List exceptions = su.getExceptions(); if (exceptions.size() > 0) {
			 * throw (Exception) exceptions.get(0); }
			 */

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
			// postProps.setProperty("python.path", "C:\\Program
			// Files\\Apache
			// Software Foundation\\Tomcat
			// 5.5\\webapps\\chellow\\WEB-INF\\classes;C:\\Program
			// Files\\Apache
			// Software Foundation\\Tomcat
			// 5.5\\webapps\\chellow\\WEB-INF\\lib\\hibernate3.jar");
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
		} catch (SQLException e) {
		}
		DatabaseVersion.setDatabaseVersion(11);
		Hiber.close();
		Participant.loadFromCsv();
		Hiber.close();
		MarketRole.loadFromCsv();
		Hiber.close();
		EmailAddress adminUserEmailAddress = new EmailAddress(
				"administrator@localhost");
		User adminUser = User.findUserByEmail(adminUserEmailAddress);
		if (adminUser == null) {
			adminUser = User.insertUser(adminUserEmailAddress,
					new Password("administrator"));

			Role adminRole = Role.insertRole("administrator");
			adminRole.insertPermission("/", new Invocation.HttpMethod[] {
					Invocation.HttpMethod.GET, Invocation.HttpMethod.POST,
					Invocation.HttpMethod.DELETE });
			adminUser.insertRole(adminUser, adminRole);
		}
		EmailAddress basicUserEmailAddress = new EmailAddress(
				"basic-user@localhost");
		User basicUser = User.findUserByEmail(basicUserEmailAddress);
		if (basicUser == null) {
			basicUser = User.insertUser(basicUserEmailAddress,
					new Password("basic-user"));
			Hiber.flush();
			Role basicUserRole = Role.insertRole("basic-user");
			Hiber.flush();
			basicUserRole
					.insertPermission(
							basicUserRole.getUri(),
							new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
			basicUserRole
					.insertPermission(
							"/",
							new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
			basicUserRole.insertPermission("/orgs/",
					new Invocation.HttpMethod[] {});
			basicUserRole.insertPermission("/users/",
					new Invocation.HttpMethod[] {});
			basicUserRole
					.insertPermission(
							"/users/implicit-me/",
							new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
			basicUserRole
					.insertPermission(
							"/users/explicit-me/",
							new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
			basicUserRole
					.insertPermission(
							basicUser.getUri(),
							new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
			basicUserRole.insertPermission("/roles/",
					new Invocation.HttpMethod[] {});
			//basicUserRole.insertPermission("/participants/",
			//		new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
			basicUser.insertRole(adminUser, basicUserRole);
			Hiber.commit();
		}
	}

	@SuppressWarnings("unchecked")
	private void initializeDatabaseOld(Connection con) throws InternalException {
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
		} catch (SQLException e) {
		}
		DatabaseVersion.setDatabaseVersion(11);
		Hiber.close();
		try {
			//Government.insertGovernment();
			/*
			insertDso("Eastern", "10");
			insertDso("Scottish Hydro", "17");
			insertDso("East Midlands", "11");
			insertDso("Scottish Power", "18");
			insertDso("London", "12");
			insertDso("Seeboard", "19");
			insertDso("Manweb", "13");
			insertDso("Southern", "20");
			insertDso("Midlands", "14");
			insertDso("Swalec", "21");
			insertDso("Northern", "15");
			insertDso("Sweb", "22");
			insertDso("Norweb", "16");
			insertDso("Yorkshire", "23");
			insertDso("Non-settlement 98", "98");
			insertDso("Non-settlement 99", "99");
			*/
			Source.insertSource("net", "Public distribution system.");
			Source.insertSource("chp", "Combined heat and power generator");
			Source.insertSource("lm", "Load management generator");
			Source.insertSource("turb", "Water turbine");
			Source.insertSource("sub", "Sub meter");

			VoltageLevel.insertVoltageLevels();

			Pc.insertProfileClass(0, "Half-hourly");
			Pc.insertProfileClass(1, "Domestic Unrestricted");
			Pc.insertProfileClass(2, "Domestic Economy 7");
			Pc.insertProfileClass(3, "Non-Domestic Unrestricted");
			Pc.insertProfileClass(4, "Non-Domestic Economy 7");
			Pc
					.insertProfileClass(
							5,
							"Non-domestic, with MD recording capability and with LF less than or equal to 20%");
			Pc
					.insertProfileClass(
							6,
							"Non-domestic, with MD recording capability and with LF less than or equal to 30% and greater than 20%");
			Pc
					.insertProfileClass(
							7,
							"Non-domestic, with MD recording capability and with LF less than or equal to 40% and greater than 30%");
			Pc
					.insertProfileClass(8,
							"Non-domestic, with MD recording capability and with LF greater than 40%");

			Hiber.commit();
			EmailAddress adminUserEmailAddress = new EmailAddress(
					"administrator@localhost");
			User adminUser = User.findUserByEmail(adminUserEmailAddress);
			if (adminUser == null) {
				adminUser = User.insertUser(adminUserEmailAddress,
						new Password("administrator"));

				Role adminRole = Role.insertRole("administrator");
				adminRole.insertPermission("/", new Invocation.HttpMethod[] {
						Invocation.HttpMethod.GET, Invocation.HttpMethod.POST,
						Invocation.HttpMethod.DELETE });
				adminUser.insertRole(adminUser, adminRole);
			}
			EmailAddress basicUserEmailAddress = new EmailAddress(
					"basic-user@localhost");
			User basicUser = User.findUserByEmail(basicUserEmailAddress);
			if (basicUser == null) {
				basicUser = User.insertUser(basicUserEmailAddress,
						new Password("basic-user"));
				Hiber.flush();
				Role basicUserRole = Role.insertRole("basic-user");
				Hiber.flush();
				basicUserRole
						.insertPermission(
								basicUserRole.getUri(),
								new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
				basicUserRole
						.insertPermission(
								"/",
								new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
				basicUserRole.insertPermission("/orgs/",
						new Invocation.HttpMethod[] {});
				basicUserRole.insertPermission("/users/",
						new Invocation.HttpMethod[] {});
				basicUserRole
						.insertPermission(
								"/users/implicit-me/",
								new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
				basicUserRole
						.insertPermission(
								"/users/explicit-me/",
								new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
				basicUserRole
						.insertPermission(
								basicUser.getUri(),
								new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
				basicUserRole.insertPermission("/roles/",
						new Invocation.HttpMethod[] {});
				basicUser.insertRole(adminUser, basicUserRole);
				dataDelta(con);
			}
		} catch (Exception e) {
			Hiber.rollBack();
			throw new InternalException(e);
		} finally {
			Hiber.close();
		}
	}

	private void dataDelta(Connection con) throws HttpException {
		/*
		 * try { Statement stmt = con.createStatement(); stmt .execute("CREATE
		 * UNIQUE INDEX llf_mt_idx on llf_mt (line_loss_factor_id,
		 * meter_timeswitch_id)"); } catch (SQLException e) { }
		 */

		// Ssc.insertSsc(code, tprs)
		
		/*
		Tpr tpr1 = Tpr.insertTpr(1);
		tpr1.insertLine(1, 12, 1, 7, 0, 30, 0, 0, true);
		Tpr tpr39 = Tpr.insertTpr(39);
		tpr39.insertLine(1, 12, 1, 7, 7, 0, 23, 30, false);
		Tpr tpr40 = Tpr.insertTpr(40);
		tpr40.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr43 = Tpr.insertTpr(43);
		tpr43.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr44 = Tpr.insertTpr(44);
		tpr44.insertLine(1, 12, 1, 7, 8, 0, 0, 30, false);
		Tpr tpr55 = Tpr.insertTpr(55);
		tpr55.insertLine(1, 12, 1, 7, 7, 30, 23, 0, true);
		Tpr tpr72 = Tpr.insertTpr(72);
		tpr72.insertLine(1, 12, 7, 1, 0, 30, 0, 0, true);
		tpr72.insertLine(1, 12, 2, 6, 20, 0, 7, 30, true);
		Tpr tpr184 = Tpr.insertTpr(184);
		tpr184.insertLine(1, 12, 2, 6, 8, 0, 19, 30, true);
		Tpr tpr187 = Tpr.insertTpr(187);
		tpr187.insertLine(1, 12, 7, 1, 8, 0, 0, 30, true);
		tpr187.insertLine(1, 12, 1, 6, 20, 0, 0, 30, true);
		Tpr tpr194 = Tpr.insertTpr(194);
		tpr194.insertLine(1, 12, 1, 7, 23, 30, 7, 0, true);
		Tpr tpr206 = Tpr.insertTpr(206);
		tpr206.insertLine(1, 12, 1, 7, 0, 30, 8, 0, false);
		Tpr tpr208 = Tpr.insertTpr(208);
		tpr208.insertLine(1, 12, 1, 7, 1, 0, 7, 0, true);
		Tpr tpr210 = Tpr.insertTpr(210);
		tpr210.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr221 = Tpr.insertTpr(221);
		tpr221.insertLine(1, 12, 1, 7, 0, 0, 6, 30, false);
		Tpr tpr258 = Tpr.insertTpr(258);
		tpr258.insertLine(1, 12, 1, 7, 0, 30, 12, 0, true);
		Tpr tpr259 = Tpr.insertTpr(259);
		tpr259.insertLine(1, 12, 1, 7, 12, 30, 0, 0, true);
		Tpr tpr260 = Tpr.insertTpr(260);
		tpr260.insertLine(1, 12, 1, 7, 18, 30, 6, 0, true);
		Tpr tpr261 = Tpr.insertTpr(261);
		tpr261.insertLine(1, 12, 1, 7, 6, 30, 18, 0, true);
		Tpr tpr262 = Tpr.insertTpr(262);
		tpr262.insertLine(1, 12, 1, 7, 6, 30, 18, 30, true);
		Tpr tpr263 = Tpr.insertTpr(263);
		tpr263.insertLine(1, 12, 1, 7, 19, 00, 6, 0, true);
		Tpr tpr264 = Tpr.insertTpr(264);
		tpr264.insertLine(1, 12, 1, 7, 3, 30, 6, 0, true);
		Tpr tpr265 = Tpr.insertTpr(265);
		tpr265.insertLine(1, 12, 1, 7, 6, 30, 3, 30, true);
		Tpr tpr1000 = Tpr.insertTpr(1000);
		tpr1000.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1001 = Tpr.insertTpr(1001);
		tpr1001.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1002 = Tpr.insertTpr(1002);
		tpr1002.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1003 = Tpr.insertTpr(1003);
		tpr1003.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1008 = Tpr.insertTpr(1008);
		tpr1008.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1009 = Tpr.insertTpr(1009);
		tpr1009.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1012 = Tpr.insertTpr(1012);
		tpr1012.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1013 = Tpr.insertTpr(1013);
		tpr1013.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1014 = Tpr.insertTpr(1014);
		tpr1014.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1015 = Tpr.insertTpr(1015);
		tpr1015.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1018 = Tpr.insertTpr(1018);
		tpr1018.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1019 = Tpr.insertTpr(1019);
		tpr1019.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1020 = Tpr.insertTpr(1020);
		tpr1020.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1021 = Tpr.insertTpr(1021);
		tpr1021.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1034 = Tpr.insertTpr(1034);
		tpr1034.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1035 = Tpr.insertTpr(1035);
		tpr1035.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1037 = Tpr.insertTpr(1037);
		tpr1037.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1038 = Tpr.insertTpr(1038);
		tpr1038.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1039 = Tpr.insertTpr(1039);
		tpr1039.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1040 = Tpr.insertTpr(1040);
		tpr1040.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1048 = Tpr.insertTpr(1048);
		tpr1048.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1049 = Tpr.insertTpr(1049);
		tpr1049.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1055 = Tpr.insertTpr(1055);
		tpr1055.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1056 = Tpr.insertTpr(1056);
		tpr1056.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1057 = Tpr.insertTpr(1057);
		tpr1057.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1058 = Tpr.insertTpr(1058);
		tpr1058.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1059 = Tpr.insertTpr(1059);
		tpr1059.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1060 = Tpr.insertTpr(1060);
		tpr1060.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1061 = Tpr.insertTpr(1061);
		tpr1061.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1062 = Tpr.insertTpr(1062);
		tpr1062.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1063 = Tpr.insertTpr(1063);
		tpr1063.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1064 = Tpr.insertTpr(1064);
		tpr1064.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1065 = Tpr.insertTpr(1065);
		tpr1065.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1066 = Tpr.insertTpr(1066);
		tpr1066.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1067 = Tpr.insertTpr(1067);
		tpr1067.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1068 = Tpr.insertTpr(1068);
		tpr1068.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1071 = Tpr.insertTpr(1071);
		tpr1071.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1072 = Tpr.insertTpr(1072);
		tpr1072.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1078 = Tpr.insertTpr(1078);
		tpr1078.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1079 = Tpr.insertTpr(1079);
		tpr1079.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1153 = Tpr.insertTpr(1153);
		tpr1153.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1154 = Tpr.insertTpr(1154);
		tpr1154.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1191 = Tpr.insertTpr(1191);
		tpr1191.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1192 = Tpr.insertTpr(1192);
		tpr1192.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1233 = Tpr.insertTpr(1233);
		tpr1233.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1234 = Tpr.insertTpr(1234);
		tpr1234.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1238 = Tpr.insertTpr(1238);
		tpr1238.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1239 = Tpr.insertTpr(1239);
		tpr1239.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1240 = Tpr.insertTpr(1240);
		tpr1240.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1241 = Tpr.insertTpr(1241);
		tpr1241.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1242 = Tpr.insertTpr(1242);
		tpr1242.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1243 = Tpr.insertTpr(1243);
		tpr1243.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1244 = Tpr.insertTpr(1244);
		tpr1244.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1245 = Tpr.insertTpr(1245);
		tpr1245.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1246 = Tpr.insertTpr(1246);
		tpr1246.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1247 = Tpr.insertTpr(1247);
		tpr1247.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1248 = Tpr.insertTpr(1248);
		tpr1248.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1249 = Tpr.insertTpr(1249);
		tpr1249.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1250 = Tpr.insertTpr(1250);
		tpr1250.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1251 = Tpr.insertTpr(1251);
		tpr1251.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1252 = Tpr.insertTpr(1252);
		tpr1252.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1253 = Tpr.insertTpr(1253);
		tpr1253.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1254 = Tpr.insertTpr(1254);
		tpr1254.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1255 = Tpr.insertTpr(1255);
		tpr1255.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1256 = Tpr.insertTpr(1256);
		tpr1256.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1257 = Tpr.insertTpr(1257);
		tpr1257.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1258 = Tpr.insertTpr(1258);
		tpr1258.insertLine(1, 12, 1, 7, 8, 30, 1, 0, false);
		Tpr tpr1259 = Tpr.insertTpr(1259);
		tpr1259.insertLine(1, 12, 1, 7, 1, 30, 8, 0, false);
		Tpr tpr1265 = Tpr.insertTpr(1265);
		tpr1265.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1266 = Tpr.insertTpr(1266);
		tpr1266.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1267 = Tpr.insertTpr(1267);
		tpr1267.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1268 = Tpr.insertTpr(1268);
		tpr1268.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1269 = Tpr.insertTpr(1269);
		tpr1269.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1270 = Tpr.insertTpr(1270);
		tpr1270.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1271 = Tpr.insertTpr(1271);
		tpr1271.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1272 = Tpr.insertTpr(1272);
		tpr1272.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1273 = Tpr.insertTpr(1273);
		tpr1273.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1274 = Tpr.insertTpr(1274);
		tpr1274.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1275 = Tpr.insertTpr(1275);
		tpr1275.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1276 = Tpr.insertTpr(1276);
		tpr1276.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1277 = Tpr.insertTpr(1277);
		tpr1277.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1278 = Tpr.insertTpr(1278);
		tpr1278.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1279 = Tpr.insertTpr(1279);
		tpr1279.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1280 = Tpr.insertTpr(1280);
		tpr1280.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1288 = Tpr.insertTpr(1288);
		tpr1288.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1289 = Tpr.insertTpr(1289);
		tpr1289.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1295 = Tpr.insertTpr(1295);
		tpr1295.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1296 = Tpr.insertTpr(1296);
		tpr1296.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1297 = Tpr.insertTpr(1297);
		tpr1297.insertLine(1, 12, 1, 7, 0, 0, 6, 30, true);
		Tpr tpr1298 = Tpr.insertTpr(1298);
		tpr1298.insertLine(1, 12, 1, 7, 7, 0, 0, 0, true);
		Tpr tpr1299 = Tpr.insertTpr(1299);
		tpr1299.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1300 = Tpr.insertTpr(1300);
		tpr1300.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1324 = Tpr.insertTpr(1324);
		tpr1324.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1325 = Tpr.insertTpr(1325);
		tpr1325.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1326 = Tpr.insertTpr(1326);
		tpr1326.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1327 = Tpr.insertTpr(1327);
		tpr1327.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1328 = Tpr.insertTpr(1328);
		tpr1328.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1329 = Tpr.insertTpr(1329);
		tpr1329.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1330 = Tpr.insertTpr(1330);
		tpr1330.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1331 = Tpr.insertTpr(1331);
		tpr1331.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1332 = Tpr.insertTpr(1332);
		tpr1332.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1333 = Tpr.insertTpr(1333);
		tpr1333.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1334 = Tpr.insertTpr(1334);
		tpr1334.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1335 = Tpr.insertTpr(1335);
		tpr1335.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1336 = Tpr.insertTpr(1336);
		tpr1336.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1337 = Tpr.insertTpr(1337);
		tpr1337.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1338 = Tpr.insertTpr(1338);
		tpr1338.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1339 = Tpr.insertTpr(1339);
		tpr1339.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1340 = Tpr.insertTpr(1340);
		tpr1340.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1341 = Tpr.insertTpr(1341);
		tpr1341.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1342 = Tpr.insertTpr(1342);
		tpr1342.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1343 = Tpr.insertTpr(1343);
		tpr1343.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1344 = Tpr.insertTpr(1344);
		tpr1344.insertLine(1, 12, 1, 7, 1, 0, 7, 30, true);
		Tpr tpr1345 = Tpr.insertTpr(1345);
		tpr1345.insertLine(1, 12, 1, 7, 8, 0, 0, 30, true);
		Tpr tpr1351 = Tpr.insertTpr(1351);
		tpr1351.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1352 = Tpr.insertTpr(1352);
		tpr1352.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1353 = Tpr.insertTpr(1353);
		tpr1353.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1354 = Tpr.insertTpr(1354);
		tpr1354.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1355 = Tpr.insertTpr(1355);
		tpr1355.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1356 = Tpr.insertTpr(1356);
		tpr1356.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1357 = Tpr.insertTpr(1357);
		tpr1357.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1358 = Tpr.insertTpr(1358);
		tpr1358.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1359 = Tpr.insertTpr(1359);
		tpr1359.insertLine(1, 12, 1, 7, 0, 30, 7, 0, true);
		Tpr tpr1360 = Tpr.insertTpr(1360);
		tpr1360.insertLine(1, 12, 1, 7, 6, 30, 0, 0, true);
		Tpr tpr1371 = Tpr.insertTpr(1371);
		tpr1371.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1371.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1372 = Tpr.insertTpr(1372);
		tpr1372.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1372.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1373 = Tpr.insertTpr(1373);
		tpr1373.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1373.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1374 = Tpr.insertTpr(1374);
		tpr1374.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1374.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1375 = Tpr.insertTpr(1375);
		tpr1375.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1375.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1376 = Tpr.insertTpr(1376);
		tpr1376.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1376.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1377 = Tpr.insertTpr(1377);
		tpr1377.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1377.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1378 = Tpr.insertTpr(1378);
		tpr1378.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1378.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1379 = Tpr.insertTpr(1379);
		tpr1379.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1379.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1380 = Tpr.insertTpr(1380);
		tpr1380.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1380.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1381 = Tpr.insertTpr(1381);
		tpr1381.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1381.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1382 = Tpr.insertTpr(1382);
		tpr1382.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1382.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1383 = Tpr.insertTpr(1383);
		tpr1383.insertLine(1, 12, 1, 7, 23, 0, 0, 30, false);
		tpr1383.insertLine(1, 12, 1, 7, 3, 0, 7, 30, false);
		Tpr tpr1384 = Tpr.insertTpr(1384);
		tpr1384.insertLine(1, 12, 1, 7, 1, 0, 2, 30, false);
		tpr1384.insertLine(1, 12, 1, 7, 8, 0, 22, 30, false);
		Tpr tpr1385 = Tpr.insertTpr(1385);
		tpr1385.insertLine(1, 12, 1, 7, 1, 0, 7, 30, false);
		Tpr tpr1386 = Tpr.insertTpr(1386);
		tpr1386.insertLine(1, 12, 1, 7, 8, 0, 7, 30, false);
		
		*/
		Hiber.commit();

		/*
		Ssc.insertSsc(0, null);
		Ssc.insertSsc(6, null);
		Ssc.insertSsc(7, null);
		Ssc.insertSsc(8, null);
		Ssc.insertSsc(9, null);
		Ssc.insertSsc(10, null);
		Ssc.insertSsc(11, null);
		Ssc.insertSsc(12, null);
		Ssc.insertSsc(13, null);
		Ssc.insertSsc(15, null);
		Ssc.insertSsc(16, null);
		Ssc.insertSsc(17, null);
		Ssc.insertSsc(18, null);
		Ssc.insertSsc(19, null);
		Ssc.insertSsc(20, null);
		Ssc.insertSsc(21, null);
		Ssc.insertSsc(22, null);
		Ssc.insertSsc(23, null);
		Ssc.insertSsc(24, null);
		Ssc.insertSsc(25, null);
		Ssc.insertSsc(33, null);
		Ssc.insertSsc(34, null);
		Ssc.insertSsc(35, null);
		Ssc.insertSsc(36, null);
		Ssc.insertSsc(37, null);
		Ssc.insertSsc(40, null);
		Ssc.insertSsc(41, null);
		Ssc.insertSsc(42, null);
		Ssc.insertSsc(43, null);
		Ssc.insertSsc(44, null);
		Ssc.insertSsc(62, null);
		Ssc.insertSsc(64, null);
		Ssc.insertSsc(65, null);
		Ssc.insertSsc(66, null);
		Ssc.insertSsc(67, null);
		Ssc.insertSsc(73, null);
		Ssc.insertSsc(82, null);
		Ssc.insertSsc(83, null);
		Ssc.insertSsc(85, null);
		Ssc.insertSsc(86, null);
		Ssc.insertSsc(87, null);
		Ssc.insertSsc(88, null);
		Ssc.insertSsc(91, null);
		Ssc.insertSsc(95, null);
		Ssc.insertSsc(96, null);
		Ssc.insertSsc(100, null);
		Ssc.insertSsc(104, null);
		Ssc.insertSsc(106, null);
		Ssc.insertSsc(107, null);
		Ssc.insertSsc(108, null);
		Ssc.insertSsc(127, null);
		Ssc.insertSsc(128, null);
		Ssc.insertSsc(132, null);
		Ssc.insertSsc(135, null);
		Ssc.insertSsc(145, null);
		Ssc.insertSsc(146, null);
		Ssc.insertSsc(148, null);
		Ssc.insertSsc(151, null);
		Ssc.insertSsc(154, null);
		Ssc.insertSsc(167, null);
		Ssc.insertSsc(168, null);
		Ssc.insertSsc(169, null);
		Ssc.insertSsc(170, null);
		Ssc.insertSsc(171, null);
		Ssc.insertSsc(172, null);
		Ssc.insertSsc(173, null);
		Ssc.insertSsc(174, null);
		Ssc.insertSsc(175, null);
		Ssc.insertSsc(176, null);
		Ssc.insertSsc(177, null);
		Ssc.insertSsc(178, null);
		Ssc.insertSsc(179, null);
		Ssc.insertSsc(180, null);
		Ssc.insertSsc(181, null);
		Ssc.insertSsc(182, null);
		Ssc.insertSsc(183, null);
		Ssc.insertSsc(184, null);
		Ssc.insertSsc(185, null);
		Ssc.insertSsc(186, null);
		Ssc.insertSsc(201, null);
		Ssc.insertSsc(202, null);
		Ssc.insertSsc(203, null);
		Ssc.insertSsc(204, null);
		Ssc.insertSsc(205, null);
		Ssc.insertSsc(206, null);
		Ssc.insertSsc(207, null);
		Ssc.insertSsc(208, null);
		Ssc.insertSsc(242, null);
		Ssc.insertSsc(243, null);
		Ssc.insertSsc(244, null);
		Ssc.insertSsc(246, null);
		Ssc.insertSsc(251, null);
		Ssc.insertSsc(252, null);
		Ssc.insertSsc(260, null);
		Ssc.insertSsc(261, null);
		Ssc.insertSsc(264, null);
		Ssc.insertSsc(265, null);
		Ssc.insertSsc(266, null);
		Ssc.insertSsc(268, null);
		Ssc.insertSsc(270, null);
		Ssc.insertSsc(271, null);
		Ssc.insertSsc(272, null);
		Ssc.insertSsc(273, null);
		Ssc.insertSsc(274, null);
		Ssc.insertSsc(299, null);
		Ssc.insertSsc(300, null);
		Ssc.insertSsc(301, null);
		Ssc.insertSsc(302, null);
		Ssc.insertSsc(303, null);
		Ssc.insertSsc(304, null);
		Ssc.insertSsc(309, null);
		Ssc.insertSsc(312, null);
		Ssc.insertSsc(314, null);
		Ssc.insertSsc(315, null);
		Ssc.insertSsc(317, null);
		Ssc.insertSsc(319, null);
		Ssc.insertSsc(320, null);
		Ssc.insertSsc(322, null);
		Ssc.insertSsc(326, null);
		Ssc.insertSsc(330, null);
		Ssc.insertSsc(334, null);
		Ssc.insertSsc(342, null);
		Ssc.insertSsc(343, null);
		Ssc.insertSsc(344, null);
		Ssc.insertSsc(345, null);
		Ssc.insertSsc(346, null);
		Ssc.insertSsc(349, null);
		Ssc.insertSsc(351, null);
		Ssc.insertSsc(352, null);
		Ssc.insertSsc(353, null);
		Ssc.insertSsc(393, null);
		Ssc.insertSsc(425, null);
		Ssc.insertSsc(427, null);
		Ssc.insertSsc(428, null);
		Ssc.insertSsc(429, null);
		Ssc.insertSsc(430, null);
		Ssc.insertSsc(431, null);
		Ssc.insertSsc(432, null);
		Ssc.insertSsc(435, null);
		Ssc.insertSsc(436, null);
		Ssc.insertSsc(440, null);
		Ssc.insertSsc(443, null);
		Ssc.insertSsc(447, null);
		Ssc.insertSsc(448, null);
		Ssc.insertSsc(449, null);
		Ssc.insertSsc(450, null);
		Ssc.insertSsc(451, null);
		Ssc.insertSsc(452, null);
		Ssc.insertSsc(453, null);
		Ssc.insertSsc(454, null);
		Ssc.insertSsc(455, null);
		Ssc.insertSsc(456, null);
		Ssc.insertSsc(459, null);
		Ssc.insertSsc(482, null);
		Ssc.insertSsc(483, null);
		Ssc.insertSsc(484, null);
		Ssc.insertSsc(485, null);
		Ssc.insertSsc(486, null);
		Ssc.insertSsc(487, null);
		Ssc.insertSsc(488, null);
		Ssc.insertSsc(489, null);
		Ssc.insertSsc(490, null);
		Ssc.insertSsc(491, null);
		Ssc.insertSsc(492, null);
		Ssc.insertSsc(493, null);
		Ssc.insertSsc(494, null);
		Ssc.insertSsc(495, null);
		Ssc.insertSsc(496, null);
		Ssc.insertSsc(497, null);
		Ssc.insertSsc(498, null);
		Ssc.insertSsc(935, null);
		Ssc.insertSsc(936, null);
		Ssc.insertSsc(940, null);
		Ssc.insertSsc(941, null);
		Ssc.insertSsc(9999, null);

		MeterTimeswitch.insertMeterTimeswitch(null, "500",
				"Credit single rate", false);
		// mtc_null_500.insertRegister(Ssc.Units.KWH, "1");
		Hiber.commit();
		MeterTimeswitch.insertMeterTimeswitch(null, "501",
				"Credit single rate", false);
		// mtc_null_501.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "502", "Continuous", true);
		// mtc_null_502.insertRegister(Ssc.Units.KWH, "258");
		// mtc_null_502.insertRegister(Ssc.Units.KWH, "259");
		MeterTimeswitch
				.insertMeterTimeswitch(null, "503", "Dawn to Dusk", true);
		// mtc_null_503.insertRegister(Ssc.Units.KWH, "262");
		// mtc_null_503.insertRegister(Ssc.Units.KWH, "263");
		MeterTimeswitch
				.insertMeterTimeswitch(null, "504", "Dusk to Dawn", true);
		// mtc_null_504.insertRegister(Ssc.Units.KWH, "260");
		// mtc_null_504.insertRegister(Ssc.Units.KWH, "261");
		MeterTimeswitch.insertMeterTimeswitch(null, "505",
				"Half Night / Pre Dawn", true);
		// mtc_null_505.insertRegister(Ssc.Units.KWH, "264");
		// mtc_null_505.insertRegister(Ssc.Units.KWH, "265");
		MeterTimeswitch.insertMeterTimeswitch(null, "800", "Temp No Meter",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "801",
				"Credit single rate", false);
		// mtc_null_801.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "802",
				"Credit single rate", false);
		// mtc_null_802.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "803", "7 hr E7", false);
		// mtc_null_803.insertRegister(Ssc.Units.KWH, "39");
		// mtc_null_803.insertRegister(Ssc.Units.KWH, "221");
		MeterTimeswitch.insertMeterTimeswitch(null, "804", "7 hr E7", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "845",
				"HH Code 5 and above (with Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "846",
				"HH Code 5 and above (without Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "847",
				"HH Code 6 A (with Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "848",
				"HH Code 6 B (with Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "849",
				"HH Code 6 C (with Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "850",
				"HH Code 6 D (with Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "851",
				"HH Code 6 A (without Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "852",
				"HH Code 6 B (without Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "853",
				"HH Code 6 C (without Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "854",
				"HH Code 6 D (without Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "855",
				"HH Code 7 (with Comms)", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "856",
				"HH Code 7 (without Comms)", false);
		MeterTimeswitch
				.insertMeterTimeswitch(null, "863", "Pseudo Meter", true);
		MeterTimeswitch.insertMeterTimeswitch(null, "864", "", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "865", "", false);
		// mtc_null_804.insertRegister(Ssc.Units.KWH, "39");
		// mtc_null_804.insertRegister(Ssc.Units.KWH, "221");
		MeterTimeswitch.insertMeterTimeswitch(null, "805", "7 hr E7", false);
		// mtc_null_805.insertRegister(Ssc.Units.KWH,
		// "1008, 1048, 1060, 1062, 1064, 1066, 1068, 1297");
		// mtc_null_805.insertRegister(Ssc.Units.KWH,
		// "1009, 1049, 1059, 1061, 1063, 1065, 1067, 1298");
		MeterTimeswitch.insertMeterTimeswitch(null, "806", "7 hr E7", false);
		// mtc_null_806.insertRegister(Ssc.Units.KWH,
		// "1008, 1048, 1060, 1062, 1064, 1066, 1068, 1297");
		// mtc_null_806.insertRegister(Ssc.Units.KWH,
		// "1009, 1049, 1059, 1061, 1063, 1065, 1067, 1298");
		MeterTimeswitch.insertMeterTimeswitch(null, "807", "7 hr E7", false);
		// mtc_null_807.insertRegister(Ssc.Units.KWH, "40");
		// mtc_null_807.insertRegister(Ssc.Units.KWH, "206");
		MeterTimeswitch.insertMeterTimeswitch(null, "808", "7 hr E7", false);
		// mtc_null_808.insertRegister(Ssc.Units.KWH, "40");
		// mtc_null_808.insertRegister(Ssc.Units.KWH, "206");
		MeterTimeswitch.insertMeterTimeswitch(null, "809", "7 hr E7", false);
		// mtc_null_809
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1078, 1154, 1192, 1273, 1275, 1277, 1279, 1296, 1013, 1352, 1354,
		// 1356, 1358, 1360");
		// mtc_null_809
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1079, 1153, 1191, 1274, 1276, 1278, 1280, 1295, 1012, 1351, 1353,
		// 1355, 1357, 1359");
		MeterTimeswitch.insertMeterTimeswitch(null, "810", "7 hr E7", false);
		// mtc_null_810
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1078, 1154, 1192, 1273, 1275, 1277, 1279, 1296, 1013, 1352, 1354,
		// 1356, 1358, 1360");
		// mtc_null_810
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1079, 1153, 1191, 1274, 1276, 1278, 1280, 1295, 1012, 1351, 1353,
		// 1355, 1357, 1359");
		MeterTimeswitch.insertMeterTimeswitch(null, "811", "7 hr E7", false);
		// mtc_null_811.insertRegister(Ssc.Units.KWH, "43");
		// mtc_null_811.insertRegister(Ssc.Units.KWH, "210");
		MeterTimeswitch.insertMeterTimeswitch(null, "812", "7 hr E7", false);
		// mtc_null_812.insertRegister(Ssc.Units.KWH, "43");
		// mtc_null_812.insertRegister(Ssc.Units.KWH, "210");
		MeterTimeswitch.insertMeterTimeswitch(null, "813", "7 hr E7", false);
		// mtc_null_813.insertRegister(Ssc.Units.KWH, "1385");
		// mtc_null_813.insertRegister(Ssc.Units.KWH, "1386");
		MeterTimeswitch.insertMeterTimeswitch(null, "814", "7 hr E7", false);
		// mtc_null_814
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1000, 1002, 1014, 1018, 1020, 1034, 1037, 1039, 1056, 1058, 1072,
		// 1239, 1266, 1268, 1270, 1272, 1288, 1299, 1324, 1326, 1328, 1330,
		// 1332, 1334, 1336, 1338, 1340, 1342, 1344");
		// mtc_null_814
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1001, 1003, 1015, 1019, 1021, 1035, 1038, 1040, 1055, 1057, 1071,
		// 1238, 1265, 1267, 1269, 1271, 1289, 1300, 1325, 1327, 1329, 1331,
		// 1333, 1335, 1337, 1339, 1341, 1343, 1345");
		MeterTimeswitch.insertMeterTimeswitch(null, "815", "7 hr E7", false);
		// mtc_null_815
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1000, 1002, 1014, 1018, 1020, 1034, 1037, 1039, 1056, 1058, 1072,
		// 1239, 1266, 1268, 1270, 1272, 1288, 1299, 1324, 1326, 1328, 1330,
		// 1332, 1334, 1336, 1338, 1340, 1342, 1344");
		// mtc_null_815
		// .insertRegister(
		// Ssc.Units.KWH,
		// "1001, 1003, 1015, 1019, 1021, 1035, 1038, 1040, 1055, 1057, 1071,
		// 1238, 1265, 1267, 1269, 1271, 1289, 1300, 1325, 1327, 1329, 1331,
		// 1333, 1335, 1337, 1339, 1341, 1343, 1345");
		MeterTimeswitch.insertMeterTimeswitch(null, "816", "7 hr E7", false);
		// mtc_null_816.insertRegister(Ssc.Units.KWH, "44");
		// mtc_null_816.insertRegister(Ssc.Units.KWH, "208");
		MeterTimeswitch.insertMeterTimeswitch(null, "817", "7 hr E7", false);
		// mtc_null_817.insertRegister(Ssc.Units.KWH, "44");
		// mtc_null_817.insertRegister(Ssc.Units.KWH, "208");
		MeterTimeswitch.insertMeterTimeswitch(null, "818", "7 hr OP (1-rate)",
				false);
		// mtc_null_818.insertRegister(Ssc.Units.KWH, "210");
		MeterTimeswitch.insertMeterTimeswitch(null, "819", "7 hr OP (1-rate)",
				false);
		// mtc_null_819.insertRegister(Ssc.Units.KWH, "210");
		MeterTimeswitch.insertMeterTimeswitch(null, "820", "8 hr night", false);
		// mtc_null_820.insertRegister(Ssc.Units.KWH, "55");
		// mtc_null_820.insertRegister(Ssc.Units.KWH, "194");
		MeterTimeswitch.insertMeterTimeswitch(null, "821", "8 hr night", false);
		// mtc_null_821.insertRegister(Ssc.Units.KWH, "55");
		// mtc_null_821.insertRegister(Ssc.Units.KWH, "194");
		MeterTimeswitch.insertMeterTimeswitch(null, "822", "8 hr OP (1-rate)",
				false);
		// mtc_null_822.insertRegister(Ssc.Units.KWH, "194");
		MeterTimeswitch.insertMeterTimeswitch(null, "823", "8 hr OP (1-rate)",
				false);
		// mtc_null_823.insertRegister(Ssc.Units.KWH, "194");
		MeterTimeswitch.insertMeterTimeswitch(null, "824", "8 hr OP (1-rate)",
				false);
		// mtc_null_824.insertRegister(Ssc.Units.KWH, "194");
		MeterTimeswitch.insertMeterTimeswitch(null, "825", "8 hr OP (1-rate)",
				false);
		// mtc_null_825.insertRegister(Ssc.Units.KWH, "194");
		MeterTimeswitch.insertMeterTimeswitch(null, "826", "Eve / Weekend",
				false);
		// mtc_null_826.insertRegister(Ssc.Units.KWH, "72");
		// mtc_null_826.insertRegister(Ssc.Units.KWH, "184");
		MeterTimeswitch.insertMeterTimeswitch(null, "827", "Eve / Weekend",
				false);
		// mtc_null_827.insertRegister(Ssc.Units.KWH, "72");
		// mtc_null_827.insertRegister(Ssc.Units.KWH, "184");
		MeterTimeswitch.insertMeterTimeswitch(null, "828",
				"Evening / Weekend E7", false);
		// mtc_null_828.insertRegister(Ssc.Units.KWH, "184");
		// mtc_null_828.insertRegister(Ssc.Units.KWH, "187");
		// mtc_null_828.insertRegister(Ssc.Units.KWH, "210");
		MeterTimeswitch.insertMeterTimeswitch(null, "829",
				"Evening / Weekend E7", false);
		// mtc_null_829.insertRegister(Ssc.Units.KWH, "184");
		// mtc_null_829.insertRegister(Ssc.Units.KWH, "187");
		// mtc_null_829.insertRegister(Ssc.Units.KWH, "210");
		MeterTimeswitch.insertMeterTimeswitch(null, "830", "7 hr E7", false);
		// mtc_null_830
		// .insertRegister(Ssc.Units.KWH,
		// "1233, 1240, 1242, 1244, 1246, 1248, 1250, 1252, 1254, 1256, 1258");
		// mtc_null_830
		// .insertRegister(Ssc.Units.KWH,
		// "1234, 1241, 1243, 1245, 1247, 1249, 1251, 1253, 1255, 1257, 1259");
		MeterTimeswitch.insertMeterTimeswitch(null, "831", "7 hr E7", false);
		// mtc_null_831
		// .insertRegister(Ssc.Units.KWH,
		// "1233, 1240, 1242, 1244, 1246, 1248, 1250, 1252, 1254, 1256, 1258");
		// mtc_null_831
		// .insertRegister(Ssc.Units.KWH,
		// "1234, 1241, 1243, 1245, 1247, 1249, 1251, 1253, 1255, 1257, 1259");
		MeterTimeswitch.insertMeterTimeswitch(null, "832", "split 7 hr E7",
				false);
		// mtc_null_832.insertRegister(Ssc.Units.KWH,
		// "1371, 1373, 1375, 1377, 1379, 1381, 1383");
		// mtc_null_832.insertRegister(Ssc.Units.KWH,
		// "1372, 1374, 1376, 1378, 1380, 1382, 1384");
		MeterTimeswitch.insertMeterTimeswitch(null, "833",
				"Pre-payment single rate", false);
		// mtc_null_833.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "834",
				"Pre-payment two or more rates", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "835",
				"1-Rate Unrestricted PPM - Key", false);
		// mtc_null_835.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "836",
				"1-Rate Unrestricted PPM - Smartcard", false);
		// mtc_null_836.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "837",
				"1-Rate Unrestricted PPM - Token Meter (Small)", false);
		// mtc_null_837.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "838",
				"1-Rate Unrestricted PPM - Token Meter (Large)", false);
		// mtc_null_838.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "839",
				"1-Rate Unrestricted PPM - Token Meter (Small)", false);
		// mtc_null_839.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "840",
				"1-Rate Unrestricted PPM - Token Meter (Large)", false);
		// mtc_null_840.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "841",
				"1-Rate Unrestricted PPM - Token Acceptor Small", false);
		// mtc_null_841.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "842",
				"1-Rate Unrestricted PPM - Token Acceptor (Large)", false);
		// mtc_null_842.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "843",
				"1-Rate Unrestricted PPM - Token Acceptor (Small)", false);
		// mtc_null_843.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "844",
				"1-Rate Unrestricted PPM - Token Acceptor (Large)", false);
		// mtc_null_844.insertRegister(Ssc.Units.KWH, "1");
		MeterTimeswitch.insertMeterTimeswitch(null, "857", "Continuous", true);
		// mtc_null_857.insertRegister(Ssc.Units.KWH, "258");
		// mtc_null_857.insertRegister(Ssc.Units.KWH, "258");
		MeterTimeswitch
				.insertMeterTimeswitch(null, "858", "Dawn to Dusk", true);
		// mtc_null_858.insertRegister(Ssc.Units.KWH, "262");
		// mtc_null_858.insertRegister(Ssc.Units.KWH, "263");
		MeterTimeswitch
				.insertMeterTimeswitch(null, "859", "Dusk to Dawn", true);
		// mtc_null_859.insertRegister(Ssc.Units.KWH, "260");
		// mtc_null_859.insertRegister(Ssc.Units.KWH, "261");
		MeterTimeswitch.insertMeterTimeswitch(null, "860",
				"Half Night / Pre Dawn", true);
		// mtc_null_860.insertRegister(Ssc.Units.KWH, "264");
		// mtc_null_860.insertRegister(Ssc.Units.KWH, "265");
		MeterTimeswitch.insertMeterTimeswitch(null, "862", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "866", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "867", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "868", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "869", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "870", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "871", "Site Specific",
				true);
		MeterTimeswitch.insertMeterTimeswitch(null, "873", "", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "874", "", false);
		MeterTimeswitch.insertMeterTimeswitch(null, "890", "", false);
		ProfileClass pc00 = ProfileClass.getProfileClass(0);
		ProfileClass pc01 = ProfileClass.getProfileClass(1);
		ProfileClass pc02 = ProfileClass.getProfileClass(2);
		ProfileClass pc03 = ProfileClass.getProfileClass(3);
		ProfileClass pc04 = ProfileClass.getProfileClass(4);
		ProfileClass pc05 = ProfileClass.getProfileClass(5);
		ProfileClass pc06 = ProfileClass.getProfileClass(6);
		ProfileClass pc07 = ProfileClass.getProfileClass(7);
		ProfileClass pc08 = ProfileClass.getProfileClass(8);
		ProfileClass[] pc00array = new ProfileClass[1];
		pc00array[0] = pc00;
		ProfileClass[] pc01array = new ProfileClass[1];
		pc01array[0] = pc01;
		ProfileClass[] pc02array = new ProfileClass[1];
		pc02array[0] = pc02;
		ProfileClass[] pc03array = new ProfileClass[1];
		pc03array[0] = pc03;
		ProfileClass[] pc04array = new ProfileClass[1];
		pc04array[0] = pc04;
		ProfileClass[] pc05array = new ProfileClass[1];
		pc05array[0] = pc05;
		ProfileClass[] pc06array = new ProfileClass[1];
		pc06array[0] = pc06;
		ProfileClass[] pc07array = new ProfileClass[1];
		pc07array[0] = pc07;
		ProfileClass[] pc08array = new ProfileClass[1];
		pc08array[0] = pc08;
		ProfileClass[] pc05to08array = new ProfileClass[4];
		pc05to08array[0] = pc05;
		pc05to08array[1] = pc06;
		pc05to08array[2] = pc07;
		pc05to08array[3] = pc08;

		Dso dso14 = Dso.findDso("14");
		MeterTimeswitch.insertMeterTimeswitch(dso14, "001", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "002", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "003", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "004", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "005", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "006", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "007", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "008", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "009", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "010", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "011", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "021", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "022", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "023", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "024", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "026", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "031", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "032", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "033", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "034", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "035", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "036", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "037", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "038", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "039", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "056", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "058", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "059", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "511", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "512", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "513", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "517", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "522", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "523", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "524", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "526", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "531", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "532", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "533", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "534", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "536", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "537", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "538", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "539", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "540", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "541", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "551", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "556", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "565", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "560", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso14, "570", "", false);

		dso14.insertLlf(1, "Domestic Single Rate", "LV", false, true);
		dso14.insertLlf(2, "Domestic Prepayment Unrestricted", "LV", false,
				true);
		dso14.insertLlf(3, "Domestic Prepayment Unrestricted", "LV", false,
				true);
		dso14.insertLlf(4, "Domestic 2 Rate", "LV", false, true);
		dso14.insertLlf(5, "Domestic Prepayment 2 Rate", "LV", false, true);
		dso14.insertLlf(6, "Domestic Prepayment 2 Rate", "LV", false, true);
		dso14.insertLlf(7, "Small Non Domestic Single Rate", "LV", false, true);
		dso14.insertLlf(8, "Small Non Domestic Single Rate", "LV", false, true);
		dso14.insertLlf(9, "Small Non Domestic Single Rate", "LV", false, true);
		dso14.insertLlf(10, "Small Non Domestic 2 Rate", "LV", false, true);
		dso14.insertLlf(11, "Small Non Domestic 2 Rate", "LV", false, true);
		dso14.insertLlf(12, "Small Non Domestic 2 Rate", "LV", false, true);
		dso14
				.insertLlf(13, "Eve/Wkd Supply Tariff (1Ph WC)", "LV", false,
						true);
		dso14
				.insertLlf(14, "Eve/Wkd Supply Tariff (3Ph WC)", "LV", false,
						true);
		dso14
				.insertLlf(15, "Eve/Wkd Supply Tariff (3Ph CT)", "LV", false,
						true);
		dso14.insertLlf(20, "Medium Non Domestic LV 2 Rate", "LV", false, true);
		dso14.insertLlf(21, "Medium Non Domestic LV 2 Rate", "LV", false, true);
		dso14.insertLlf(22, "Medium Non Domestic LV 2 Rate", "LV", false, true);
		dso14.insertLlf(23,
				"MD Two Rate – HV (3Ph CT HV Exit Point, LV Meter)", "LV",
				false, true);
		dso14.insertLlf(25, "Medium Non Domestic LV 2 Rate", "LV", false, true);
		dso14.insertLlf(26, "Medium Non Domestic LV 2 Rate", "LV", false, true);
		dso14.insertLlf(27, "Medium Non Domestic LV 2 Rate", "LV", false, true);
		dso14.insertLlf(30, "Domestic 2 Rate", "LV", false, true);
		dso14.insertLlf(34, "Domestic Restricted (1Ph WC)", "LV", false, true);
		dso14.insertLlf(35, "Domestic Restricted (3Ph WC)", "LV", false, true);
		dso14.insertLlf(36, "Domestic Restricted (3Ph CT)", "LV", false, true);
		dso14.insertLlf(40, "Non Domestic Restricted (1Ph WC)", "LV", false,
				true);
		dso14.insertLlf(41, "Non Domestic Restricted (3Ph WC)", "LV", false,
				true);
		dso14.insertLlf(42, "Non Domestic Restricted (3Ph CT)", "LV", false,
				true);
		dso14.insertLlf(46, "Non Domestic Prepayment Unrestricted (1Ph WC)",
				"LV", false, true);
		dso14.insertLlf(47, "Non Domestic Prepayment Unrestricted (3Ph WC)",
				"LV", false, true);
		dso14.insertLlf(49, "Non Domestic Prepayment Unrestricted", "LV",
				false, true);
		dso14.insertLlf(85, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(86, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(87, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(88, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(95, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(96, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(97, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(98, "NHH Unmetered Supplies", "LV", false, true);
		dso14.insertLlf(107, "Small Non Domestic Single Rate", "LV", false,
				true);
		dso14.insertLlf(108, "Small Non Domestic Single Rate", "LV", false,
				true);
		dso14.insertLlf(109, "Small Non Domestic Single Rate", "LV", false,
				true);
		dso14.insertLlf(110, "Small Non Domestic 2 Rate", "LV", false, true);
		dso14.insertLlf(111, "Small Non Domestic 2 Rate", "LV", false, true);
		dso14.insertLlf(112, "Small Non Domestic 2 Rate", "LV", false, true);
		dso14
				.insertLlf(322, "Medium Non Domestic HV 2 Rate", "LV", false,
						true);
		dso14
				.insertLlf(323, "Medium Non Domestic HV 2 Rate", "LV", false,
						true);
		dso14.insertLlf(326, "MD Two Rate - LV (HV Meter)", "LV", false, true);
		dso14.insertLlf(620, "Export (LV 1Phase WC)", "LV", false, false);
		dso14.insertLlf(621, "Export (LV 3Phase WC)", "LV", false, false);
		dso14.insertLlf(622, "Export (LV 3Phase CT)", "LV", false, false);
		dso14.insertLlf(623, "Export (HV)", "HV", false, false);
		dso14.insertLlf(624, "Export (33kV)", "EHV", false, false);
		dso14.insertLlf(121, "LV Half Hourly", "LV", false, true);
		dso14.insertLlf(124, "LV Half Hourly", "LV", false, true);
		dso14.insertLlf(127, "LV Half Hourly", "LV", false, true);
		dso14.insertLlf(130, "MD HH HV (3Ph CT HV Exit Point, LV Meter)", "HV",
				false, true);
		dso14.insertLlf(132, "LV Half Hourly", "LV", false, true);
		dso14.insertLlf(365, "HV Half Hourly", "HV", false, true);
		dso14.insertLlf(522, "33kV EHV Import", "EHV", false, true);
		dso14.insertLlf(627, "LV HH Export 2005", "LV", false, false);
		dso14.insertLlf(628, "HV HH Export 2005", "HV", false, false);

		Dso dso20 = Dso.findDso("20");
		MeterTimeswitch.insertMeterTimeswitch(dso20, "001", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "002", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "003", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "004", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "005", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "006", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "007", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "008", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "009", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "010", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "011", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "012", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "013", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "014", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "015", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "016", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "017", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "018", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "019", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "020", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "023", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "024", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "025", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "026", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "027", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "028", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "029", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "030", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "031", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "032", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "033", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "034", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "035", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "036", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "039", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "040", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "041", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "042", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "043", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "044", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "045", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "046", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "049", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "050", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "051", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "052", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "053", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "064", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "065", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "066", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "067", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "070", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "071", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "072", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "073", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "074", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "075", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "076", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "077", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "078", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "079", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "080", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "081", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "082", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "083", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "084", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "085", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "091", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "092", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "104", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "105", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "106", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "107", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "108", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "109", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "110", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "111", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "126", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "127", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "128", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "129", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "130", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "131", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "132", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "133", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "134", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "135", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "136", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "137", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "378", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "379", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "380", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "381", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "382", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "383", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "384", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "385", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "386", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "387", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "388", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "389", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "390", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "391", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "392", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "393", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "394", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "397", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "398", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "510", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "511", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "512", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "513", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "514", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "515", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "516", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "517", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "518", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "519", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "520", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "523", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "524", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "525", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "526", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "527", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "528", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "529", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "530", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "531", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "532", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "533", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "534", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "535", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "536", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "539", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "540", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "541", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "542", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "543", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "544", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "545", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "546", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "547", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "548", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "549", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "550", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "551", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "552", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "553", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "554", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "555", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "564", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "565", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "566", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "567", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "568", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "569", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "570", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "571", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "572", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "573", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "574", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "575", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "576", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "577", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "578", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "579", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "580", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "581", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "582", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "583", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "584", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "585", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "586", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "587", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "588", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "589", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "591", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "592", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "600", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "601", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "602", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "603", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "604", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "605", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "606", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "607", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "608", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "609", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "610", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "611", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "615", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "616", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "617", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "618", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "619", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "620", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "621", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "622", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "623", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "630", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "631", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "632", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "633", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "634", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "635", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "636", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "637", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "638", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso20, "656", "", false);

		dso20.insertLlf(450, "Non-domestic Unrestricted LV HH", "LV", false,
				true);
		dso20.insertLlf(453, "Non-domestic Day/Night LV HH", "LV", false, true);
		dso20.insertLlf(520, "Unmetered Supplies LV HH", "LV", false, true);
		dso20.insertLlf(655, "Non-domestic Unrestricted HV HH", "HV", false,
				true);
		dso20.insertLlf(658, "Non-domestic Day/Night HV HH", "HV", false, true);
		dso20.insertLlf(909, "Embedded Generation - LV export", "LV", false,
				false);
		dso20.insertLlf(910, "Embedded Generation - HV export", "HV", false,
				false);
		dso20.insertLlf(930, "Embedded Generation - EHV export", "EHV", false,
				false);

		dso20.insertLlf(100, "Single Phase Domestic Unrestricted", "LV", false,
				true);
		dso20.insertLlf(101, "Three Phase Domestic Unrestricted", "LV", false,
				true);
		dso20.insertLlf(102, "Single Phase Domestic Unrestricted Key Meter",
				"LV", false, true);
		dso20.insertLlf(104, "Single Phase Domestic Economy 7", "LV", false,
				true);
		dso20.insertLlf(105, "Three Phase Domestic Economy 7", "LV", false,
				true);
		dso20.insertLlf(106, "Single Phase Domestic Economy 7 Key Meter", "LV",
				false, true);
		dso20.insertLlf(108, "Single Phase Domestic Flexiheat", "LV", false,
				true);
		dso20.insertLlf(109, "Three Phase Domestic Flexiheat", "LV", false,
				true);
		dso20.insertLlf(110, "Single Phase Domestic Superdeal", "LV", false,
				true);
		dso20.insertLlf(111, "Three Phase Domestic Superdeal", "LV", false,
				true);
		dso20.insertLlf(112, "Single Phase Domestic Off-Peak 'A'", "LV", false,
				true);
		dso20.insertLlf(113, "Single Phase Domestic Off-Peak 'B", "LV", false,
				true);
		dso20.insertLlf(114, "Single Phase Domestic Off-Peak 'Bx'", "LV",
				false, true);
		dso20.insertLlf(115, "Single Phase Domestic Off-Peak 'E'", "LV", false,
				true);
		dso20.insertLlf(116, "Single Phase Domestic Off-Peak 'F'", "LV", false,
				true);
		dso20.insertLlf(117, "Single Phase Domestic Off-Peak 'Fx'", "LV",
				false, true);
		dso20.insertLlf(118, "Three Phase Domestic Off-Peak 'A'", "LV", false,
				true);
		dso20.insertLlf(119, "Three Phase Domestic Off-Peak 'B'", "LV", false,
				true);
		dso20.insertLlf(120, "Three Phase Domestic Off-Peak 'Bx'", "LV", false,
				true);
		dso20.insertLlf(121, "Three Phase Domestic Off-Peak 'E'", "LV", false,
				true);
		dso20.insertLlf(122, "Three Phase Domestic Off-Peak 'F'", "LV", false,
				true);
		dso20.insertLlf(123, "Three Phase Domestic Off-Peak 'Fx'", "LV", false,
				true);
		dso20.insertLlf(124, "Single Phase Domestic White Meter", "LV", false,
				true);
		dso20.insertLlf(125, "Three Phase Domestic Whit e Meter", "LV", false,
				true);
		dso20.insertLlf(126, "Single Phase Non-domestic Unrestricted", "LV",
				false, true);
		dso20.insertLlf(127, "Three Phase Non-domestic Unrestricted", "LV",
				false, true);
		dso20.insertLlf(128,
				"Single Phase Non-domestic Unrestricted Key Meter", "LV",
				false, true);
		dso20.insertLlf(129, "Single Phase Non-domestic Day/Night", "LV",
				false, true);
		dso20.insertLlf(130, "Three Phase Non-domestic Day/Night", "LV", false,
				true);
		dso20.insertLlf(131, "Single Phase Non-domestic Day/Night Key Meter",
				"LV", false, true);
		dso20.insertLlf(133, "Single Phase Non-domestic Evening & Weekend",
				"LV", false, true);
		dso20.insertLlf(134, "Three Phase Non-domestic Evening & Weekend",
				"LV", false, true);
		dso20.insertLlf(135,
				"Single Phase Non-domestic Night/Evening & Weekend", "LV",
				false, true);
		dso20.insertLlf(136,
				"Three Phase Non-domestic Night/Evening & Weekend", "LV",
				false, true);
		dso20.insertLlf(138, "Single Phase Non-domestic Off Peak 'Ac'", "LV",
				false, true);
		dso20.insertLlf(139, "Single Phase Non-domestic Off Peak 'Bc'", "LV",
				false, true);
		dso20.insertLlf(140, "Single Phase Non-domestic Off Peak 'Ec'", "LV",
				false, true);
		dso20.insertLlf(141, "Single Phase Non-domestic Off Peak 'Fc'", "LV",
				false, true);
		dso20.insertLlf(142, "Three Phase Non-domestic Off Peak 'Ac'", "LV",
				false, true);
		dso20.insertLlf(143, "Three Phase Non-domestic Off Peak 'Bc'", "LV",
				false, true);
		dso20.insertLlf(144, "Three Phase Non-domestic Off Peak 'Ec'", "LV",
				false, true);
		dso20.insertLlf(145, "Three Phase Non-domestic Off Peak 'Fc'", "LV",
				false, true);
		dso20.insertLlf(150,
				"Single Phase Domestic Flexiheat (stored heat only)", "LV",
				false, true);
		dso20.insertLlf(151,
				"Three Phase Domestic Flexiheat (stored heat only)", "LV",
				false, true);
		dso20.insertLlf(152,
				"Single Phase Domestic Superdeal (stored heat only)", "LV",
				false, true);
		dso20.insertLlf(153,
				"Three Phase Domestic Superdeal (stored heat only)", "LV",
				false, true);
		dso20.insertLlf(154, "Single Phase Domestic Evening & Weekend", "LV",
				false, true);
		dso20.insertLlf(155, "Three Phase Domestic Evening & Weekend", "LV",
				false, true);
		dso20.insertLlf(156, "Single Phase Domestic Night/Evening & Weekend",
				"LV", false, true);
		dso20.insertLlf(157, "Three Phase Domestic Night/Evening & Weekend",
				"LV", false, true);
		dso20.insertLlf(400, "Non-domestic Unrestricted LV", "LV", false, true);
		dso20.insertLlf(401, "Non-domestic Day/Night LV", "LV", false, true);
		dso20.insertLlf(500, "Unmetered Supplies A CONT", "LV", false, true);
		dso20.insertLlf(501, "Unmetered Supplies B DU DA", "LV", false, true);
		dso20.insertLlf(502, "Unmetered Supplies C HN PD", "LV", false, true);
		dso20.insertLlf(503, "Unmetered Supplies D DA DU", "LV", false, true);
		dso20.insertLlf(504, "Unmetered Supplies BUD WARM", "LV", false, true);
		dso20.insertLlf(510, "Unmetered Supplies A CONT 2", "LV", false, true);
		dso20.insertLlf(511, "Unmetered Supplies B DU DA 2", "LV", false, true);
		dso20.insertLlf(512, "Unmetered Supplies C HN PD 2", "LV", false, true);
		dso20.insertLlf(513, "Unmetered Supplies D DA DU_2", "LV", false, true);
		dso20.insertLlf(605, "Non-domestic Unrestricted HV", "HV", false, true);
		dso20.insertLlf(606, "Non-domestic Day/Night HV", "HV", false, true);
		dso20.insertLlf(700, "Site specific", "HV", false, true);
		dso20.insertLlf(701, "Site specific", "HV", false, true);
		dso20.insertLlf(702, "Site specific", "HV", false, true);
		dso20.insertLlf(703, "Site specific", "HV", false, true);
		dso20.insertLlf(704, "Site specific", "HV", false, true);
		dso20.insertLlf(705, "Site specific", "HV", false, true);
		dso20.insertLlf(706, "Site specific", "HV", false, true);
		dso20.insertLlf(707, "Site specific", "HV", false, true);
		dso20.insertLlf(708, "Site specific", "HV", false, true);
		dso20.insertLlf(709, "Site specific", "HV", false, true);
		dso20.insertLlf(710, "Site specific", "HV", false, true);
		dso20.insertLlf(711, "Site specific", "HV", false, true);
		dso20.insertLlf(712, "Site specific", "HV", false, true);
		dso20.insertLlf(713, "Site specific", "HV", false, true);
		dso20.insertLlf(714, "Site specific", "HV", false, true);
		dso20.insertLlf(715, "Site specific", "HV", false, true);
		dso20.insertLlf(716, "Site specific", "HV", false, true);
		dso20.insertLlf(717, "Site specific", "HV", false, true);
		dso20.insertLlf(718, "Site specific", "HV", false, true);
		dso20.insertLlf(719, "Site specific", "HV", false, true);
		dso20.insertLlf(720, "Site specific", "HV", false, true);
		dso20.insertLlf(721, "Site specific", "HV", false, true);
		dso20.insertLlf(722, "Site specific", "HV", false, true);
		dso20.insertLlf(723, "Site specific", "HV", false, true);
		dso20.insertLlf(724, "Site specific", "HV", false, true);
		dso20.insertLlf(725, "Site specific", "HV", false, true);
		dso20.insertLlf(726, "Site specific", "HV", false, true);
		dso20.insertLlf(727, "Site specific", "HV", false, true);
		dso20.insertLlf(728, "Site specific", "HV", false, true);
		dso20.insertLlf(729, "Site specific", "HV", false, true);
		dso20.insertLlf(730, "Site specific", "HV", false, true);
		dso20.insertLlf(731, "Site specific", "HV", false, true);
		dso20.insertLlf(732, "Site specific", "HV", false, true);
		dso20.insertLlf(733, "Site specific", "HV", false, true);
		dso20.insertLlf(734, "Site specific", "HV", false, true);
		dso20.insertLlf(735, "Site specific", "HV", false, true);
		dso20.insertLlf(736, "Site specific", "HV", false, true);
		dso20.insertLlf(737, "Site specific", "HV", false, true);
		dso20.insertLlf(738, "Site specific", "HV", false, true);
		dso20.insertLlf(739, "Site specific", "HV", false, true);
		dso20.insertLlf(740, "Site specific", "HV", false, true);
		dso20.insertLlf(741, "Site specific", "HV", false, true);
		dso20.insertLlf(742, "Site specific", "HV", false, true);
		dso20.insertLlf(743, "Site specific", "HV", false, true);
		dso20.insertLlf(744, "Site specific", "HV", false, true);
		dso20.insertLlf(745, "Site specific", "HV", false, true);
		dso20.insertLlf(746, "Site specific", "HV", false, true);
		dso20.insertLlf(747, "Site specific", "HV", false, true);
		dso20.insertLlf(748, "Site specific", "HV", false, true);
		dso20.insertLlf(749, "Site specific", "HV", false, true);
		dso20.insertLlf(750, "Site specific", "HV", false, true);
		dso20.insertLlf(751, "Site specific", "HV", false, true);
		dso20.insertLlf(752, "Site specific", "HV", false, true);
		dso20.insertLlf(753, "Site specific", "HV", false, true);
		dso20.insertLlf(754, "Site specific", "HV", false, true);
		dso20.insertLlf(755, "Site specific", "HV", false, true);
		dso20.insertLlf(756, "Site specific", "HV", false, true);
		dso20.insertLlf(757, "Site specific", "HV", false, true);
		dso20.insertLlf(758, "Site specific", "HV", false, true);
		dso20.insertLlf(759, "Site specific", "HV", false, true);
		dso20.insertLlf(760, "Site specific", "HV", false, true);
		dso20.insertLlf(761, "Site specific", "HV", false, true);
		dso20.insertLlf(762, "Site specific", "HV", false, true);
		dso20.insertLlf(763, "Site specific", "HV", false, true);
		dso20.insertLlf(764, "Site specific", "HV", false, true);
		dso20.insertLlf(765, "Site specific", "HV", false, true);
		dso20.insertLlf(766, "Site specific", "HV", false, true);
		dso20.insertLlf(767, "Site specific", "HV", false, true);
		dso20.insertLlf(768, "Site specific", "HV", false, true);
		dso20.insertLlf(769, "Site specific", "HV", false, true);
		dso20.insertLlf(770, "Site specific", "HV", false, true);
		dso20.insertLlf(771, "Site specific", "HV", false, true);
		dso20.insertLlf(772, "Site specific", "HV", false, true);
		dso20.insertLlf(773, "Site specific", "HV", false, true);
		dso20.insertLlf(774, "Site specific", "HV", false, true);
		dso20.insertLlf(775, "Site specific", "HV", false, true);
		dso20.insertLlf(776, "Site specific", "HV", false, true);
		dso20.insertLlf(777, "Site specific", "HV", false, true);
		dso20.insertLlf(778, "Site specific", "HV", false, true);
		dso20.insertLlf(779, "Site specific", "HV", false, true);
		dso20.insertLlf(780, "Site specific", "HV", false, true);
		dso20.insertLlf(781, "Site specific", "HV", false, true);
		dso20.insertLlf(782, "Site specific", "HV", false, true);
		dso20.insertLlf(783, "Site specific", "HV", false, true);
		dso20.insertLlf(784, "Site specific", "HV", false, true);
		dso20.insertLlf(785, "Site specific", "HV", false, true);
		dso20.insertLlf(786, "Site specific", "HV", false, true);
		dso20.insertLlf(787, "Site specific", "HV", false, true);
		dso20.insertLlf(788, "Site specific", "HV", false, true);
		dso20.insertLlf(789, "Site specific", "HV", false, true);
		dso20.insertLlf(790, "Site specific", "HV", false, true);
		dso20.insertLlf(791, "Site specific", "HV", false, true);
		dso20.insertLlf(792, "Site specific", "HV", false, true);
		dso20.insertLlf(793, "Site specific", "HV", false, true);
		dso20.insertLlf(794, "Site specific", "HV", false, true);
		dso20.insertLlf(795, "Site specific", "HV", false, true);
		dso20.insertLlf(796, "Site specific", "HV", false, true);
		dso20.insertLlf(797, "Site specific", "HV", false, true);
		dso20.insertLlf(798, "Site specific", "HV", false, true);
		dso20.insertLlf(799, "Site specific", "HV", false, true);
		dso20.insertLlf(800, "Site specific", "HV", false, true);
		dso20.insertLlf(801, "Site specific", "HV", false, true);
		dso20.insertLlf(802, "Site specific", "HV", false, true);
		dso20.insertLlf(803, "Site specific", "HV", false, true);
		dso20.insertLlf(804, "Site specific", "HV", false, true);
		dso20.insertLlf(805, "Site specific", "HV", false, true);
		dso20.insertLlf(806, "Site specific", "HV", false, true);
		dso20.insertLlf(807, "Site specific", "HV", false, true);
		dso20.insertLlf(808, "Site specific", "HV", false, true);
		dso20.insertLlf(809, "Site specific", "HV", false, true);
		dso20.insertLlf(810, "Site specific", "HV", false, true);
		dso20.insertLlf(811, "Site specific", "HV", false, true);
		dso20.insertLlf(812, "Site specific", "HV", false, true);
		dso20.insertLlf(813, "Site specific", "HV", false, true);
		dso20.insertLlf(814, "Site specific", "HV", false, true);
		dso20.insertLlf(815, "Site specific", "HV", false, true);
		dso20.insertLlf(816, "Site specific", "HV", false, true);
		dso20.insertLlf(817, "Site specific", "HV", false, true);
		dso20.insertLlf(818, "Site specific", "HV", false, true);
		dso20.insertLlf(819, "Site specific", "HV", false, true);
		dso20.insertLlf(820, "Site specific", "HV", false, true);
		dso20.insertLlf(821, "Site specific", "HV", false, true);
		dso20.insertLlf(822, "Site specific", "HV", false, true);
		dso20.insertLlf(823, "Site specific", "HV", false, true);
		dso20.insertLlf(824, "Site specific", "HV", false, true);
		dso20.insertLlf(825, "Site specific", "HV", false, true);
		dso20.insertLlf(826, "Site specific", "HV", false, true);
		dso20.insertLlf(827, "Site specific", "HV", false, true);
		dso20.insertLlf(828, "Site specific", "HV", false, true);
		dso20.insertLlf(829, "Site specific", "HV", false, true);
		dso20.insertLlf(830, "Site specific", "HV", false, true);
		dso20.insertLlf(831, "Site specific", "HV", false, true);
		dso20.insertLlf(832, "Site specific", "HV", false, true);
		dso20.insertLlf(833, "Site specific", "HV", false, true);
		dso20.insertLlf(834, "Site specific", "HV", false, true);
		dso20.insertLlf(835, "Site specific", "HV", false, true);
		dso20.insertLlf(836, "Site specific", "HV", false, true);
		dso20.insertLlf(837, "Site specific", "HV", false, true);
		dso20.insertLlf(838, "Site specific", "HV", false, true);
		dso20.insertLlf(839, "Site specific", "HV", false, true);
		dso20.insertLlf(840, "Site specific", "HV", false, true);
		dso20.insertLlf(841, "Site specific", "HV", false, true);
		dso20.insertLlf(842, "Site specific", "HV", false, true);
		dso20.insertLlf(843, "Site specific", "HV", false, true);
		dso20.insertLlf(844, "Site specific", "HV", false, true);
		dso20.insertLlf(845, "Site specific", "HV", false, true);
		dso20.insertLlf(846, "Site specific", "HV", false, true);
		dso20.insertLlf(847, "Site specific", "HV", false, true);
		dso20.insertLlf(848, "Site specific", "HV", false, true);
		dso20.insertLlf(849, "Site specific", "HV", false, true);
		dso20.insertLlf(850, "Site specific", "HV", false, true);
		dso20.insertLlf(851, "Site specific", "HV", false, true);
		dso20.insertLlf(852, "Site specific", "HV", false, true);
		dso20.insertLlf(853, "Site specific", "HV", false, true);
		dso20.insertLlf(854, "Site specific", "HV", false, true);
		dso20.insertLlf(855, "Site specific", "HV", false, true);
		dso20.insertLlf(856, "Site specific", "HV", false, true);
		dso20.insertLlf(857, "Site specific", "HV", false, true);
		dso20.insertLlf(858, "Site specific", "HV", false, true);
		dso20.insertLlf(859, "Site specific", "HV", false, true);
		dso20.insertLlf(860, "Site specific", "HV", false, true);
		dso20.insertLlf(861, "Site specific", "HV", false, true);
		dso20.insertLlf(862, "Site specific", "HV", false, true);
		dso20.insertLlf(863, "Site specific", "HV", false, true);
		dso20.insertLlf(864, "Site specific", "HV", false, true);
		dso20.insertLlf(865, "Site specific", "HV", false, true);
		dso20.insertLlf(866, "Site specific", "HV", false, true);
		dso20.insertLlf(867, "Site specific", "HV", false, true);
		dso20.insertLlf(868, "Site specific", "HV", false, true);
		dso20.insertLlf(869, "Site specific", "HV", false, true);
		dso20.insertLlf(870, "Site specific", "HV", false, true);
		dso20.insertLlf(871, "Site specific", "HV", false, true);
		dso20.insertLlf(872, "Site specific", "HV", false, true);
		dso20.insertLlf(873, "Site specific", "HV", false, true);
		dso20.insertLlf(874, "Site specific", "HV", false, true);
		dso20.insertLlf(875, "Site specific", "HV", false, true);
		dso20.insertLlf(876, "Site specific", "HV", false, true);
		dso20.insertLlf(877, "Site specific", "HV", false, true);
		dso20.insertLlf(878, "Site specific", "HV", false, true);
		dso20.insertLlf(879, "Site specific", "HV", false, true);
		dso20.insertLlf(880, "Site specific", "HV", false, true);
		dso20.insertLlf(881, "Site specific", "HV", false, true);
		dso20.insertLlf(882, "Site specific", "HV", false, true);
		dso20.insertLlf(883, "Site specific", "HV", false, true);
		dso20.insertLlf(884, "Site specific", "HV", false, true);
		dso20.insertLlf(885, "Site specific", "HV", false, true);
		dso20.insertLlf(886, "Site specific", "HV", false, true);
		dso20.insertLlf(887, "Site specific", "HV", false, true);
		dso20.insertLlf(888, "Site specific", "HV", false, true);
		dso20.insertLlf(889, "Site specific", "HV", false, true);
		dso20.insertLlf(890, "Site specific", "HV", false, true);
		dso20.insertLlf(891, "Site specific", "HV", false, true);
		dso20.insertLlf(892, "Site specific", "HV", false, true);
		dso20.insertLlf(893, "Site specific", "HV", false, true);
		dso20.insertLlf(894, "Site specific", "HV", false, true);
		dso20.insertLlf(895, "Site specific", "HV", false, true);
		dso20.insertLlf(896, "Site specific", "HV", false, true);
		dso20.insertLlf(897, "Site specific", "HV", false, true);
		dso20.insertLlf(898, "Site specific", "HV", false, true);
		dso20.insertLlf(899, "Site specific", "HV", false, true);
		dso20.insertLlf(900, "Site specific", "HV", false, true);
		dso20.insertLlf(901, "Site specific", "HV", false, true);
		dso20.insertLlf(902, "Site specific", "HV", false, true);
		dso20.insertLlf(903, "Site specific", "HV", false, true);
		dso20.insertLlf(904, "Site specific", "HV", false, true);
		dso20.insertLlf(905, "Site specific", "HV", false, true);
		dso20.insertLlf(906, "Site specific", "HV", false, true);
		dso20.insertLlf(907, "Site specific", "HV", false, true);
		dso20.insertLlf(908, "Site specific", "HV", false, true);
		dso20.insertLlf(911, "Site specific", "HV", false, true);
		dso20.insertLlf(912, "Site specific", "HV", false, true);
		dso20.insertLlf(913, "Site specific", "HV", false, true);
		dso20.insertLlf(914, "Site specific", "HV", false, true);
		dso20.insertLlf(915, "Site specific", "HV", false, true);
		dso20.insertLlf(916, "Site specific", "HV", false, true);
		dso20.insertLlf(917, "Site specific", "HV", false, true);
		dso20.insertLlf(918, "Site specific", "HV", false, true);
		dso20.insertLlf(919, "Site specific", "HV", false, true);
		dso20.insertLlf(920, "Site specific", "HV", false, true);
		dso20.insertLlf(921, "Site specific", "HV", false, true);
		dso20.insertLlf(922, "Site specific", "HV", false, true);
		dso20.insertLlf(923, "Site specific", "HV", false, true);
		dso20.insertLlf(924, "Site specific", "HV", false, true);
		dso20.insertLlf(925, "Site specific", "HV", false, true);
		dso20.insertLlf(926, "Site specific", "HV", false, true);
		dso20.insertLlf(927, "Site specific", "HV", false, true);
		dso20.insertLlf(928, "Site specific", "HV", false, true);
		dso20.insertLlf(929, "Site specific", "HV", false, true);

		dso20.insertLlf(931,
				"LV export - Non Small Scaled Embedded Generation", "LV",
				false, true);
		dso20.insertLlf(932, "LV export - Small Scaled Embedded Generation",
				"LV", false, true);
		Dso dso22 = Dso.findDso("22");
		MeterTimeswitch.insertMeterTimeswitch(dso22, "0", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "1", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "2", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "3", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "4", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "5", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "6", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "7", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "8", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "9", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "10", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "11", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "12", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "13", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "14", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "15", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "16", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "17", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "18", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "19", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "20", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "21", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "22", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "23", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "24", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "25", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "26", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "27", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "29", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "30", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "31", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "32", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "33", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "34", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "35", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "36", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "37", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "38", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "39", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "40", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "41", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "42", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "43", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "44", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "45", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "46", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "47", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "48", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "49", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "50", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "51", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "52", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "53", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "54", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "55", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "56", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "57", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "58", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "60", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "62", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "63", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "64", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "65", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "66", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "67", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "68", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "69", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "70", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "71", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "72", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "74", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "510", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "511", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "512", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "513", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "514", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "515", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "516", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "517", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "518", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "519", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "520", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "521", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "522", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "523", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "524", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "525", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "526", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "527", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "528", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "529", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "530", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "531", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "532", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "533", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "534", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "535", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "536", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "537", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "539", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "540", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "541", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "542", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "543", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "544", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "545", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "546", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "547", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "548", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "549", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "550", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "551", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "552", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "553", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "554", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "555", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "556", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "557", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "558", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "559", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "560", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "561", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "562", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "563", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "564", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "565", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "566", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "567", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "568", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "569", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "570", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "572", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "573", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "574", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "575", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "576", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "577", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "578", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "579", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "580", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "581", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "582", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "583", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "584", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "585", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "586", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "587", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "588", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "589", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "590", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "591", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "592", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "593", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "594", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "595", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "596", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "597", "", false);
		MeterTimeswitch.insertMeterTimeswitch(dso22, "599", "", false);

		dso22.insertLlf(10, "Profile 1 Unrestricted", "LV", false, true);
		dso22.insertLlf(11, "Profile 1 Export LV", "LV", false, true);
		dso22
				.insertLlf(20, "Profile 1 Key Mtr Unrestricted", "LV", false,
						true);
		dso22.insertLlf(30, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(31, "Profile 2 Export LV", "LV", false, true);
		dso22.insertLlf(40, "Profile 2 Key Meter Economy 7", "LV", false, true);
		dso22.insertLlf(50, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(51, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(60, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(61, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(70, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(110, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(111, "Profile 3 Export LV", "LV", false, false);
		dso22.insertLlf(120, "Profile 3 Key Mtr Unrestricted", "LV", false,
				true);
		dso22.insertLlf(130, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(140, "Kry Mtr Unrestricted", "LV", false, true);
		dso22.insertLlf(210, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(211, "Profile 4 Export LV", "LV", false, false);
		dso22
				.insertLlf(220, "Profile 4 Key Meter Economy 7", "LV", false,
						true);
		dso22.insertLlf(230, "Profile 4 Economy 7", "LV", false, true);
		dso22
				.insertLlf(240, "Profile 4 Key Meter Economy 7", "LV", false,
						true);
		dso22.insertLlf(250, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(251, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(260, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(261, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(270, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(280, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(281, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(310, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(320, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(330, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(340, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(350, "Profile 4 Economy 7", "LV", false, true);
		dso22.insertLlf(410, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(415, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(420, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(425, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(430, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(435, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(440, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(445, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(450, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(455, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(460, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(470, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(480, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(510, "PC 05-Aug & HH HV", "HV", false, true);
		dso22.insertLlf(520, "PC 05-Aug & HH HV (Parallel Gen)", "HV", false,
				true);
		dso22.insertLlf(521, "Export (HV)", "HV", false, false);
		dso22.insertLlf(540, "PC 05-Aug & HH S/S", "LV", true, true);
		dso22.insertLlf(550, "PC 05-Aug & HH S/S (Parallel Gen)", "LV", true,
				true);
		dso22.insertLlf(551, "Export (S/S)", "LV", true, false);
		dso22.insertLlf(570, "PC 05-Aug & HH LV", "LV", false, true);
		dso22.insertLlf(580, "PC 05-Aug & HH LV (Parallel Gen)", "LV", false,
				true);
		dso22.insertLlf(581, "Export (LV)", "LV", false, false);

		// LineLossFactor llf22_510 = dso22.getLineLossFactor("510");
		// LineLossFactor llf22_520 = dso22.insertLlf(520",
		// "PC 5-8 & HH HV (Parallel Gen)", "HV", false,
		// false);
		// LineLossFactor llf22_520 = dso22.getLineLossFactor("520");
		// LineLossFactor llf22_521 = dso22.insertLlf(521",
		// "Export (HV)", "HV", false, false);
		// LineLossFactor llf22_521 = dso22.getLineLossFactor("521");
		// LineLossFactor llf22_540 = dso22.insertLlf(540",
		// "PC 5-8 & HH S/S", "LV", true, true);
		// LineLossFactor llf22_540 = dso22.getLineLossFactor("540");
		// LineLossFactor llf22_550 = dso22.insertLlf(550",
		// "PC 5-8 & HH S/S (Parallel Gen)", "LV", true,
		// true);
		// LineLossFactor llf22_550 = dso22.getLineLossFactor("550");
		// LineLossFactor llf22_551 = dso22.insertLlf(551",
		// "Export (S/S)", "LV", true, false);
		// LineLossFactor llf22_551 = dso22.getLineLossFactor("551");
		// LineLossFactor llf22_570 = dso22.insertLlf(570",
		// "PC 5-8 & HH LV", "LV", false, true);
		// LineLossFactor llf22_570 = dso22.getLineLossFactor("570");
		// LineLossFactor llf22_580 = dso22.insertLlf(580",
		// "PC 5-8 & HH LV (Parallel Gen)", "LV", false,
		// true);
		// LineLossFactor llf22_580 = dso22.getLineLossFactor("580");
		// LineLossFactor llf22_581 = dso22.insertLlf(581",
		// "Export (LV)", "LV", false, false);
		// LineLossFactor llf22_581 = dso22.getLineLossFactor("581");
		dso22.insertLlf(840, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(850, "Profile 2 Economy 7", "LV", false, true);
		dso22.insertLlf(860, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(870, "Profile 1 Unrestricted", "LV", false, true);
		dso22.insertLlf(890, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(900, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(910, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(920, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(930, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(950, "Profile 3 Unrestricted", "LV", false, true);
		dso22.insertLlf(970, "Unmetered Pseudo Metered", "LV", false, true);
		dso22.insertLlf(980, "PC 1&8 Unmetered Profiled", "LV", false, true);
		Hiber.flush();
		Dso dso98 = Dso.findDso("98");
		dso98.insertLlf(000, "LV Substation Import", "LV", true, true);
		dso98.insertLlf(001, "LV Substation Export", "LV", true, false);
		dso98.insertLlf(002, "LV Network Import", "LV", false, true);
		dso98.insertLlf(003, "LV Network Export", "LV", false, false);
		dso98.insertLlf(004, "HV Substation Import", "HV", true, true);
		dso98.insertLlf(005, "HV Substation Export", "HV", true, false);
		dso98.insertLlf(006, "HV Network Import", "HV", false, true);
		dso98.insertLlf(007, "HV Network Export", "HV", false, false);
		Dso dso99 = Dso.findDso("99");
		dso99.insertLlf(000, "LV Substation Import", "LV", true, true);
		dso99.insertLlf(001, "LV Substation Export", "LV", true, false);
		dso99.insertLlf(002, "LV Network Import", "LV", false, true);
		dso99.insertLlf(003, "LV Network Export", "LV", false, false);
		dso99.insertLlf(004, "HV Substation Import", "HV", true, true);
		dso99.insertLlf(005, "HV Substation Export", "HV", true, false);
		dso99.insertLlf(006, "HV Network Import", "HV", false, true);
		dso99.insertLlf(007, "HV Network Export", "HV", false, false);
		Hiber.flush();
		/*
		 * llf14_620.attachProfileClass(profileClass00);
		 * llf14_620.addMeterTimeswitch("845");
		 * llf14_620.addMeterTimeswitch("846");
		 * llf14_621.attachProfileClass(profileClass00);
		 * llf14_621.addMeterTimeswitch("845");
		 * llf14_621.addMeterTimeswitch("846");
		 * llf14_622.attachProfileClass(profileClass00);
		 * llf14_622.addMeterTimeswitch("845");
		 * llf14_622.addMeterTimeswitch("846");
		 * llf14_001.attachProfileClass(pc01); llf14_001
		 * .addMeterTimeswitches("3, 36, 37, 500, 512, 513, 531, 565, 8, 801,
		 * 802, 809, 811, 812,814, 835, 837, 838,842");
		 * llf14_002.attachProfileClass(pc01);
		 * llf14_002.addMeterTimeswitches("512, 513, 837, 838, 842");
		 * llf14_003.attachProfileClass(pc01);
		 * llf14_003.addMeterTimeswitches("3, 8, 36, 37, 837");
		 * llf14_004.attachProfileClass(pc02); llf14_004
		 * .addMeterTimeswitches("1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 21, 22, 24,
		 * 26, 38, 39, 59, 500, 511,522, 523, 524, 532,533, 534, 538, 539,540,
		 * 809, 811, 812,814, 864, 865, 890");
		 * llf14_005.attachProfileClass(pc02);
		 * llf14_005.addMeterTimeswitches("4, 5, 9, 10, 38, 39, 523");
		 * llf14_006.attachProfileClass(pc02);
		 * llf14_006.addMeterTimeswitches("1, 2, 3, 6, 7, 8, 523");
		 * llf14_007.attachProfileClass(pc03); llf14_007
		 * .addMeterTimeswitches("1, 2, 3, 4, 5, 8, 9, 31,38, 500, 512, 524,
		 * 551,565, 801, 802, 809,811, 812, 814, 835,838, 842, 873");
		 * llf14_008.attachProfileClass(pc03); llf14_008
		 * .addMeterTimeswitches("4, 5, 31, 38, 500, 512,524, 551, 565, 801,802,
		 * 809, 811, 812,814, 838, 842"); llf14_010.attachProfileClass(pc04);
		 * llf14_010 .addMeterTimeswitches("21, 23, 26, 58, 511,524, 532, 533,
		 * 536,537, 538, 540, 541,809, 811, 812, 814,874, 890");
		 * llf14_011.attachProfileClass(pc04); llf14_011
		 * .addMeterTimeswitches("21, 23, 26, 58, 511,524, 532, 533, 536,537,
		 * 538, 540, 541,809, 811, 812, 814");
		 * llf14_012.attachProfileClass(pc04); llf14_012
		 * .addMeterTimeswitches("21, 23, 26, 58, 511,524, 532, 533, 536,537,
		 * 538, 540, 541,809, 811, 812"); llf14_013.attachProfileClass(pc03);
		 * llf14_013.addMeterTimeswitches("31, 551");
		 * llf14_014.attachProfileClass(pc03);
		 * llf14_014.addMeterTimeswitches("31, 551");
		 * llf14_015.attachProfileClass(pc03);
		 * llf14_015.addMeterTimeswitches("31, 551");
		 * llf14_020.attachProfileClass(pc05);
		 * llf14_020.attachProfileClass(pc06);
		 * llf14_020.attachProfileClass(pc07);
		 * llf14_020.attachProfileClass(pc08); llf14_020
		 * .addMeterTimeswitches("32, 33, 34, 35, 56,500, 517, 524, 526,556,
		 * 560, 565, 570,801, 802, 811, 812,874");
		 * llf14_021.attachProfileClass(pc05);
		 * llf14_021.attachProfileClass(pc06);
		 * llf14_021.attachProfileClass(pc07);
		 * llf14_021.attachProfileClass(pc08); llf14_021
		 * .addMeterTimeswitches("32, 33, 34, 35, 56,500, 517, 524, 526,556,
		 * 560, 565, 570,801, 802, 811, 812");
		 * llf14_022.attachProfileClass(pc05);
		 * llf14_022.attachProfileClass(pc06);
		 * llf14_022.attachProfileClass(pc07);
		 * llf14_022.attachProfileClass(pc08); llf14_022
		 * .addMeterTimeswitches("32, 33, 34, 35, 56,500, 517, 524, 526,556,
		 * 560, 565, 570,801, 802, 811, 812");
		 * llf14_023.attachProfileClass(pc05);
		 * llf14_023.attachProfileClass(pc06);
		 * llf14_023.attachProfileClass(pc07);
		 * llf14_023.attachProfileClass(pc08);
		 * llf14_023.addMeterTimeswitches("524, 526, 811, 812");
		 * llf14_025.attachProfileClass(pc05);
		 * llf14_025.attachProfileClass(pc06);
		 * llf14_025.attachProfileClass(pc07);
		 * llf14_025.attachProfileClass(pc08); llf14_025
		 * .addMeterTimeswitches("32, 33, 34, 35, 56,500, 517, 524, 526,556,
		 * 560, 565, 570,801, 802, 811, 812");
		 * llf14_026.attachProfileClass(pc05);
		 * llf14_026.attachProfileClass(pc06);
		 * llf14_026.attachProfileClass(pc07);
		 * llf14_026.attachProfileClass(pc08); llf14_026
		 * .addMeterTimeswitches("32, 33, 34, 35, 56,500, 517, 524, 526,556,
		 * 560, 565, 570,801, 802, 811, 812");
		 * llf14_027.attachProfileClass(pc05);
		 * llf14_027.attachProfileClass(pc06);
		 * llf14_027.attachProfileClass(pc07);
		 * llf14_027.attachProfileClass(pc08); llf14_027
		 * .addMeterTimeswitches("32, 33, 34, 35, 56,500, 517, 524, 526,556,
		 * 560, 565, 570,801, 802, 811, 812");
		 * llf14_030.attachProfileClass(pc02);
		 * llf14_030.addMeterTimeswitches("11");
		 * llf14_034.attachProfileClass(pc02); llf14_034
		 * .addMeterTimeswitches("21, 22, 24, 59, 500,532, 533, 534, 538");
		 * llf14_035.attachProfileClass(pc02); llf14_035
		 * .addMeterTimeswitches("21, 22, 24, 59, 532,533, 534, 538, 539");
		 * llf14_036.attachProfileClass(pc02); llf14_036
		 * .addMeterTimeswitches("21, 22, 24, 59, 532,533, 534, 538, 539");
		 * llf14_040.attachProfileClass(pc04); llf14_040
		 * .addMeterTimeswitches("21, 23, 26, 511, 524,532, 533, 536, 537,541,
		 * 811"); llf14_041.attachProfileClass(pc04);
		 * llf14_041.addMeterTimeswitches("21, 23, 532, 533, 536,537, 540,
		 * 541"); llf14_042.attachProfileClass(pc04);
		 * llf14_042.addMeterTimeswitches("23, 536, 537, 538, 541");
		 * llf14_046.attachProfileClass(pc03);
		 * llf14_046.addMeterTimeswitches("512, 838, 842");
		 * llf14_047.attachProfileClass(pc03);
		 * llf14_047.addMeterTimeswitches("512, 838, 842");
		 * llf14_049.attachProfileClass(pc03);
		 * llf14_049.addMeterTimeswitches("3, 8");
		 * llf14_085.attachProfileClass(pc08);
		 * llf14_085.addMeterTimeswitches("502");
		 * llf14_086.attachProfileClass(pc01);
		 * llf14_086.addMeterTimeswitches("504");
		 * llf14_087.attachProfileClass(pc01);
		 * llf14_087.addMeterTimeswitches("505");
		 * llf14_088.attachProfileClass(pc01);
		 * llf14_088.addMeterTimeswitches("503");
		 * llf14_095.attachProfileClass(pc08);
		 * llf14_095.addMeterTimeswitches("502");
		 * llf14_096.attachProfileClass(pc01);
		 * llf14_096.addMeterTimeswitches("504");
		 * llf14_097.attachProfileClass(pc01);
		 * llf14_097.addMeterTimeswitches("505");
		 * llf14_098.attachProfileClass(pc01);
		 * llf14_098.addMeterTimeswitches("503");
		 * llf14_107.attachProfileClass(pc03); llf14_107
		 * .addMeterTimeswitches("1, 2, 3, 4, 5, 8, 9, 31,38, 500, 512, 524,
		 * 551,565, 801, 802, 809,811, 812, 814, 838,842");
		 * llf14_108.attachProfileClass(pc03); llf14_108
		 * .addMeterTimeswitches("4, 5, 31, 38, 500, 512,524, 551, 565, 801,802,
		 * 809, 811, 812,814, 838, 842"); llf14_109.attachProfileClass(pc03);
		 * llf14_109 .addMeterTimeswitches("31, 500, 524, 551, 565,801, 802,
		 * 811, 812"); llf14_110.attachProfileClass(pc04); llf14_110
		 * .addMeterTimeswitches("21, 23, 26, 58, 511,524, 532, 533, 536,537,
		 * 538, 540, 541,809, 811, 812, 814");
		 * llf14_111.attachProfileClass(pc04); llf14_111
		 * .addMeterTimeswitches("21, 23, 26, 58, 511,524, 532, 533, 536,537,
		 * 538, 540, 541,809, 811, 812, 814");
		 * llf14_112.attachProfileClass(pc04); llf14_112
		 * .addMeterTimeswitches("21, 23, 26, 58, 511,524, 532, 533, 536,537,
		 * 538, 540, 541,809, 811, 812"); llf14_322.attachProfileClass(pc05);
		 * llf14_322.attachProfileClass(pc06);
		 * llf14_322.attachProfileClass(pc07);
		 * llf14_322.attachProfileClass(pc08);
		 * llf14_322.addMeterTimeswitches("33, 34, 524, 526, 811,812");
		 * llf14_323.attachProfileClass(pc05);
		 * llf14_323.attachProfileClass(pc06);
		 * llf14_323.attachProfileClass(pc07);
		 * llf14_323.attachProfileClass(pc08);
		 * llf14_323.addMeterTimeswitches("33, 34, 524, 526, 811,812");
		 * llf14_326.attachProfileClass(pc06);
		 * llf14_326.addMeterTimeswitches("812");
		 * llf14_620.attachProfileClass(profileClass00);
		 * llf14_620.addMeterTimeswitch("845");
		 * llf14_620.addMeterTimeswitch("846");
		 * llf14_621.attachProfileClass(profileClass00);
		 * llf14_621.addMeterTimeswitch("845");
		 * llf14_621.addMeterTimeswitch("846");
		 */
		/*
		MpanTop.insertMpanTops(dso14, pc00array, "845", 622, "09999");
		MpanTop.insertMpanTops(dso14, pc00array, "846", 622, "09999");

		MpanTop
				.insertMpanTops(
						dso14,
						pc01array,
						"3, 36, 37, 500, 512, 513, 531, 565, 8, 801, 802, 809, 811, 812, 814, 835, 837, 838, 842",
						1,
						"0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0260, 0393 ");
		MpanTop.insertMpanTops(dso14, pc01array, "512, 513, 837, 838, 842", 2,
				"393");
		MpanTop.insertMpanTops(dso14, pc01array, "3, 8, 36, 37, 837 ", 3,
				"151, 393 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc02array,
						"1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 21, 22, 24, 26, 38, 39, 59, 500, 511, 522, 523, 524, 532, 533, 534, 538, 539, 540, 809, 811, 812, 814, 864, 865, 890 ",
						4,
						"0013, 0100, 0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0260, 0266, 0315, 0393, 935");
		MpanTop.insertMpanTops(dso14, pc02array, "4, 5, 9, 10, 38, 39, 523 ",
				5, "0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208");
		MpanTop.insertMpanTops(dso14, pc02array, "1, 2, 3, 6, 7, 8, 523 ", 6,
				"0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208");
		MpanTop
				.insertMpanTops(
						dso14,
						pc03array,
						"1, 2, 3, 4, 5, 8, 9, 31, 38, 500, 512, 524, 551, 565, 801, 802, 809, 811, 812, 814, 835, 838, 842, 873 ",
						7,
						"0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0317, 0393");
		MpanTop
				.insertMpanTops(
						dso14,
						pc03array,
						"4, 5, 31, 38, 500, 512, 524, 551, 565, 801, 802, 809, 811, 812, 814, 838, 842 ",
						8,
						"0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0317, 0393 ");
		MpanTop.insertMpanTops(dso14, pc03array,
				"31, 500, 524, 551, 565, 801, 802, 811, 812 ", 9,
				"0151, 0317, 0393 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc04array,
						"21, 23, 26, 58, 511, 524, 532, 533, 536, 537, 538, 540, 541, 809, 811, 812, 814, 874, 890 ",
						10,
						"0015, 0100, 0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0251, 0266, 0314, 0315, 393");
		MpanTop
				.insertMpanTops(
						dso14,
						pc04array,
						"21, 23, 26, 58, 511, 524, 532, 533, 536, 537, 538, 540, 541, 809, 811, 812, 814 ",
						11,
						"0015, 0100, 0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0251, 0266, 0314, 0315, 393");
		MpanTop
				.insertMpanTops(
						dso14,
						pc04array,
						"21, 23, 26, 58, 511, 524, 532, 533, 536, 537, 538, 540, 541, 809, 811, 812 ",
						12,
						"0015, 0100, 0151, 0205, 0206, 0207, 0208, 0251, 0266, 0314, 0315, 0393 ");
		MpanTop.insertMpanTops(dso14, pc03array, "31, 551 ", 13, "317");
		MpanTop.insertMpanTops(dso14, pc03array, "31, 551 ", 14, "317");
		MpanTop.insertMpanTops(dso14, pc03array, "31, 551 ", 15, "317");
		MpanTop
				.insertMpanTops(
						dso14,
						pc05to08array,
						"32, 33, 34, 35, 56, 500, 517, 524, 526, 556, 560, 565, 570, 801, 802, 811, 812, 874",
						20, "0132, 0145, 0151, 0251, 0393, 0440 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc05to08array,
						"32, 33, 34, 35, 56, 500, 517, 524, 526, 556, 560, 565, 570, 801, 802, 811, 812 ",
						21, "0132, 0145, 0151, 0251, 0393, 0440 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc05to08array,
						"32, 33, 34, 35, 56, 500, 517, 524, 526, 556, 560, 565, 570, 801, 802, 811, 812 ",
						22, "0132, 0145, 0151, 0251, 0393, 0440 ");
		MpanTop.insertMpanTops(dso14, pc05to08array, "524, 526, 811, 812 ", 23,
				"151");
		MpanTop
				.insertMpanTops(
						dso14,
						pc05to08array,
						"32, 33, 34, 35, 56, 500, 517, 524, 526, 556, 560, 565, 570, 801, 802, 811, 812 ",
						25, "0132, 0145, 0151, 0251, 0393, 0440 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc05to08array,
						"32, 33, 34, 35, 56, 500, 517, 524, 526, 556, 560, 565, 570, 801, 802, 811, 812 ",
						26, "0132, 0145, 0151, 0251, 0393, 0440 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc05to08array,
						"32, 33, 34, 35, 56, 500, 517, 524, 526, 556, 560, 565, 570, 801, 802, 811, 812 ",
						27, "0132, 0145, 0151, 0251, 0393, 0440 ");
		MpanTop.insertMpanTops(dso14, pc02array, "11", 30, "260");
		MpanTop.insertMpanTops(dso14, pc02array,
				"21, 22, 24, 59, 500, 532, 533, 534, 538 ", 34,
				"0013, 0100, 0266, 393");
		MpanTop.insertMpanTops(dso14, pc02array,
				"21, 22, 24, 59, 532, 533, 534, 538, 539 ", 35,
				"0013, 0100, 0266 ");
		MpanTop.insertMpanTops(dso14, pc02array,
				"21, 22, 24, 59, 532, 533, 534, 538, 539 ", 36,
				"0013, 0100, 0266 ");
		MpanTop.insertMpanTops(dso14, pc04array,
				"21, 23, 26, 511, 524, 532, 533, 536, 537, 541, 811 ", 40,
				"0015, 0151, 0266, 0314, 0315, 0393 ");
		MpanTop.insertMpanTops(dso14, pc04array,
				"21, 23, 532, 533, 536, 537, 540, 541 ", 41,
				"0015, 0266, 0314, 315");
		MpanTop.insertMpanTops(dso14, pc04array, "23, 536, 537, 538, 541 ", 42,
				"0015, 0100, 0314 ");
		MpanTop.insertMpanTops(dso14, pc03array, "512, 838, 842", 46, "393");
		MpanTop.insertMpanTops(dso14, pc03array, "512, 838, 842 ", 47, "393");
		MpanTop.insertMpanTops(dso14, pc03array, "3, 8 ", 49, "151");
		MpanTop.insertMpanTops(dso14, pc08array, "502", 85, "428");
		MpanTop.insertMpanTops(dso14, pc01array, "504", 86, "429");
		MpanTop.insertMpanTops(dso14, pc01array, "505", 87, "430");
		MpanTop.insertMpanTops(dso14, pc01array, "503", 88, "431");
		MpanTop.insertMpanTops(dso14, pc08array, "502", 95, "428");
		MpanTop.insertMpanTops(dso14, pc01array, "504", 96, "429");
		MpanTop.insertMpanTops(dso14, pc01array, "505", 97, "430");
		MpanTop.insertMpanTops(dso14, pc01array, "503", 98, "431");
		MpanTop
				.insertMpanTops(
						dso14,
						pc03array,
						"1, 2, 3, 4, 5, 8, 9, 31, 38, 500, 512, 524, 551, 565, 801, 802, 809, 811, 812, 814, 838, 842",
						107,
						"0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0317, 0393 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc03array,
						"4, 5, 31, 38, 500, 512, 524, 551, 565, 801, 802, 809, 811, 812, 814, 838, 842 ",
						108,
						"0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0317, 0393 ");
		MpanTop.insertMpanTops(dso14, pc03array,
				"31, 500, 524, 551, 565, 801, 802, 811, 812 ", 109,
				"0151, 0317, 0393 ");
		MpanTop
				.insertMpanTops(
						dso14,
						pc04array,
						"21, 23, 26, 58, 511, 524, 532, 533, 536, 537, 538, 540, 541, 809, 811, 812, 814 ",
						110,
						"0015, 0100, 0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0251, 0266, 0314, 0315, 393");
		MpanTop
				.insertMpanTops(
						dso14,
						pc04array,
						"21, 23, 26, 58, 511, 524, 532, 533, 536, 537, 538, 540, 541, 809, 811, 812, 814 ",
						111,
						"0015, 0100, 0151, 0201, 0202, 0203, 0204, 0205, 0206, 0207, 0208, 0251, 0266, 0314, 0315, 393");
		MpanTop
				.insertMpanTops(
						dso14,
						pc04array,
						"21, 23, 26, 58, 511, 524, 532, 533, 536, 537, 538, 540, 541, 809, 811, 812 ",
						112,
						"0015, 0100, 0151, 0205, 0206, 0207, 0208, 0251, 0266, 0314, 0315, 0393 ");
		MpanTop.insertMpanTops(dso14, pc05to08array,
				"33, 34, 524, 526, 811, 812", 322, "0132, 0145, 0151 ");
		MpanTop.insertMpanTops(dso14, pc05to08array,
				"33, 34, 524, 526, 811, 812", 323, "0132, 0145, 0151 ");
		MpanTop.insertMpanTops(dso14, pc06array, "812", 326, "151");

		/*
		 * llf14_623.attachProfileClass(profileClass00);
		 * llf14_623.addMeterTimeswitch("845");
		 * llf14_623.addMeterTimeswitch("846");
		 * llf14_624.attachProfileClass(profileClass00);
		 * llf14_624.addMeterTimeswitch("845");
		 * llf14_624.addMeterTimeswitch("846");
		 * llf14_121.attachProfileClass(profileClass00);
		 * llf14_121.addMeterTimeswitch("845");
		 * llf14_121.addMeterTimeswitch("846");
		 * llf14_124.attachProfileClass(profileClass00);
		 * llf14_124.addMeterTimeswitch("845");
		 * llf14_124.addMeterTimeswitch("846");
		 * llf14_127.attachProfileClass(profileClass00);
		 * llf14_127.addMeterTimeswitch("845");
		 * llf14_127.addMeterTimeswitch("846");
		 * llf14_130.attachProfileClass(profileClass00);
		 * llf14_130.addMeterTimeswitch("845");
		 * llf14_130.addMeterTimeswitch("846");
		 * llf14_132.attachProfileClass(profileClass00);
		 * llf14_132.addMeterTimeswitch("845");
		 * llf14_132.addMeterTimeswitch("846");
		 * llf14_365.attachProfileClass(profileClass00);
		 * llf14_365.addMeterTimeswitch("845");
		 * llf14_365.addMeterTimeswitch("846");
		 * llf14_522.attachProfileClass(profileClass00);
		 * llf14_522.addMeterTimeswitch("845");
		 * llf14_522.addMeterTimeswitch("846");
		 * llf14_627.attachProfileClass(profileClass00);
		 * llf14_627.addMeterTimeswitch("845");
		 * llf14_627.addMeterTimeswitch("846");
		 * llf14_628.attachProfileClass(profileClass00);
		 * llf14_628.addMeterTimeswitch("845");
		 * llf14_628.addMeterTimeswitch("846");
		 * llf20_450.attachProfileClass(profileClass00);
		 * llf20_450.addMeterTimeswitch("845");
		 * llf20_453.attachProfileClass(profileClass00);
		 * llf20_453.addMeterTimeswitch("845");
		 * llf20_520.attachProfileClass(profileClass00);
		 * llf20_520.addMeterTimeswitch("863");
		 * llf20_655.attachProfileClass(profileClass00);
		 * llf20_655.addMeterTimeswitch("845");
		 * llf20_658.attachProfileClass(profileClass00);
		 * llf20_658.addMeterTimeswitch("845");
		 * llf20_909.attachProfileClass(profileClass00);
		 * llf20_909.addMeterTimeswitch("845");
		 * llf20_910.attachProfileClass(profileClass00);
		 * llf20_910.addMeterTimeswitch("845");
		 * llf20_930.attachProfileClass(profileClass00);
		 * llf20_930.addMeterTimeswitch("845");
		 */
/*
		MpanTop.insertMpanTops(dso20, pc01array, "801, 500", 100, "393");
		MpanTop.insertMpanTops(dso20, pc01array, "802, 501", 100, "393");
		MpanTop.insertMpanTops(dso20, pc01array, "801, 500", 101, "393");
		MpanTop.insertMpanTops(dso20, pc01array, "802, 501", 101, "393");
		MpanTop.insertMpanTops(dso20, pc01array, "126", 102, "393");
		MpanTop.insertMpanTops(dso20, pc01array, "835, 623", 102, "393");
		MpanTop.insertMpanTops(dso20, pc02array, "044, 544", 104, "151");
		MpanTop.insertMpanTops(dso20, pc02array, "045, 545", 104, "151");
		MpanTop.insertMpanTops(dso20, pc02array, "050, 550", 104, "167");
		MpanTop.insertMpanTops(dso20, pc02array, "051, 551", 104, "167");
		MpanTop.insertMpanTops(dso20, pc02array, "052, 552", 104, "168");
		MpanTop.insertMpanTops(dso20, pc02array, "053, 553", 104, "168");
		MpanTop.insertMpanTops(dso20, pc02array, "805, 555", 104, "169");
		MpanTop.insertMpanTops(dso20, pc02array, "806, 554", 104,
				"169, 170, 171, 172, 173");
		MpanTop.insertMpanTops(dso20, pc02array, "804, 548", 104, "349");
		MpanTop.insertMpanTops(dso20, pc02array, "803, 547", 104, "349");
		MpanTop.insertMpanTops(dso20, pc02array, "136", 104, "936");
		MpanTop.insertMpanTops(dso20, pc02array, "044, 544", 105, "151");
		MpanTop.insertMpanTops(dso20, pc02array, "045, 545", 105, "151");
		MpanTop.insertMpanTops(dso20, pc02array, "051, 551", 105, "167");
		MpanTop.insertMpanTops(dso20, pc02array, "050, 550", 105, "167");
		MpanTop.insertMpanTops(dso20, pc02array, "052, 552", 105, "168");
		MpanTop.insertMpanTops(dso20, pc02array, "053, 553", 105, "168");
		MpanTop.insertMpanTops(dso20, pc02array, "805, 555", 105, "169");
		MpanTop.insertMpanTops(dso20, pc02array, "806, 554", 105,
				"169, 170, 171, 172, 173");
		MpanTop.insertMpanTops(dso20, pc02array, "804, 548", 105, "349");
		MpanTop.insertMpanTops(dso20, pc02array, "803, 547", 105, "349");
		MpanTop.insertMpanTops(dso20, pc02array, "136", 105, "936");
		MpanTop.insertMpanTops(dso20, pc02array, "046, 546", 106, "151");
		MpanTop.insertMpanTops(dso20, pc02array, "127", 106, "349");
		MpanTop.insertMpanTops(dso20, pc02array, "049, 549", 106, "349");
		MpanTop.insertMpanTops(dso20, pc01array, "586", 108, "300");
		MpanTop.insertMpanTops(dso20, pc01array, "587", 108, "300");
		MpanTop.insertMpanTops(dso20, pc01array, "588", 108, "301");
		MpanTop.insertMpanTops(dso20, pc01array, "589", 108, "301");
		MpanTop.insertMpanTops(dso20, pc01array, "586", 109, "300");
		MpanTop.insertMpanTops(dso20, pc01array, "587", 109, "300");
		MpanTop.insertMpanTops(dso20, pc01array, "588", 109, "301");
		MpanTop.insertMpanTops(dso20, pc01array, "589", 109, "301");
		MpanTop.insertMpanTops(dso20, pc01array, "600", 110, "302");
		MpanTop.insertMpanTops(dso20, pc01array, "601", 110, "302");
		MpanTop.insertMpanTops(dso20, pc01array, "602", 110, "309");
		MpanTop.insertMpanTops(dso20, pc01array, "603", 110, "309");
		MpanTop.insertMpanTops(dso20, pc01array, "600", 111, "302");
		MpanTop.insertMpanTops(dso20, pc01array, "601", 111, "302");
		MpanTop.insertMpanTops(dso20, pc01array, "602", 111, "309");
		MpanTop.insertMpanTops(dso20, pc01array, "603", 111, "309");
		MpanTop.insertMpanTops(dso20, pc02array, "015, 515", 112, "64");
		MpanTop.insertMpanTops(dso20, pc02array, "016, 516", 112, "64");
		MpanTop.insertMpanTops(dso20, pc02array, "017, 517", 112, "65");
		MpanTop.insertMpanTops(dso20, pc02array, "018, 518", 112, "65");
		MpanTop.insertMpanTops(dso20, pc02array, "019, 519", 112, "66");
		MpanTop.insertMpanTops(dso20, pc02array, "020, 520", 112, "66");
		MpanTop.insertMpanTops(dso20, pc02array, "025, 525", 113, "85");
		MpanTop.insertMpanTops(dso20, pc02array, "026, 526", 113, "85");
		MpanTop.insertMpanTops(dso20, pc02array, "027, 527", 113, "86");
		MpanTop.insertMpanTops(dso20, pc02array, "028, 528", 113, "86");
		MpanTop.insertMpanTops(dso20, pc02array, "035, 535", 114, "82");
		MpanTop.insertMpanTops(dso20, pc02array, "036, 536", 114, "82");
		MpanTop.insertMpanTops(dso20, pc02array, "029, 529", 114, "87");
		MpanTop.insertMpanTops(dso20, pc02array, "030, 530", 114, "87");
		MpanTop.insertMpanTops(dso20, pc02array, "033, 533", 114, "91");
		MpanTop.insertMpanTops(dso20, pc02array, "034, 534", 114, "91");
		MpanTop.insertMpanTops(dso20, pc02array, "039, 539", 114, "95");
		MpanTop.insertMpanTops(dso20, pc02array, "040, 540", 114, "95");
		MpanTop.insertMpanTops(dso20, pc02array, "077, 577", 115, "271");
		MpanTop.insertMpanTops(dso20, pc02array, "078, 578", 115, "271");
		MpanTop.insertMpanTops(dso20, pc02array, "079, 579", 115, "272");
		MpanTop.insertMpanTops(dso20, pc02array, "080, 580", 115, "272");
		MpanTop.insertMpanTops(dso20, pc02array, "081, 581", 115, "273");
		MpanTop.insertMpanTops(dso20, pc02array, "082, 582", 115, "273");
		MpanTop.insertMpanTops(dso20, pc02array, "001, 630", 116, "6");
		MpanTop.insertMpanTops(dso20, pc02array, "002, 631", 116, "6");
		MpanTop.insertMpanTops(dso20, pc02array, "007, 636", 116, "9");
		MpanTop.insertMpanTops(dso20, pc02array, "008, 637", 116, "9");
		MpanTop.insertMpanTops(dso20, pc02array, "003, 632", 117, "7");
		MpanTop.insertMpanTops(dso20, pc02array, "004, 633", 117, "7");
		MpanTop.insertMpanTops(dso20, pc02array, "009, 638", 117, "10");
		MpanTop.insertMpanTops(dso20, pc02array, "010, 510", 117, "10");
		MpanTop.insertMpanTops(dso20, pc02array, "011, 511", 117, "11");
		MpanTop.insertMpanTops(dso20, pc02array, "012, 512", 117, "11");
		MpanTop.insertMpanTops(dso20, pc02array, "015, 515", 118, "64");
		MpanTop.insertMpanTops(dso20, pc02array, "016, 516", 118, "64");
		MpanTop.insertMpanTops(dso20, pc02array, "017, 517", 118, "65");
		MpanTop.insertMpanTops(dso20, pc02array, "018, 518", 118, "65");
		MpanTop.insertMpanTops(dso20, pc02array, "019, 519", 118, "66");
		MpanTop.insertMpanTops(dso20, pc02array, "020, 520", 118, "66");
		MpanTop.insertMpanTops(dso20, pc02array, "025, 525", 119, "85");
		MpanTop.insertMpanTops(dso20, pc02array, "026, 526", 119, "85");
		MpanTop.insertMpanTops(dso20, pc02array, "027, 527", 119, "86");
		MpanTop.insertMpanTops(dso20, pc02array, "028, 528", 119, "86");
		MpanTop.insertMpanTops(dso20, pc02array, "035, 535", 120, "82");
		MpanTop.insertMpanTops(dso20, pc02array, "036, 536", 120, "82");
		MpanTop.insertMpanTops(dso20, pc02array, "029, 529", 120, "87");
		MpanTop.insertMpanTops(dso20, pc02array, "030, 530", 120, "87");
		MpanTop.insertMpanTops(dso20, pc02array, "033, 533", 120, "91");
		MpanTop.insertMpanTops(dso20, pc02array, "034, 534", 120, "91");
		MpanTop.insertMpanTops(dso20, pc02array, "039, 539", 120, "95");
		MpanTop.insertMpanTops(dso20, pc02array, "040, 540", 120, "95");
		MpanTop.insertMpanTops(dso20, pc02array, "077, 577", 121, "271");
		MpanTop.insertMpanTops(dso20, pc02array, "078, 578", 121, "271");
		MpanTop.insertMpanTops(dso20, pc02array, "079, 579", 121, "272");
		MpanTop.insertMpanTops(dso20, pc02array, "080, 580", 121, "272");
		MpanTop.insertMpanTops(dso20, pc02array, "081, 581", 121, "273");
		MpanTop.insertMpanTops(dso20, pc02array, "082, 582", 121, "273");
		MpanTop.insertMpanTops(dso20, pc02array, "001, 630", 122, "6");
		MpanTop.insertMpanTops(dso20, pc02array, "002, 631", 122, "6");
		MpanTop.insertMpanTops(dso20, pc02array, "007, 636", 122, "9");
		MpanTop.insertMpanTops(dso20, pc02array, "008, 637", 122, "9");
		MpanTop.insertMpanTops(dso20, pc02array, "003, 632", 123, "7");
		MpanTop.insertMpanTops(dso20, pc02array, "004, 633", 123, "7");
		MpanTop.insertMpanTops(dso20, pc02array, "009, 638", 123, "10");
		MpanTop.insertMpanTops(dso20, pc02array, "010, 510", 123, "10");
		MpanTop.insertMpanTops(dso20, pc02array, "011, 511", 123, "11");
		MpanTop.insertMpanTops(dso20, pc02array, "012, 512", 123, "11");
		MpanTop.insertMpanTops(dso20, pc02array, "071, 571", 124, "261");
		MpanTop.insertMpanTops(dso20, pc02array, "072, 572", 124, "261");
		MpanTop.insertMpanTops(dso20, pc02array, "073, 573", 124, "264");
		MpanTop.insertMpanTops(dso20, pc02array, "074, 574", 124, "264");
		MpanTop.insertMpanTops(dso20, pc02array, "071, 571", 125, "261");
		MpanTop.insertMpanTops(dso20, pc02array, "072, 572", 125, "261");
		MpanTop.insertMpanTops(dso20, pc02array, "073, 573", 125, "264");
		MpanTop.insertMpanTops(dso20, pc02array, "074, 574", 125, "264");
		MpanTop.insertMpanTops(dso20, pc03array, "801, 500", 126, "393");
		MpanTop.insertMpanTops(dso20, pc03array, "801, 500", 127, "393");
		MpanTop.insertMpanTops(dso20, pc03array, "126, 656", 128, "393");
		MpanTop.insertMpanTops(dso20, pc04array, "044, 544", 129, "151");
		MpanTop.insertMpanTops(dso20, pc04array, "045, 545", 129, "151");
		MpanTop.insertMpanTops(dso20, pc04array, "064, 564", 129, "174");
		MpanTop.insertMpanTops(dso20, pc04array, "065, 565", 129, "174");
		MpanTop.insertMpanTops(dso20, pc04array, "874", 129, "242");
		MpanTop.insertMpanTops(dso20, pc04array, "044, 544", 130, "151");
		MpanTop.insertMpanTops(dso20, pc04array, "045, 545", 130, "151");
		MpanTop.insertMpanTops(dso20, pc04array, "064, 564", 130, "174");
		MpanTop.insertMpanTops(dso20, pc04array, "065, 565", 130, "174");
		MpanTop.insertMpanTops(dso20, pc04array, "874", 130, "242");
		MpanTop.insertMpanTops(dso20, pc04array, "46, 546", 131, "151");
		MpanTop.insertMpanTops(dso20, pc03array, "104, 615", 133, "320");
		MpanTop.insertMpanTops(dso20, pc03array, "105, 616", 133, "320");
		MpanTop.insertMpanTops(dso20, pc03array, "106, 617", 133, "322");
		MpanTop.insertMpanTops(dso20, pc03array, "107, 618", 133, "322");
		MpanTop.insertMpanTops(dso20, pc03array, "104, 615", 134, "320");
		MpanTop.insertMpanTops(dso20, pc03array, "105, 616", 134, "320");
		MpanTop.insertMpanTops(dso20, pc03array, "106, 617", 134, "322");
		MpanTop.insertMpanTops(dso20, pc03array, "107, 618", 134, "322");
		MpanTop.insertMpanTops(dso20, pc04array, "111, 622", 135, "326");
		MpanTop.insertMpanTops(dso20, pc04array, "108, 619", 135, "326");
		MpanTop.insertMpanTops(dso20, pc04array, "110, 621", 135, "330");
		MpanTop.insertMpanTops(dso20, pc04array, "109, 620", 135, "330");
		MpanTop.insertMpanTops(dso20, pc04array, "111, 622", 136, "326");
		MpanTop.insertMpanTops(dso20, pc04array, "108, 619", 136, "326");
		MpanTop.insertMpanTops(dso20, pc04array, "110, 621", 136, "330");
		MpanTop.insertMpanTops(dso20, pc04array, "109, 620", 136, "330");
		MpanTop.insertMpanTops(dso20, pc04array, "015, 515", 138, "64");
		MpanTop.insertMpanTops(dso20, pc04array, "017, 517", 138, "65");
		MpanTop.insertMpanTops(dso20, pc04array, "018, 518", 138, "65");
		MpanTop.insertMpanTops(dso20, pc04array, "019, 519", 138, "66");
		MpanTop.insertMpanTops(dso20, pc04array, "020, 520", 138, "66");
		MpanTop.insertMpanTops(dso20, pc04array, "023, 523", 139, "83");
		MpanTop.insertMpanTops(dso20, pc04array, "024, 524", 139, "83");
		MpanTop.insertMpanTops(dso20, pc04array, "031, 531", 139, "88");
		MpanTop.insertMpanTops(dso20, pc04array, "032, 532", 139, "88");
		MpanTop.insertMpanTops(dso20, pc04array, "041, 541", 139, "96");
		MpanTop.insertMpanTops(dso20, pc04array, "042, 542", 139, "96");
		MpanTop.insertMpanTops(dso20, pc04array, "075, 575", 140, "265");
		MpanTop.insertMpanTops(dso20, pc04array, "076, 576", 140, "265");
		MpanTop.insertMpanTops(dso20, pc04array, "083, 583", 140, "274");
		MpanTop.insertMpanTops(dso20, pc04array, "084, 584", 140, "274");
		MpanTop.insertMpanTops(dso20, pc04array, "005, 634", 141, "8");
		MpanTop.insertMpanTops(dso20, pc04array, "006, 635", 141, "8");
		MpanTop.insertMpanTops(dso20, pc04array, "013, 513", 141, "12");
		MpanTop.insertMpanTops(dso20, pc04array, "014, 514", 141, "12");
		MpanTop.insertMpanTops(dso20, pc04array, "015, 515", 142, "64");
		MpanTop.insertMpanTops(dso20, pc04array, "017, 517", 142, "65");
		MpanTop.insertMpanTops(dso20, pc04array, "018, 518", 142, "65");
		MpanTop.insertMpanTops(dso20, pc04array, "019, 519", 142, "66");
		MpanTop.insertMpanTops(dso20, pc04array, "020, 520", 142, "66");
		MpanTop.insertMpanTops(dso20, pc04array, "023, 523", 143, "83");
		MpanTop.insertMpanTops(dso20, pc04array, "024, 524", 143, "83");
		MpanTop.insertMpanTops(dso20, pc04array, "031, 531", 143, "88");
		MpanTop.insertMpanTops(dso20, pc04array, "032, 532", 143, "88");
		MpanTop.insertMpanTops(dso20, pc04array, "041, 541", 143, "96");
		MpanTop.insertMpanTops(dso20, pc04array, "042, 542", 143, "96");
		MpanTop.insertMpanTops(dso20, pc04array, "075, 575", 144, "265");
		MpanTop.insertMpanTops(dso20, pc04array, "076, 576", 144, "265");
		MpanTop.insertMpanTops(dso20, pc04array, "083, 583", 144, "274");
		MpanTop.insertMpanTops(dso20, pc04array, "084, 584", 144, "274");
		MpanTop.insertMpanTops(dso20, pc04array, "005, 634", 145, "8");
		MpanTop.insertMpanTops(dso20, pc04array, "006, 635", 145, "8");
		MpanTop.insertMpanTops(dso20, pc04array, "013, 513", 145, "12");
		MpanTop.insertMpanTops(dso20, pc04array, "014, 514", 145, "12");
		MpanTop.insertMpanTops(dso20, pc02array, "604", 150, "351");
		MpanTop.insertMpanTops(dso20, pc02array, "605", 150, "351");
		MpanTop.insertMpanTops(dso20, pc02array, "606", 150, "352");
		MpanTop.insertMpanTops(dso20, pc02array, "607", 150, "352");
		MpanTop.insertMpanTops(dso20, pc02array, "604", 151, "351");
		MpanTop.insertMpanTops(dso20, pc02array, "605", 151, "351");
		MpanTop.insertMpanTops(dso20, pc02array, "606", 151, "352");
		MpanTop.insertMpanTops(dso20, pc02array, "607", 151, "352");
		MpanTop.insertMpanTops(dso20, pc02array, "608", 152, "353");
		MpanTop.insertMpanTops(dso20, pc02array, "609", 152, "353");
		MpanTop.insertMpanTops(dso20, pc02array, "610", 152, "425");
		MpanTop.insertMpanTops(dso20, pc02array, "611", 152, "425");
		MpanTop.insertMpanTops(dso20, pc02array, "608", 153, "353");
		MpanTop.insertMpanTops(dso20, pc02array, "609", 153, "353");
		MpanTop.insertMpanTops(dso20, pc02array, "610", 153, "425");
		MpanTop.insertMpanTops(dso20, pc02array, "611", 153, "425");
		MpanTop.insertMpanTops(dso20, pc01array, "128", 154, "320");
		MpanTop.insertMpanTops(dso20, pc01array, "129", 154, "320");
		MpanTop.insertMpanTops(dso20, pc01array, "130", 154, "322");
		MpanTop.insertMpanTops(dso20, pc01array, "131", 154, "322");
		MpanTop.insertMpanTops(dso20, pc01array, "137", 154, "443");
		MpanTop.insertMpanTops(dso20, pc01array, "128", 155, "320");
		MpanTop.insertMpanTops(dso20, pc01array, "129", 155, "320");
		MpanTop.insertMpanTops(dso20, pc01array, "130", 155, "322");
		MpanTop.insertMpanTops(dso20, pc01array, "131", 155, "322");
		MpanTop.insertMpanTops(dso20, pc01array, "137", 155, "443");
		MpanTop.insertMpanTops(dso20, pc02array, "132", 156, "326");
		MpanTop.insertMpanTops(dso20, pc02array, "133", 156, "326");
		MpanTop.insertMpanTops(dso20, pc02array, "134", 156, "330");
		MpanTop.insertMpanTops(dso20, pc02array, "135", 156, "330");
		MpanTop.insertMpanTops(dso20, pc02array, "132", 157, "326");
		MpanTop.insertMpanTops(dso20, pc02array, "133", 157, "326");
		MpanTop.insertMpanTops(dso20, pc02array, "134", 157, "330");
		MpanTop.insertMpanTops(dso20, pc02array, "135", 157, "330");
		MpanTop.insertMpanTops(dso20, pc05to08array, "801, 501", 400, "393");
		MpanTop.insertMpanTops(dso20, pc05to08array, "802, 500", 400, "393");
		MpanTop.insertMpanTops(dso20, pc05to08array, "873", 400, "393");
		MpanTop.insertMpanTops(dso20, pc05to08array, "66, 566", 401, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "67, 567", 401, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "810", 401, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "809", 401, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "874", 401, "242");
		MpanTop.insertMpanTops(dso20, pc05to08array, "808, 568", 401, "244");
		MpanTop.insertMpanTops(dso20, pc05to08array, "807, 569", 401, "244");
		MpanTop.insertMpanTops(dso20, pc05to08array, "43, 543", 401, "146");
		MpanTop.insertMpanTops(dso20, pc05to08array, "801, 501", 605, "393");
		MpanTop.insertMpanTops(dso20, pc05to08array, "802, 500", 605, "393");
		MpanTop.insertMpanTops(dso20, pc05to08array, "66, 566", 606, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "67, 567", 606, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "810", 606, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "809", 606, "175");
		MpanTop.insertMpanTops(dso20, pc05to08array, "808, 568", 606, "244");
		MpanTop.insertMpanTops(dso20, pc05to08array, "807, 569", 606, "244");
		MpanTop.insertMpanTops(dso20, pc05to08array, "43, 543", 606, "146");
		MpanTop.insertMpanTops(dso20, pc08array, "857, 502", 500, "428");
		MpanTop.insertMpanTops(dso20, pc01array, "859, 504", 501, "429");
		MpanTop.insertMpanTops(dso20, pc01array, "860, 505", 502, "430");
		MpanTop.insertMpanTops(dso20, pc01array, "858, 503", 503, "431");
		MpanTop.insertMpanTops(dso20, pc08array, "502", 510, "428");
		MpanTop.insertMpanTops(dso20, pc01array, "504", 511, "429");
		MpanTop.insertMpanTops(dso20, pc01array, "505", 512, "430");
		MpanTop.insertMpanTops(dso20, pc01array, "503", 513, "431");
		MpanTop.insertMpanTops(dso20, pc02array, "085, 585", 504, "299");
		MpanTop.insertMpanTops(dso20, pc02array, "091, 591", 504, "303");
		MpanTop.insertMpanTops(dso20, pc02array, "092, 592", 504, "304");
		MpanTop.insertMpanTops(dso20, pc00array, "863", 520, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "070, 570", 450, "9999");
		MpanTop.insertMpanTops(dso20, pc00array, "070, 570", 453, "9999");
		MpanTop.insertMpanTops(dso20, pc00array, "070, 570", 655, "9999");
		MpanTop.insertMpanTops(dso20, pc00array, "070, 570", 658, "9999");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 700, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 701, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 702, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 703, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 705, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 706, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 707, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 708, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 709, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 710, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 800, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 801, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 802, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 803, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 804, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 805, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 806, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 807, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 808, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 809, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 810, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 811, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 812, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 813, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 814, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 815, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 816, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 817, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 818, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 819, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 820, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 821, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 822, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 823, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 824, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 825, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 826, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 827, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 828, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 829, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 830, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 831, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 832, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 833, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 834, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 835, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 836, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 837, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 838, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 839, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 840, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 841, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 842, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 843, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 844, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 845, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 846, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 847, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 900, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 901, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 902, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 903, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 904, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 905, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 906, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 907, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 908, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 909, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 910, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 911, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 912, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 913, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 914, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 915, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 916, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 917, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 918, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 919, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 920, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 921, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 922, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 923, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 924, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 925, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 926, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 927, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 928, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "862", 929, " 0000");
		MpanTop.insertMpanTops(dso20, pc00array, "845, 846", 909, "0000");
		MpanTop.insertMpanTops(dso20, pc00array, "845, 846", 910, "0000");
		MpanTop.insertMpanTops(dso20, pc00array, "845", 930, "0000");
		MpanTop.insertMpanTops(dso20, pc08array, "867, 870", 931,
				"484, 485, 486, 487, 488, 489");
		MpanTop.insertMpanTops(dso20, pc08array, "380", 931, "484");
		MpanTop.insertMpanTops(dso20, pc08array, "381", 931, "485");
		MpanTop.insertMpanTops(dso20, pc08array, "382", 931, "486");
		MpanTop.insertMpanTops(dso20, pc08array, "383", 931, "487");
		MpanTop.insertMpanTops(dso20, pc08array, "384", 931, "488");
		MpanTop.insertMpanTops(dso20, pc08array, "385", 931, "489");
		MpanTop.insertMpanTops(dso20, pc08array, "388", 931, "492");
		MpanTop.insertMpanTops(dso20, pc08array, "389", 931, "493");
		MpanTop.insertMpanTops(dso20, pc08array, "390", 931,
				"494, 495, 496, 497");
		MpanTop.insertMpanTops(dso20, pc08array, "391", 931, "495");
		MpanTop.insertMpanTops(dso20, pc08array, "392", 931, "496");
		MpanTop.insertMpanTops(dso20, pc08array, "393", 931, "497");
		MpanTop.insertMpanTops(dso20, pc08array, "394", 931, "498");
		MpanTop.insertMpanTops(dso20, pc08array, "397", 931, "940");
		MpanTop.insertMpanTops(dso20, pc08array, "398", 931, "941");
		MpanTop.insertMpanTops(dso20, pc08array, "866", 931,
				"490, 491, 492, 493, 494, 495, 496, 497");
		MpanTop.insertMpanTops(dso20, pc08array, "868", 931, "941, 498");
		MpanTop.insertMpanTops(dso20, pc08array, "869", 931, "492, 493");
		MpanTop.insertMpanTops(dso20, pc08array, "871", 931, "498, 941");
		MpanTop.insertMpanTops(dso20, pc08array, "378", 932, "482");
		MpanTop.insertMpanTops(dso20, pc08array, "379", 932, "483");
		MpanTop.insertMpanTops(dso20, pc08array, "380", 932, "484");
		MpanTop.insertMpanTops(dso20, pc08array, "381", 932, "485");
		MpanTop.insertMpanTops(dso20, pc08array, "386", 932, "490");
		MpanTop.insertMpanTops(dso20, pc08array, "387", 932, "491");
		MpanTop.insertMpanTops(dso20, pc08array, "388", 932, "492");
		MpanTop.insertMpanTops(dso20, pc08array, "389", 932, "493");
		MpanTop.insertMpanTops(dso20, pc08array, "394", 932, "498");
		MpanTop.insertMpanTops(dso20, pc08array, "397", 932, "940");
		MpanTop.insertMpanTops(dso20, pc08array, "398", 932, "941");
		MpanTop.insertMpanTops(dso20, pc08array, "868", 932,
				"940, 941, 498, 940");
		MpanTop.insertMpanTops(dso20, pc08array, "869", 932, "490, 491, 492");
		MpanTop.insertMpanTops(dso20, pc08array, "871", 932, "498, 940, 941");
		MpanTop.insertMpanTops(dso20, pc08array, "867, 870", 932,
				"482, 483, 484, 485");

		/*
		 * * llf20_931 .addMeterTimeswitches("867, 380, 870, 380, 867, 381, 870,
		 * 381, 867, 382, 870, 382, 867, 383, 870, 383, 867, 384, 870, 384, 867,
		 * 385, 870, 385, 866, 388, 869, 388, 866, 389, 869, 389, 866, 390, 869,
		 * 390, 866, 391, 869, 392, 393, 868, 394, 871, 397, 871, 398");
		 * llf20_932.attachProfileClass(pc08); llf20_932
		 * .addMeterTimeswitches("867, 378, 870, 379, 380, 381, 866, 386, 869,
		 * 866, 387, 388, 389, 868, 394, 871, 397, 868, 398");
		 * 
		 * llf22_510.attachProfileClass(profileClass00);
		 * llf22_510.addMeterTimeswitch("845");
		 * llf22_510.addMeterTimeswitch("846");
		 * llf22_510.addMeterTimeswitch("847");
		 * llf22_510.addMeterTimeswitch("848");
		 * llf22_510.addMeterTimeswitch("849");
		 * llf22_510.addMeterTimeswitch("850");
		 * llf22_510.addMeterTimeswitch("851");
		 * llf22_510.addMeterTimeswitch("852");
		 * llf22_510.addMeterTimeswitch("853");
		 * llf22_510.addMeterTimeswitch("854");
		 * llf22_510.addMeterTimeswitch("855");
		 * llf22_510.addMeterTimeswitch("856");
		 * llf22_520.attachProfileClass(profileClass00);
		 * llf22_520.addMeterTimeswitch("845");
		 * llf22_520.addMeterTimeswitch("846");
		 * llf22_520.addMeterTimeswitch("847");
		 * llf22_520.addMeterTimeswitch("848");
		 * llf22_520.addMeterTimeswitch("849");
		 * llf22_520.addMeterTimeswitch("850");
		 * llf22_520.addMeterTimeswitch("851");
		 * llf22_520.addMeterTimeswitch("852");
		 * llf22_520.addMeterTimeswitch("853");
		 * llf22_520.addMeterTimeswitch("854");
		 * llf22_520.addMeterTimeswitch("855");
		 * llf22_520.addMeterTimeswitch("856");
		 * llf22_521.attachProfileClass(profileClass00);
		 * llf22_521.addMeterTimeswitch("845");
		 * llf22_521.addMeterTimeswitch("846");
		 * llf22_521.addMeterTimeswitch("847");
		 * llf22_521.addMeterTimeswitch("848");
		 * llf22_521.addMeterTimeswitch("849");
		 * llf22_521.addMeterTimeswitch("850");
		 * llf22_521.addMeterTimeswitch("851");
		 * llf22_521.addMeterTimeswitch("852");
		 * llf22_521.addMeterTimeswitch("853");
		 * llf22_521.addMeterTimeswitch("854");
		 * llf22_521.addMeterTimeswitch("855");
		 * llf22_521.addMeterTimeswitch("856");
		 * llf22_540.attachProfileClass(profileClass00);
		 * llf22_540.addMeterTimeswitch("845");
		 * llf22_540.addMeterTimeswitch("846");
		 * llf22_540.addMeterTimeswitch("847");
		 * llf22_540.addMeterTimeswitch("848");
		 * llf22_540.addMeterTimeswitch("849");
		 * llf22_540.addMeterTimeswitch("850");
		 * llf22_540.addMeterTimeswitch("851");
		 * llf22_540.addMeterTimeswitch("852");
		 * llf22_540.addMeterTimeswitch("853");
		 * llf22_540.addMeterTimeswitch("854");
		 * llf22_540.addMeterTimeswitch("855");
		 * llf22_540.addMeterTimeswitch("856");
		 * llf22_550.attachProfileClass(profileClass00);
		 * llf22_550.addMeterTimeswitch("845");
		 * llf22_550.addMeterTimeswitch("846");
		 * llf22_550.addMeterTimeswitch("847");
		 * llf22_550.addMeterTimeswitch("848");
		 * llf22_550.addMeterTimeswitch("849");
		 * llf22_550.addMeterTimeswitch("850");
		 * llf22_550.addMeterTimeswitch("851");
		 * llf22_550.addMeterTimeswitch("852");
		 * llf22_550.addMeterTimeswitch("853");
		 * llf22_550.addMeterTimeswitch("854");
		 * llf22_550.addMeterTimeswitch("855");
		 * llf22_550.addMeterTimeswitch("856");
		 * llf22_551.attachProfileClass(profileClass00);
		 * llf22_551.addMeterTimeswitch("845");
		 * llf22_551.addMeterTimeswitch("846");
		 * llf22_551.addMeterTimeswitch("847");
		 * llf22_551.addMeterTimeswitch("848");
		 * llf22_551.addMeterTimeswitch("849");
		 * llf22_551.addMeterTimeswitch("850");
		 * llf22_551.addMeterTimeswitch("851");
		 * llf22_551.addMeterTimeswitch("852");
		 * llf22_551.addMeterTimeswitch("853");
		 * llf22_551.addMeterTimeswitch("854");
		 * llf22_551.addMeterTimeswitch("855");
		 * llf22_551.addMeterTimeswitch("856");
		 * llf22_570.attachProfileClass(profileClass00);
		 * llf22_570.addMeterTimeswitch("845");
		 * llf22_570.addMeterTimeswitch("846");
		 * llf22_570.addMeterTimeswitch("847");
		 * llf22_570.addMeterTimeswitch("848");
		 * llf22_570.addMeterTimeswitch("849");
		 * llf22_570.addMeterTimeswitch("850");
		 * llf22_570.addMeterTimeswitch("851");
		 * llf22_570.addMeterTimeswitch("852");
		 * llf22_570.addMeterTimeswitch("853");
		 * llf22_570.addMeterTimeswitch("854");
		 * llf22_570.addMeterTimeswitch("855");
		 * llf22_570.addMeterTimeswitch("856");
		 * llf22_580.attachProfileClass(profileClass00);
		 * llf22_580.addMeterTimeswitch("845");
		 * llf22_580.addMeterTimeswitch("846");
		 * llf22_580.addMeterTimeswitch("847");
		 * llf22_580.addMeterTimeswitch("848");
		 * llf22_580.addMeterTimeswitch("849");
		 * llf22_580.addMeterTimeswitch("850");
		 * llf22_580.addMeterTimeswitch("851");
		 * llf22_580.addMeterTimeswitch("852");
		 * llf22_580.addMeterTimeswitch("853");
		 * llf22_580.addMeterTimeswitch("854");
		 * llf22_580.addMeterTimeswitch("855");
		 * llf22_580.addMeterTimeswitch("856");
		 * llf22_581.attachProfileClass(profileClass00);
		 * llf22_581.addMeterTimeswitch("845");
		 * llf22_581.addMeterTimeswitch("846");
		 * llf22_581.addMeterTimeswitch("847");
		 * llf22_581.addMeterTimeswitch("848");
		 * llf22_581.addMeterTimeswitch("849");
		 * llf22_581.addMeterTimeswitch("850");
		 * llf22_581.addMeterTimeswitch("851");
		 * llf22_581.addMeterTimeswitch("852");
		 * llf22_581.addMeterTimeswitch("853");
		 * llf22_581.addMeterTimeswitch("854");
		 * llf22_581.addMeterTimeswitch("855");
		 * llf22_581.addMeterTimeswitch("856");
		 * llf98_000.attachProfileClass(profileClass00);
		 * llf98_000.addMeterTimeswitch("845");
		 * llf98_001.attachProfileClass(profileClass00);
		 * llf98_001.addMeterTimeswitch("845");
		 * llf98_002.attachProfileClass(profileClass00);
		 * llf98_002.addMeterTimeswitch("845");
		 * llf98_003.attachProfileClass(profileClass00);
		 * llf98_003.addMeterTimeswitch("845");
		 * llf98_004.attachProfileClass(profileClass00);
		 * llf98_004.addMeterTimeswitch("845");
		 * llf98_005.attachProfileClass(profileClass00);
		 * llf98_005.addMeterTimeswitch("845");
		 * llf98_006.attachProfileClass(profileClass00);
		 * llf98_006.addMeterTimeswitch("845");
		 * llf98_007.attachProfileClass(profileClass00);
		 * llf98_007.addMeterTimeswitch("845");
		 */
		
	/*
		MpanTop.insertMpanTops(dso22, pc01array, "500", 10, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "501", 10, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "801", 10, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "802", 10, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "587", 20, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "835", 20, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "500", 870, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "501", 870, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "801", 870, "393");
		MpanTop.insertMpanTops(dso22, pc01array, "802", 870, "393");
		MpanTop.insertMpanTops(dso22, pc02array, "536", 30, "128");
		MpanTop.insertMpanTops(dso22, pc02array, "48", 30, "148");
		MpanTop.insertMpanTops(dso22, pc02array, "585", 30, "148");
		MpanTop.insertMpanTops(dso22, pc02array, "31", 30, "176");
		MpanTop.insertMpanTops(dso22, pc02array, "541", 30, "176");
		MpanTop.insertMpanTops(dso22, pc02array, "32", 30, "177");
		MpanTop.insertMpanTops(dso22, pc02array, "542", 30, "177");
		MpanTop.insertMpanTops(dso22, pc02array, "33", 30, "178");
		MpanTop.insertMpanTops(dso22, pc02array, "543", 30, "178");
		MpanTop.insertMpanTops(dso22, pc02array, "34", 30, "179");
		MpanTop.insertMpanTops(dso22, pc02array, "544", 30, "179");
		MpanTop.insertMpanTops(dso22, pc02array, "35", 30, "180");
		MpanTop.insertMpanTops(dso22, pc02array, "545", 30, "180");
		MpanTop.insertMpanTops(dso22, pc02array, "36", 30, "181");
		MpanTop.insertMpanTops(dso22, pc02array, "546", 30, "181");
		MpanTop.insertMpanTops(dso22, pc02array, "37", 30, "182");
		MpanTop.insertMpanTops(dso22, pc02array, "547", 30, "182");
		MpanTop.insertMpanTops(dso22, pc02array, "38", 30, "183");
		MpanTop.insertMpanTops(dso22, pc02array, "548", 30, "183");
		MpanTop.insertMpanTops(dso22, pc02array, "39", 30, "184");
		MpanTop.insertMpanTops(dso22, pc02array, "549", 30, "184");
		MpanTop.insertMpanTops(dso22, pc02array, "40", 30, "185");
		MpanTop.insertMpanTops(dso22, pc02array, "550", 30, "185");
		MpanTop.insertMpanTops(dso22, pc02array, "41", 30, "186");
		MpanTop.insertMpanTops(dso22, pc02array, "551", 30, "186");
		MpanTop.insertMpanTops(dso22, pc02array, "573, 580, 807, 808", 30,
				"244");
		MpanTop.insertMpanTops(dso22, pc02array, "574, 581, 818, 819", 30,
				"251");
		MpanTop.insertMpanTops(dso22, pc02array, "43, 553", 30, "252");
		MpanTop.insertMpanTops(dso22, pc02array, "52,586", 30, "312");
		MpanTop.insertMpanTops(dso22, pc02array, "557", 30, "334");
		MpanTop.insertMpanTops(dso22, pc02array, "537", 30, "342");
		MpanTop.insertMpanTops(dso22, pc02array, "558", 30, "343");
		MpanTop.insertMpanTops(dso22, pc02array, "47, 584", 30, "432");
		MpanTop.insertMpanTops(dso22, pc02array, "53,57,565,569", 30, "435");
		MpanTop.insertMpanTops(dso22, pc02array, "54,58,566,570", 30, "436");
		MpanTop.insertMpanTops(dso22, pc02array, "74, 599", 30, "447");
		MpanTop.insertMpanTops(dso22, pc02array, "63, 588", 30, "448");
		MpanTop.insertMpanTops(dso22, pc02array, "64, 589", 30, "449");
		MpanTop.insertMpanTops(dso22, pc02array, "65, 590", 30, "450");
		MpanTop.insertMpanTops(dso22, pc02array, "66, 591", 30, "451");
		MpanTop.insertMpanTops(dso22, pc02array, "67, 592", 30, "452");
		MpanTop.insertMpanTops(dso22, pc02array, "68, 593", 30, "453");
		MpanTop.insertMpanTops(dso22, pc02array, "69, 594", 30, "454");
		MpanTop.insertMpanTops(dso22, pc02array, "70, 595", 30, "455");
		MpanTop.insertMpanTops(dso22, pc02array, "71, 596", 30, "456");
		MpanTop.insertMpanTops(dso22, pc02array, "72, 597", 30, "459");
		MpanTop.insertMpanTops(dso22, pc02array, "42, 552", 40, "244");
		MpanTop.insertMpanTops(dso22, pc02array, "536", 50, "128");
		MpanTop.insertMpanTops(dso22, pc02array, "54,58,566,570", 50, "436");
		MpanTop.insertMpanTops(dso22, pc02array, "537", 51, "342");
		MpanTop.insertMpanTops(dso22, pc02array, "557", 60, "334");
		MpanTop.insertMpanTops(dso22, pc02array, "53,57,565,569", 60, "435");
		MpanTop.insertMpanTops(dso22, pc02array, "558", 61, "343");
		MpanTop.insertMpanTops(dso22, pc02array, "48, 585", 430, "148");
		MpanTop.insertMpanTops(dso22, pc02array, "574, 581, 818, 819", 430,
				"251");
		MpanTop.insertMpanTops(dso22, pc02array, "43, 553", 430, "252");
		MpanTop.insertMpanTops(dso22, pc02array, "52, 586", 430, "312");
		MpanTop.insertMpanTops(dso22, pc02array, "74, 599", 430, "447");
		MpanTop.insertMpanTops(dso22, pc02array, "63, 588", 430, "448");
		MpanTop.insertMpanTops(dso22, pc02array, "64, 589", 430, "449");
		MpanTop.insertMpanTops(dso22, pc02array, "65, 590", 430, "450");
		MpanTop.insertMpanTops(dso22, pc02array, "66, 591", 430, "451");
		MpanTop.insertMpanTops(dso22, pc02array, "67, 592", 430, "452");
		MpanTop.insertMpanTops(dso22, pc02array, "68, 593", 430, "453");
		MpanTop.insertMpanTops(dso22, pc02array, "69, 594", 430, "454");
		MpanTop.insertMpanTops(dso22, pc02array, "70, 595", 430, "455");
		MpanTop.insertMpanTops(dso22, pc02array, "71, 596", 430, "456");
		MpanTop.insertMpanTops(dso22, pc02array, "72, 597", 430, "459");
		MpanTop.insertMpanTops(dso22, pc02array, "48, 585", 435, "148");
		MpanTop.insertMpanTops(dso22, pc02array, "574, 581, 818, 819", 435,
				"251");
		MpanTop.insertMpanTops(dso22, pc02array, "43, 553", 435, "252");
		MpanTop.insertMpanTops(dso22, pc02array, "52, 586", 435, "312");
		MpanTop.insertMpanTops(dso22, pc02array, "74, 599", 435, "447");
		MpanTop.insertMpanTops(dso22, pc02array, "63, 588", 435, "448");
		MpanTop.insertMpanTops(dso22, pc02array, "64, 589", 435, "449");
		MpanTop.insertMpanTops(dso22, pc02array, "65, 590", 435, "450");
		MpanTop.insertMpanTops(dso22, pc02array, "66, 591", 435, "451");
		MpanTop.insertMpanTops(dso22, pc02array, "67, 592", 435, "452");
		MpanTop.insertMpanTops(dso22, pc02array, "68, 593", 435, "453");
		MpanTop.insertMpanTops(dso22, pc02array, "69, 594", 435, "454");
		MpanTop.insertMpanTops(dso22, pc02array, "70, 595", 435, "455");
		MpanTop.insertMpanTops(dso22, pc02array, "71, 596", 435, "456");
		MpanTop.insertMpanTops(dso22, pc02array, "72, 597", 435, "459");
		MpanTop.insertMpanTops(dso22, pc02array, "31, 541", 850, "176");
		MpanTop.insertMpanTops(dso22, pc02array, "32, 542", 850, "177");
		MpanTop.insertMpanTops(dso22, pc02array, "33, 543", 850, "178");
		MpanTop.insertMpanTops(dso22, pc02array, "34, 544", 850, "179");
		MpanTop.insertMpanTops(dso22, pc02array, "35, 545", 850, "180");
		MpanTop.insertMpanTops(dso22, pc02array, "36, 546", 850, "181");
		MpanTop.insertMpanTops(dso22, pc02array, "37, 547", 850, "182");
		MpanTop.insertMpanTops(dso22, pc02array, "38, 548", 850, "183");
		MpanTop.insertMpanTops(dso22, pc02array, "39, 549", 850, "184");
		MpanTop.insertMpanTops(dso22, pc02array, "40, 550", 850, "185");
		MpanTop.insertMpanTops(dso22, pc02array, "41, 551", 850, "186");
		MpanTop.insertMpanTops(dso22, pc02array, "573, 580, 807, 808", 850,
				"244");
		MpanTop.insertMpanTops(dso22, pc02array, "47, 584", 850, "432");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 110,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "587, 835", 120, "393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 130,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "587, 835", 140, "393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 310,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 320,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 460,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 470,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 480,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 860,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 890,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 900,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 910,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 920,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 930,
				"393");
		MpanTop.insertMpanTops(dso22, pc03array, "500, 501, 801, 802", 950,
				"393");
		MpanTop.insertMpanTops(dso22, pc04array, "536", 210, "128");
		MpanTop.insertMpanTops(dso22, pc04array, "48, 585", 210, "148");
		MpanTop.insertMpanTops(dso22, pc04array, "564, 579, 803, 804", 210,
				"154");
		MpanTop.insertMpanTops(dso22, pc04array, "31, 541", 210, "176");
		MpanTop.insertMpanTops(dso22, pc04array, "32, 542", 210, "177");
		MpanTop.insertMpanTops(dso22, pc04array, "33, 543", 210, "178");
		MpanTop.insertMpanTops(dso22, pc04array, "34, 544", 210, "179");
		MpanTop.insertMpanTops(dso22, pc04array, "35, 545", 210, "180");
		MpanTop.insertMpanTops(dso22, pc04array, "36, 546", 210, "181");
		MpanTop.insertMpanTops(dso22, pc04array, "37, 547", 210, "182");
		MpanTop.insertMpanTops(dso22, pc04array, "38, 548", 210, "183");
		MpanTop.insertMpanTops(dso22, pc04array, "39, 549", 210, "184");
		MpanTop.insertMpanTops(dso22, pc04array, "40, 550", 210, "185");
		MpanTop.insertMpanTops(dso22, pc04array, "41, 551", 210, "186");
		MpanTop.insertMpanTops(dso22, pc04array, "573, 580, 807, 808", 210,
				"244");
		MpanTop.insertMpanTops(dso22, pc04array, "56,60,568,572", 210, "246");
		MpanTop.insertMpanTops(dso22, pc04array, "574, 581, 818, 819", 210,
				"251");
		MpanTop.insertMpanTops(dso22, pc04array, "43, 553", 210, "252");
		MpanTop.insertMpanTops(dso22, pc04array, "52, 586", 210, "312");
		MpanTop.insertMpanTops(dso22, pc04array, "537", 210, "342");
		MpanTop.insertMpanTops(dso22, pc04array, "562", 210, "344");
		MpanTop.insertMpanTops(dso22, pc04array, "563", 210, "345");
		MpanTop.insertMpanTops(dso22, pc04array, "47, 584", 210, "432");
		MpanTop.insertMpanTops(dso22, pc04array, "54,58,566,570", 210, "436");
		MpanTop.insertMpanTops(dso22, pc04array, "74, 599", 210, "447");
		MpanTop.insertMpanTops(dso22, pc04array, "63, 588", 210, "448");
		MpanTop.insertMpanTops(dso22, pc04array, "64, 589", 210, "449");
		MpanTop.insertMpanTops(dso22, pc04array, "65, 590", 210, "450");
		MpanTop.insertMpanTops(dso22, pc04array, "66, 591", 210, "451");
		MpanTop.insertMpanTops(dso22, pc04array, "67, 592", 210, "452");
		MpanTop.insertMpanTops(dso22, pc04array, "68, 593", 210, "453");
		MpanTop.insertMpanTops(dso22, pc04array, "69, 594", 210, "454");
		MpanTop.insertMpanTops(dso22, pc04array, "70, 595", 210, "455");
		MpanTop.insertMpanTops(dso22, pc04array, "71, 596", 210, "456");
		MpanTop.insertMpanTops(dso22, pc04array, "72, 597", 210, "459");
		MpanTop.insertMpanTops(dso22, pc04array, "42, 552", 220, "244");
		MpanTop.insertMpanTops(dso22, pc04array, "564, 579, 803, 804", 230,
				"154");
		MpanTop.insertMpanTops(dso22, pc04array, "31, 541", 230, "176");
		MpanTop.insertMpanTops(dso22, pc04array, "32, 542", 230, "177");
		MpanTop.insertMpanTops(dso22, pc04array, "33, 543", 230, "178");
		MpanTop.insertMpanTops(dso22, pc04array, "34, 544", 230, "179");
		MpanTop.insertMpanTops(dso22, pc04array, "35, 545", 230, "180");
		MpanTop.insertMpanTops(dso22, pc04array, "36, 546", 230, "181");
		MpanTop.insertMpanTops(dso22, pc04array, "37, 547", 230, "182");
		MpanTop.insertMpanTops(dso22, pc04array, "38, 548", 230, "183");
		MpanTop.insertMpanTops(dso22, pc04array, "39, 549", 230, "184");
		MpanTop.insertMpanTops(dso22, pc04array, "40, 550", 230, "185");
		MpanTop.insertMpanTops(dso22, pc04array, "41, 551", 230, "186");
		MpanTop.insertMpanTops(dso22, pc04array, "573, 580, 807, 808", 230,
				"244");
		MpanTop.insertMpanTops(dso22, pc04array, "47, 584", 230, "432");
		MpanTop.insertMpanTops(dso22, pc04array, "42, 552", 240, "244");
		MpanTop.insertMpanTops(dso22, pc04array, "536", 250, "128");
		MpanTop.insertMpanTops(dso22, pc04array, "54,58,566,570", 250, "436");
		MpanTop.insertMpanTops(dso22, pc04array, "537", 251, "342");
		MpanTop.insertMpanTops(dso22, pc04array, "536", 260, "128");
		MpanTop.insertMpanTops(dso22, pc04array, "54,58,566,570", 260, "436");
		MpanTop.insertMpanTops(dso22, pc04array, "537", 261, "342");
		MpanTop.insertMpanTops(dso22, pc04array, "56,60,568,572", 280, "246");
		MpanTop.insertMpanTops(dso22, pc04array, "562", 280, "344");
		MpanTop.insertMpanTops(dso22, pc04array, "563", 281, "345");
		MpanTop.insertMpanTops(dso22, pc04array, "564, 579, 803, 804", 330,
				"154");
		MpanTop.insertMpanTops(dso22, pc04array, "31, 541", 330, "176");
		MpanTop.insertMpanTops(dso22, pc04array, "32, 542", 330, "177");
		MpanTop.insertMpanTops(dso22, pc04array, "33, 543", 330, "178");
		MpanTop.insertMpanTops(dso22, pc04array, "34, 544", 330, "179");
		MpanTop.insertMpanTops(dso22, pc04array, "35, 545", 330, "180");
		MpanTop.insertMpanTops(dso22, pc04array, "36, 546", 330, "181");
		MpanTop.insertMpanTops(dso22, pc04array, "37, 547", 330, "182");
		MpanTop.insertMpanTops(dso22, pc04array, "38, 548", 330, "183");
		MpanTop.insertMpanTops(dso22, pc04array, "39, 549", 330, "184");
		MpanTop.insertMpanTops(dso22, pc04array, "40, 550", 330, "185");
		MpanTop.insertMpanTops(dso22, pc04array, "41, 551", 330, "186");
		MpanTop.insertMpanTops(dso22, pc04array, "573, 580, 807, 808", 330,
				"244");
		MpanTop.insertMpanTops(dso22, pc04array, "47, 584", 330, "432");
		MpanTop.insertMpanTops(dso22, pc04array, "564, 579, 803, 804", 340,
				"154");
		MpanTop.insertMpanTops(dso22, pc04array, "31, 541", 340, "176");
		MpanTop.insertMpanTops(dso22, pc04array, "32, 542", 340, "177");
		MpanTop.insertMpanTops(dso22, pc04array, "33, 543", 340, "178");
		MpanTop.insertMpanTops(dso22, pc04array, "34, 544", 340, "179");
		MpanTop.insertMpanTops(dso22, pc04array, "35, 545", 340, "180");
		MpanTop.insertMpanTops(dso22, pc04array, "36, 546", 340, "181");
		MpanTop.insertMpanTops(dso22, pc04array, "37, 547", 340, "182");
		MpanTop.insertMpanTops(dso22, pc04array, "38,", 340, "183");
		MpanTop.insertMpanTops(dso22, pc04array, "39,", 340, "184");
		MpanTop.insertMpanTops(dso22, pc04array, "40,", 340, "185");
		MpanTop.insertMpanTops(dso22, pc04array, "41,", 340, "186");
		MpanTop.insertMpanTops(dso22, pc04array, "573, 580, 807, 808", 340,
				"244");
		MpanTop.insertMpanTops(dso22, pc04array, "47, 584", 340, "432");
		MpanTop.insertMpanTops(dso22, pc05to08array, "564, 579, 803, 804", 510,
				"154");
		MpanTop.insertMpanTops(dso22, pc05to08array, "564, 579, 803, 804", 520,
				"154");
		MpanTop.insertMpanTops(dso22, pc05to08array, "564, 579, 803, 804", 540,
				"154");
		MpanTop.insertMpanTops(dso22, pc05to08array, "564, 579, 803, 804", 550,
				"154");
		MpanTop.insertMpanTops(dso22, pc05to08array, "564, 579 ,803, 804", 570,
				"154");
		MpanTop.insertMpanTops(dso22, pc05to08array, "564, 579, 803, 804", 580,
				"154");
		MpanTop.insertMpanTops(dso22, pc01array, "49,50,560,561", 20, "243");
		MpanTop.insertMpanTops(dso22, pc01array, "504, 859", 980, "429");
		MpanTop.insertMpanTops(dso22, pc01array, "505, 860", 980, "430");
		MpanTop.insertMpanTops(dso22, pc01array, "503, 858", 980, "431");
		MpanTop.insertMpanTops(dso22, pc02array, "1, 510", 30, "16");
		MpanTop.insertMpanTops(dso22, pc02array, "2, 511", 30, "17");
		MpanTop.insertMpanTops(dso22, pc02array, "3, 512", 30, "18");
		MpanTop.insertMpanTops(dso22, pc02array, "4, 513", 30, "19");
		MpanTop.insertMpanTops(dso22, pc02array, "5, 514", 30, "20");
		MpanTop.insertMpanTops(dso22, pc02array, "6, 515", 30, "21");
		MpanTop.insertMpanTops(dso22, pc02array, "7, 516", 30, "22");
		MpanTop.insertMpanTops(dso22, pc02array, "8, 517", 30, "23");
		MpanTop.insertMpanTops(dso22, pc02array, "9 ,518", 30, "24");
		MpanTop.insertMpanTops(dso22, pc02array, "10, 519", 30, "25");
		MpanTop.insertMpanTops(dso22, pc02array, "11, 520", 30, "33");
		MpanTop.insertMpanTops(dso22, pc02array, "12, 521", 30, "34");
		MpanTop.insertMpanTops(dso22, pc02array, "13, 522", 30, "36");
		MpanTop.insertMpanTops(dso22, pc02array, "14, 523", 30, "37");
		MpanTop.insertMpanTops(dso22, pc02array, "15, 524", 30, "40");
		MpanTop.insertMpanTops(dso22, pc02array, "16, 525", 30, "41");
		MpanTop.insertMpanTops(dso22, pc02array, "17, 526", 30, "42");
		MpanTop.insertMpanTops(dso22, pc02array, "18, 527", 30, "43");
		MpanTop.insertMpanTops(dso22, pc02array, "19, 528", 30, "44");
		MpanTop.insertMpanTops(dso22, pc02array, "55, 567", 30, "62");
		MpanTop.insertMpanTops(dso22, pc02array, "20, 529", 30, "67");
		MpanTop.insertMpanTops(dso22, pc02array, "21, 530", 30, "73");
		MpanTop.insertMpanTops(dso22, pc02array, "22, 531", 30, "104");
		MpanTop.insertMpanTops(dso22, pc02array, "23, 532", 30, "106");
		MpanTop.insertMpanTops(dso22, pc02array, "24, 533", 30, "107");
		MpanTop.insertMpanTops(dso22, pc02array, "25, 534", 30, "108");
		MpanTop.insertMpanTops(dso22, pc02array, "576, 582, 820, 821", 30,
				"261");
		MpanTop.insertMpanTops(dso22, pc02array, "44, 554", 30, "265");
		MpanTop.insertMpanTops(dso22, pc02array, "45, 555", 30, "268");
		MpanTop.insertMpanTops(dso22, pc02array, "577, 583, 824, 825", 30,
				"270");
		MpanTop.insertMpanTops(dso22, pc02array, "62, 578", 30, "346");
		MpanTop.insertMpanTops(dso22, pc02array, "51, 575", 30, "427");
		MpanTop.insertMpanTops(dso22, pc02array, "864, 865", 30, "935");
		MpanTop.insertMpanTops(dso22, pc02array, "576, 582, 820, 821", 70,
				"261");
		MpanTop.insertMpanTops(dso22, pc02array, "51, 575", 70, "427");
		MpanTop.insertMpanTops(dso22, pc02array, "55, 567", 410, "62");
		MpanTop.insertMpanTops(dso22, pc02array, "44, 554", 410, "265");
		MpanTop.insertMpanTops(dso22, pc02array, "45, 555", 410, "268");
		MpanTop.insertMpanTops(dso22, pc02array, "577, 583, 824, 825", 410,
				"270");
		MpanTop.insertMpanTops(dso22, pc02array, "55, 567", 415, "62");
		MpanTop.insertMpanTops(dso22, pc02array, "44, 554", 415, "265");
		MpanTop.insertMpanTops(dso22, pc02array, "45, 555", 415, "268");
		MpanTop.insertMpanTops(dso22, pc02array, "577, 583, 824, 825", 415,
				"270");
		MpanTop.insertMpanTops(dso22, pc02array, "20, 529", 420, "67");
		MpanTop.insertMpanTops(dso22, pc02array, "21, 530", 420, "73");
		MpanTop.insertMpanTops(dso22, pc02array, "20, 529", 425, "67");
		MpanTop.insertMpanTops(dso22, pc02array, "21, 530", 425, "73");
		MpanTop.insertMpanTops(dso22, pc02array, "1, 510", 440, "16");
		MpanTop.insertMpanTops(dso22, pc02array, "2, 511", 440, "17");
		MpanTop.insertMpanTops(dso22, pc02array, "3, 512", 440, "18");
		MpanTop.insertMpanTops(dso22, pc02array, "4, 513", 440, "19");
		MpanTop.insertMpanTops(dso22, pc02array, "5, 514", 440, "20");
		MpanTop.insertMpanTops(dso22, pc02array, "6, 515", 440, "21");
		MpanTop.insertMpanTops(dso22, pc02array, "7, 516", 440, "22");
		MpanTop.insertMpanTops(dso22, pc02array, "8, 517", 440, "23");
		MpanTop.insertMpanTops(dso22, pc02array, "9, 518", 440, "24");
		MpanTop.insertMpanTops(dso22, pc02array, "10, 519", 440, "25");
		MpanTop.insertMpanTops(dso22, pc02array, "11, 520", 440, "33");
		MpanTop.insertMpanTops(dso22, pc02array, "12, 521", 440, "34");
		MpanTop.insertMpanTops(dso22, pc02array, "13, 522", 440, "36");
		MpanTop.insertMpanTops(dso22, pc02array, "14, 523", 440, "37");
		MpanTop.insertMpanTops(dso22, pc02array, "15, 524", 440, "40");
		MpanTop.insertMpanTops(dso22, pc02array, "16, 525", 440, "41");
		MpanTop.insertMpanTops(dso22, pc02array, "17, 526", 440, "42");
		MpanTop.insertMpanTops(dso22, pc02array, "18, 527", 440, "43");
		MpanTop.insertMpanTops(dso22, pc02array, "19, 528", 440, "44");
		MpanTop.insertMpanTops(dso22, pc02array, "62, 578", 440, "346");
		MpanTop.insertMpanTops(dso22, pc02array, "1, 510", 445, "16");
		MpanTop.insertMpanTops(dso22, pc02array, "2, 511", 445, "17");
		MpanTop.insertMpanTops(dso22, pc02array, "3, 512", 445, "18");
		MpanTop.insertMpanTops(dso22, pc02array, "4, 513", 445, "19");
		MpanTop.insertMpanTops(dso22, pc02array, "5, 514", 445, "20");
		MpanTop.insertMpanTops(dso22, pc02array, "6, 515", 445, "21");
		MpanTop.insertMpanTops(dso22, pc02array, "7, 516", 445, "22");
		MpanTop.insertMpanTops(dso22, pc02array, "8, 517", 445, "23");
		MpanTop.insertMpanTops(dso22, pc02array, "9, 518", 445, "24");
		MpanTop.insertMpanTops(dso22, pc02array, "10, 519", 445, "25");
		MpanTop.insertMpanTops(dso22, pc02array, "11, 520", 445, "33");
		MpanTop.insertMpanTops(dso22, pc02array, "12, 521", 445, "34");
		MpanTop.insertMpanTops(dso22, pc02array, "13, 522", 445, "36");
		MpanTop.insertMpanTops(dso22, pc02array, "14, 523", 445, "37");
		MpanTop.insertMpanTops(dso22, pc02array, "15, 524", 445, "40");
		MpanTop.insertMpanTops(dso22, pc02array, "16, 525", 445, "41");
		MpanTop.insertMpanTops(dso22, pc02array, "17, 526", 445, "42");
		MpanTop.insertMpanTops(dso22, pc02array, "18, 527", 445, "43");
		MpanTop.insertMpanTops(dso22, pc02array, "19, 528", 445, "44");
		MpanTop.insertMpanTops(dso22, pc02array, "62, 578", 445, "346");
		MpanTop.insertMpanTops(dso22, pc02array, "22, 531", 450, "104");
		MpanTop.insertMpanTops(dso22, pc02array, "23, 532", 450, "106");
		MpanTop.insertMpanTops(dso22, pc02array, "24, 533", 450, "107");
		MpanTop.insertMpanTops(dso22, pc02array, "25, 534", 450, "108");
		MpanTop.insertMpanTops(dso22, pc02array, "22, 531", 455, "104");
		MpanTop.insertMpanTops(dso22, pc02array, "23, 532", 455, "106");
		MpanTop.insertMpanTops(dso22, pc02array, "24, 533", 455, "107");
		MpanTop.insertMpanTops(dso22, pc02array, "25, 534", 455, "108");
		MpanTop.insertMpanTops(dso22, pc02array, "576, 582, 820, 821", 840,
				"261");
		MpanTop.insertMpanTops(dso22, pc02array, "51, 575", 840, "427");
		MpanTop.insertMpanTops(dso22, pc03array, "46, 556", 110, "319");
		MpanTop.insertMpanTops(dso22, pc03array, "49,50,560,561", 120, "243");
		MpanTop.insertMpanTops(dso22, pc03array, "49,50,560,561", 140, "243");
		MpanTop.insertMpanTops(dso22, pc03array, "46, 556", 270, "319");
		MpanTop.insertMpanTops(dso22, pc04array, "1, 510", 210, "16");
		MpanTop.insertMpanTops(dso22, pc04array, "2, 511", 210, "17");
		MpanTop.insertMpanTops(dso22, pc04array, "3, 512", 210, "18");
		MpanTop.insertMpanTops(dso22, pc04array, "4, 513", 210, "19");
		MpanTop.insertMpanTops(dso22, pc04array, "5, 514", 210, "20");
		MpanTop.insertMpanTops(dso22, pc04array, "6, 515", 210, "21");
		MpanTop.insertMpanTops(dso22, pc04array, "7, 516", 210, "22");
		MpanTop.insertMpanTops(dso22, pc04array, "8, 517", 210, "23");
		MpanTop.insertMpanTops(dso22, pc04array, "9, 518", 210, "24");
		MpanTop.insertMpanTops(dso22, pc04array, "10, 519", 210, "25");
		MpanTop.insertMpanTops(dso22, pc04array, "11, 520", 210, "33");
		MpanTop.insertMpanTops(dso22, pc04array, "12, 521", 210, "34");
		MpanTop.insertMpanTops(dso22, pc04array, "13, 522", 210, "36");
		MpanTop.insertMpanTops(dso22, pc04array, "14, 523", 210, "37");
		MpanTop.insertMpanTops(dso22, pc04array, "15, 524", 210, "40");
		MpanTop.insertMpanTops(dso22, pc04array, "16, 525", 210, "41");
		MpanTop.insertMpanTops(dso22, pc04array, "17, 526", 210, "42");
		MpanTop.insertMpanTops(dso22, pc04array, "18, 527", 210, "43");
		MpanTop.insertMpanTops(dso22, pc04array, "19, 528", 210, "44");
		MpanTop.insertMpanTops(dso22, pc04array, "55, 567", 210, "62");
		MpanTop.insertMpanTops(dso22, pc04array, "20, 529", 210, "67");
		MpanTop.insertMpanTops(dso22, pc04array, "21, 530", 210, "73");
		MpanTop.insertMpanTops(dso22, pc04array, "22, 531", 210, "104");
		MpanTop.insertMpanTops(dso22, pc04array, "23, 532", 210, "106");
		MpanTop.insertMpanTops(dso22, pc04array, "24, 533", 210, "107");
		MpanTop.insertMpanTops(dso22, pc04array, "25, 534", 210, "108");
		MpanTop.insertMpanTops(dso22, pc04array, "576, 582, 820, 821", 210,
				"261");
		MpanTop.insertMpanTops(dso22, pc04array, "44, 554", 210, "265");
		MpanTop.insertMpanTops(dso22, pc04array, "45, 555", 210, "268");
		MpanTop.insertMpanTops(dso22, pc04array, "577, 583, 824, 825", 210,
				"270");
		MpanTop.insertMpanTops(dso22, pc04array, "62, 578", 210, "346");
		MpanTop.insertMpanTops(dso22, pc04array, "51, 575", 210, "427");
		MpanTop.insertMpanTops(dso22, pc04array, "576, 582, 820, 821", 350,
				"261");
		MpanTop.insertMpanTops(dso22, pc04array, "51, 575", 350, "427");
		MpanTop.insertMpanTops(dso22, pc05to08array, "26,27,535,559", 510,
				"127");
		MpanTop.insertMpanTops(dso22, pc05to08array, "29,30,539,540", 510,
				"135");
		MpanTop.insertMpanTops(dso22, pc05to08array, "500, 501, 801, 802", 510,
				"393");
		MpanTop.insertMpanTops(dso22, pc05to08array, "26,27,535,559", 520,
				"127");
		MpanTop.insertMpanTops(dso22, pc05to08array, "29,30,539,540", 520,
				"135");
		MpanTop.insertMpanTops(dso22, pc05to08array, "500, 501, 801, 802", 520,
				"393");
		MpanTop.insertMpanTops(dso22, pc05to08array, "26,27,535,559", 540,
				"127");
		MpanTop.insertMpanTops(dso22, pc05to08array, "29,30,539,540", 540,
				"135");
		MpanTop.insertMpanTops(dso22, pc05to08array, "500, 501, 801, 802", 540,
				"393");
		MpanTop.insertMpanTops(dso22, pc05to08array, "26,27,535,559", 550,
				"127");
		MpanTop.insertMpanTops(dso22, pc05to08array, "29,30,539,540", 550,
				"135");
		MpanTop.insertMpanTops(dso22, pc05to08array, "500, 501, 801, 802", 550,
				"393");
		MpanTop.insertMpanTops(dso22, pc05to08array, "26,27,535,559", 570,
				"127");
		MpanTop.insertMpanTops(dso22, pc05to08array, "29,30,539,540", 570,
				"135");
		MpanTop.insertMpanTops(dso22, pc05to08array, "500, 501, 801, 802", 570,
				"393");
		MpanTop.insertMpanTops(dso22, pc05to08array, "26,27,535,559", 580,
				"127");
		MpanTop.insertMpanTops(dso22, pc05to08array, "29,30,539,540", 580,
				"135");
		MpanTop.insertMpanTops(dso22, pc05to08array, "500, 501, 801, 802", 580,
				"393");

		MpanTop.insertMpanTops(dso22, pc01array, "867, 870", 11,
				"482, 940, 941");
		MpanTop.insertMpanTops(dso22, pc01array, "866, 869", 11,
				"490, 940, 941");
		MpanTop.insertMpanTops(dso22, pc01array, "868, 871", 11,
				"498, 940, 941");

		MpanTop.insertMpanTops(dso22, pc02array, "867, 870", 31,
				"483, 940, 941");
		MpanTop.insertMpanTops(dso22, pc02array, "866, 869", 31,
				"491, 940, 941");
		MpanTop.insertMpanTops(dso22, pc02array, "868, 871", 31,
				"498, 940, 941");

		MpanTop.insertMpanTops(dso22, pc03array, "867, 870", 111,
				"484, 940, 941");
		MpanTop.insertMpanTops(dso22, pc03array, "866, 869", 111,
				"492, 940, 941");
		MpanTop.insertMpanTops(dso22, pc03array, "868, 871", 111,
				"498, 940, 941");

		MpanTop.insertMpanTops(dso22, pc04array, "867, 870", 211,
				"485, 940, 941");
		MpanTop.insertMpanTops(dso22, pc04array, "866, 869", 211,
				"493, 940, 941");
		MpanTop.insertMpanTops(dso22, pc04array, "868, 871", 211,
				"498, 940, 941");

		MpanTop.insertMpanTops(dso22, pc05to08array, "867, 870", 521,
				"486, 487, 488, 489, 940, 941");
		MpanTop.insertMpanTops(dso22, pc05to08array, "866, 869", 521,
				"494, 495, 496, 497, 940, 941");
		MpanTop.insertMpanTops(dso22, pc05to08array, "868, 871", 521,
				"498, 940, 941");

		MpanTop.insertMpanTops(dso22, pc05to08array, "867, 870", 551,
				"486, 487, 488, 489, 494, 495, 496, 497, 498, 940, 941");
		MpanTop.insertMpanTops(dso22, pc05to08array, "866, 868, 869, 871", 551,
				"940, 941");

		MpanTop.insertMpanTops(dso22, pc05to08array, "867, 870", 581,
				"486, 487, 488, 489, 494, 495, 496, 497, 498, 940, 941");
		MpanTop.insertMpanTops(dso22, pc05to08array, "866, 868, 869, 871", 581,
				"940, 941");

		MpanTop.insertMpanTops(dso22, pc08array, "502, 857", 980, "428");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				510, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				520, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				521, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				540, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				550, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				551, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				570, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				580, "9999");
		MpanTop.insertMpanTops(dso22, pc00array,
				"845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856",
				581, "9999");
		/*
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "610", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "611", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "640", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "641", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "650", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "651", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "660", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "661", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "670", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "671", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "680", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "681", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "690", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "691", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "692", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "694", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "693", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "695", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "696", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "710", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "711", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "720", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "721", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "730", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "731", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "741", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "750", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "751", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "752", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "753", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "754", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "671", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "671", "9999");
		 * MpanTop.insertMpanTops(dso22, pc00array, "845", "671", "9999");
		 */
		
		/*
		MpanTop.insertMpanTops(dso22, pc00array, "863", 970, "9999");

		MpanTop.insertMpanTops(dso99, pc00array, "845", 000, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 001, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 002, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 003, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 004, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 005, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 006, "9999");
		MpanTop.insertMpanTops(dso99, pc00array, "845", 007, "9999");
		/*
		 * llf22_10.attachProfileClass(pc01);
		 * llf22_10.addMeterTimeswitches("500, 501, 801,802");
		 * llf22_11.attachProfileClass(pc01); llf22_11
		 * .addMeterTimeswitches("867, 870, 866, 869, 868, 871, 866, 867, 868,
		 * 869, 870, 871, 866, 867, 868, 869, 870, 871");
		 * llf22_20.attachProfileClass(pc01);
		 * llf22_20.addMeterTimeswitches("587, 835, 49, 50, 560, 561");
		 * llf22_30.attachProfileClass(pc02); llf22_30
		 * .addMeterTimeswitches("536, 48, 585, 31, 541, 32, 542, 33, 543, 34,
		 * 544, 35, 545, 36, 546, 37, 547, 38, 548, 39, 549, 40, 550, 41, 551,
		 * 573, 580, 807, 808, 574, 581, 818, 819, 43, 553, 52, 586, 557, 537,
		 * 558, 47, 584, 53, 57, 565, 569, 54, 58, 566, 570, 74, 599, 63, 588,
		 * 64, 589, 65, 590, 66, 591, 67, 592, 68, 593, 69, 594, 70, 595, 71,
		 * 596, 72, 597, 1, 510, 2, 511, 3, 512, 4, 513, 5, 514, 6, 515, 7, 516,
		 * 8, 517, 9, 518, 10, 519, 11, 520, 12, 521, 13, 522, 14, 523, 15, 524,
		 * 16, 525, 17, 526, 18, 527, 19, 528, 55, 567, 20, 529, 21, 530, 22,
		 * 531, 23, 532, 24, 533, 25, 534, 576, 582, 820, 821, 44, 554, 45, 555,
		 * 577, 583, 824, 825, 62, 578, 51, 575, 864, 865");
		 * llf22_31.attachProfileClass(pc02);
		 * llf22_31.addMeterTimeswitches("867, 870, 866, 869, 868, 871, 867,
		 * 870"); llf22_40.attachProfileClass(pc02);
		 * llf22_40.addMeterTimeswitches("42, 552");
		 * llf22_50.attachProfileClass(pc02);
		 * llf22_50.addMeterTimeswitches("536, 54, 58, 566, 570");
		 * llf22_51.attachProfileClass(pc02);
		 * llf22_51.addMeterTimeswitches("537");
		 * llf22_60.attachProfileClass(pc02);
		 * llf22_60.addMeterTimeswitches("557, 53, 57, 565, 569");
		 * llf22_61.attachProfileClass(pc02);
		 * llf22_61.addMeterTimeswitches("558");
		 * llf22_70.attachProfileClass(pc02);
		 * llf22_70.addMeterTimeswitches("576, 582, 820, 821, 51, 575");
		 * llf22_110.attachProfileClass(pc03);
		 * llf22_110.addMeterTimeswitches("500, 501, 801, 802, 46, 556");
		 * llf22_111.attachProfileClass(pc03); llf22_111
		 * .addMeterTimeswitches("867, 870, 866, 869, 868, 871, 869, 870");
		 * llf22_120.attachProfileClass(pc03);
		 * llf22_120.addMeterTimeswitches("587, 835, 49, 50, 560, 561");
		 * llf22_130.attachProfileClass(pc03);
		 * llf22_130.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_140.attachProfileClass(pc03);
		 * llf22_140.addMeterTimeswitches("587, 835, 49, 50, 560, 561");
		 * llf22_210.attachProfileClass(pc04); llf22_210
		 * .addMeterTimeswitches("536, 48, 585, 564, 579, 803, 804, 31, 541, 32,
		 * 542, 33, 543, 34, 544, 35, 545, 36, 546, 37, 547, 38, 548, 39, 549,
		 * 40, 550, 41, 551, 573, 580, 807, 808, 56, 60, 568, 572, 574, 581,
		 * 818, 819, 43, 553, 52, 586, 537, 562, 563, 47, 584, 54, 58, 566, 570,
		 * 74, 599, 63, 588, 64, 589, 65, 590, 66, 591, 67, 592, 68, 593, 69,
		 * 594, 70, 595, 71, 596, 72, 597, 1, 510, 2, 511, 3, 512, 4, 513, 5,
		 * 514, 6, 515, 7, 516, 8, 517, 9, 518, 10, 519, 11, 520, 12, 521, 13,
		 * 522, 14, 523, 15, 524, 16, 525, 17, 526, 18, 527, 19, 528, 55, 567,
		 * 20, 529, 21, 530, 22, 531, 23, 532, 24, 533, 25, 534, 576, 582, 820,
		 * 821, 44, 554, 45, 555, 577, 583, 824, 825, 62, 578, 51, 575");
		 * llf22_211.attachProfileClass(pc04);
		 * llf22_211.addMeterTimeswitches("867, 870, 866, 869, 868, 871");
		 * llf22_220.attachProfileClass(pc04);
		 * llf22_220.addMeterTimeswitches("42, 552");
		 * llf22_230.attachProfileClass(pc04); llf22_230
		 * .addMeterTimeswitches("564, 579, 803, 804, 31, 541, 32, 542, 33, 543,
		 * 34, 544, 35, 545, 36, 546, 37, 547, 38, 548, 39, 549, 40, 550, 41,
		 * 551, 573, 580, 807, 808, 47, 584");
		 * llf22_240.attachProfileClass(pc04);
		 * llf22_240.addMeterTimeswitches("42, 552");
		 * llf22_250.attachProfileClass(pc04);
		 * llf22_250.addMeterTimeswitches("536, 54, 58, 566, 570");
		 * llf22_251.attachProfileClass(pc04);
		 * llf22_251.addMeterTimeswitches("537");
		 * llf22_260.attachProfileClass(pc04);
		 * llf22_260.addMeterTimeswitches("536, 54, 58, 566, 570");
		 * llf22_261.attachProfileClass(pc04);
		 * llf22_261.addMeterTimeswitches("537");
		 * llf22_270.attachProfileClass(pc03);
		 * llf22_270.addMeterTimeswitches("46, 556");
		 * llf22_280.attachProfileClass(pc04);
		 * llf22_280.addMeterTimeswitches("56, 60, 568, 572, 562");
		 * llf22_281.attachProfileClass(pc04);
		 * llf22_281.addMeterTimeswitches("563");
		 * llf22_310.attachProfileClass(pc03);
		 * llf22_310.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_320.attachProfileClass(pc03);
		 * llf22_320.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_330.attachProfileClass(pc04); llf22_330
		 * .addMeterTimeswitches("564, 579, 803, 804, 31, 541, 32, 542, 33, 543,
		 * 34, 544, 35, 545, 36, 546, 37, 547, 38, 548, 39, 549, 40, 550, 41,
		 * 551, 573, 580, 807, 808, 47, 584");
		 * llf22_320.attachProfileClass(pc03);
		 * llf22_320.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_330.attachProfileClass(pc04); llf22_330
		 * .addMeterTimeswitches("564, 579, 803, 804, 31, 541, 32, 542, 33, 543,
		 * 34, 544, 35, 545, 36, 546, 37, 547, 38, 548, 39, 549, 40, 550, 41,
		 * 551, 573, 580, 807, 808, 47, 584");
		 * llf22_340.attachProfileClass(pc04); llf22_340
		 * .addMeterTimeswitches("564, 579, 803, 804, 31, 541, 32, 542, 33, 543,
		 * 34, 544, 35, 545, 36, 546, 37, 547, 38, 548, 39, 549, 40, 550, 41,
		 * 551, 573, 580, 807, 808, 47, 584");
		 * llf22_350.attachProfileClass(pc04);
		 * llf22_350.addMeterTimeswitches("576, 582, 820, 821, 51, 575");
		 * llf22_410.attachProfileClass(pc02); llf22_410
		 * .addMeterTimeswitches("55, 567, 44, 554, 45, 555, 577, 583, 824,
		 * 825"); llf22_415.attachProfileClass(pc02); llf22_415
		 * .addMeterTimeswitches("55, 567, 44, 554, 45, 555, 577, 583, 824,
		 * 825"); llf22_420.attachProfileClass(pc02);
		 * llf22_420.addMeterTimeswitches("20, 529, 21, 530");
		 * llf22_425.attachProfileClass(pc02);
		 * llf22_425.addMeterTimeswitches("20, 529, 21, 530");
		 * llf22_430.attachProfileClass(pc02); llf22_430
		 * .addMeterTimeswitches("48, 585, 574, 581, 818, 819, 43, 553, 52, 586,
		 * 74, 599, 63, 588, 64, 589, 65, 590, 66, 591, 67, 592, 68, 593, 69,
		 * 594, 70, 595, 71, 596, 72, 597"); llf22_435.attachProfileClass(pc02);
		 * llf22_435 .addMeterTimeswitches("48, 585, 574, 581, 818, 819, 43,
		 * 553, 52, 586, 74, 599, 63, 588, 64, 589, 65, 590, 66, 591, 67, 592,
		 * 68, 593, 69, 594, 70, 595, 71, 596, 72, 597");
		 * llf22_440.attachProfileClass(pc02); llf22_440
		 * .addMeterTimeswitches("1, 510, 2, 511, 3, 512, 4, 513, 5, 514, 6,
		 * 515, 7, 516, 8, 517, 9, 518, 10, 519, 11, 520, 12, 521, 13, 522, 14,
		 * 523, 15, 524, 16, 525, 17, 526, 18, 527, 19, 528, 62, 578");
		 * llf22_445.attachProfileClass(pc02); llf22_445
		 * .addMeterTimeswitches("1, 510, 2, 511, 3, 512, 4, 513, 5, 514, 6,
		 * 515, 7, 516, 8, 517, 9, 518, 10, 519, 11, 520, 12, 521, 13, 522, 14,
		 * 523, 15, 524, 16, 525, 17, 526, 18, 527, 19, 528, 62, 578");
		 * llf22_450.attachProfileClass(pc02);
		 * llf22_450.addMeterTimeswitches("22, 531, 23, 532, 24, 533, 25, 534");
		 * llf22_455.attachProfileClass(pc02);
		 * llf22_455.addMeterTimeswitches("22, 531, 23, 532, 24, 533, 25, 534");
		 * llf22_460.attachProfileClass(pc03);
		 * llf22_460.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_470.attachProfileClass(pc03);
		 * llf22_470.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_480.attachProfileClass(pc03);
		 * llf22_480.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_510.attachProfileClass(pc05);
		 * llf22_510.attachProfileClass(pc06);
		 * llf22_510.attachProfileClass(pc07);
		 * llf22_510.attachProfileClass(pc08); llf22_510
		 * .addMeterTimeswitches("26, 27, 535, 559, 29, 30, 539, 540, 500, 501,
		 * 801, 802, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855,
		 * 856"); llf22_520.attachProfileClass(pc05);
		 * llf22_520.attachProfileClass(pc06);
		 * llf22_520.attachProfileClass(pc07);
		 * llf22_520.attachProfileClass(pc08); llf22_520
		 * .addMeterTimeswitches("26, 27, 535, 559, 29, 30, 539, 540, 500, 501,
		 * 801, 802, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855,
		 * 856"); llf22_521.attachProfileClass(pc05);
		 * llf22_521.attachProfileClass(pc06);
		 * llf22_521.attachProfileClass(pc07);
		 * llf22_521.attachProfileClass(pc08); llf22_521
		 * .addMeterTimeswitches("867, 870, 866, 869, 868, 871, 845, 846, 847,
		 * 848, 849, 850, 851, 852, 853, 854, 855, 856");
		 * llf22_540.attachProfileClass(pc05);
		 * llf22_540.attachProfileClass(pc06);
		 * llf22_540.attachProfileClass(pc07);
		 * llf22_540.attachProfileClass(pc08); llf22_540
		 * .addMeterTimeswitches("26, 27, 535, 559, 29, 30, 539, 540, 500, 501,
		 * 801, 802, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855,
		 * 856"); llf22_550.attachProfileClass(pc05);
		 * llf22_550.attachProfileClass(pc06);
		 * llf22_550.attachProfileClass(pc07);
		 * llf22_550.attachProfileClass(pc08); llf22_550
		 * .addMeterTimeswitches("26, 27, 535, 559, 29, 30, 539, 540, 500, 501,
		 * 801, 802"); llf22_551.attachProfileClass(pc05);
		 * llf22_551.attachProfileClass(pc06);
		 * llf22_551.attachProfileClass(pc07);
		 * llf22_551.attachProfileClass(pc08);
		 * llf22_551.addMeterTimeswitches("867, 870, 866, 869, 868, 871");
		 * llf22_570.attachProfileClass(pc05);
		 * llf22_570.attachProfileClass(pc06);
		 * llf22_570.attachProfileClass(pc07);
		 * llf22_570.attachProfileClass(pc08); llf22_570
		 * .addMeterTimeswitches("26, 27, 535, 559, 8, 29, 30, 539, 540, 8, 500,
		 * 501, 801, 802"); llf22_580.attachProfileClass(pc05);
		 * llf22_580.attachProfileClass(pc06);
		 * llf22_580.attachProfileClass(pc07);
		 * llf22_580.attachProfileClass(pc08); llf22_580
		 * .addMeterTimeswitches("26, 27, 535, 559, 29, 30, 539, 540, 500, 501,
		 * 801, 802"); llf22_581.attachProfileClass(pc05);
		 * llf22_581.attachProfileClass(pc06);
		 * llf22_581.attachProfileClass(pc07);
		 * llf22_581.attachProfileClass(pc08);
		 * llf22_581.addMeterTimeswitches("867, 870, 866, 869, 868, 871");
		 * llf22_840.attachProfileClass(pc02);
		 * llf22_840.addMeterTimeswitches("576, 582, 820, 821, 51, 575");
		 * llf22_850.attachProfileClass(pc02); llf22_850
		 * .addMeterTimeswitches("31, 541, 32, 542, 33, 543, 34, 544, 35, 545,
		 * 36, 546, 37, 547, 38, 548, 39, 549, 40, 550, 41, 551, 573, 580, 807,
		 * 808, 47, 584"); llf22_860.attachProfileClass(pc03);
		 * llf22_860.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_870.attachProfileClass(pc01);
		 * llf22_870.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_890.attachProfileClass(pc03);
		 * llf22_890.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_900.attachProfileClass(pc03);
		 * llf22_900.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_910.attachProfileClass(pc03);
		 * llf22_910.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_920.attachProfileClass(pc03);
		 * llf22_920.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_930.attachProfileClass(pc03);
		 * llf22_930.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_950.attachProfileClass(pc03);
		 * llf22_950.addMeterTimeswitches("500, 501, 801, 802");
		 * llf22_970.attachProfileClass(pc00);
		 * llf22_970.addMeterTimeswitches("863");
		 * llf22_980.attachProfileClass(pc01);
		 * llf22_980.attachProfileClass(pc08); llf22_980
		 * .addMeterTimeswitches("504, 859, 505, 860, 503, 858, 502, 857, 502,
		 * 857");
		 * 
		 */
	}
/*
	static private Dso insertDso(String name, String code)
			throws HttpException {
		Dso dso = Dso.insertDso(name, new DsoCode(code));
		ClassLoader classLoader = Dso.class.getClassLoader();
		DsoService dsoService;
		try {
			InputStreamReader isr = new InputStreamReader(classLoader
					.getResource(
							"net/sf/chellow/billing/dso"
									+ dso.getCode().getString() + "Service.py")
					.openStream(), "UTF-8");
			StringWriter pythonString = new StringWriter();
			int c;
			while ((c = isr.read()) != -1) {
				pythonString.write(c);
			}
			dsoService = dso.insertService("main", new HhEndDate(
					"2000-01-01T00:30Z"), pythonString.toString());
			RateScript dsoRateScript = dsoService.getRateScripts().iterator()
					.next();
			isr = new InputStreamReader(classLoader.getResource(
					"net/sf/chellow/billing/dso" + dso.getCode().getString()
							+ "ServiceRateScript.py").openStream(), "UTF-8");
			pythonString = new StringWriter();
			while ((c = isr.read()) != -1) {
				pythonString.write(c);
			}
			dsoRateScript.update(dsoRateScript.getStartDate(), dsoRateScript
					.getFinishDate(), pythonString.toString());
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return dso;
	}
*/
	private void upgrade10to11(Connection con) throws HttpException {
		try {
			Statement stmt = con.createStatement();

			// Also, do something about the old 000 mtcs attached to 98 and 99.

			// Add extra fields to MTC
			// 
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 5 and above (with Comms)', is_unmetered = false where code = '845'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 5 and above (without Comms)', is_unmetered = false where code = '846'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 A (with Comms)', is_unmetered = false where code = '847'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 B (with Comms)', is_unmetered = false where code = '848'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 C (with Comms)', is_unmetered = false where code = '849'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 D (with Comms)', is_unmetered = false where code = '850'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 A (without Comms)', is_unmetered = false where code = '851'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 B (without Comms)', is_unmetered = false where code = '852'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 C (without Comms)', is_unmetered = false where code = '853'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 6 D (without Comms)', is_unmetered = false where code = '854'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 7 (with Comms)', is_unmetered = false where code = '855'");
			stmt
					.execute("update meter_timeswitch set description = 'HH Code 7 (without Comms)', is_unmetered = false where code = '856'");

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
		Debug
				.print("Finished first part of upgrading, going on to initialize database...");
		dataDelta(con);
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