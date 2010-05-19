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

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.InvocationTargetException;
import java.net.MalformedURLException;
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
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.GeneratorType;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.UserRole;
import net.sf.chellow.physical.VoltageLevel;

import org.hibernate.tool.hbm2ddl.SchemaUpdate;
import org.postgresql.copy.CopyManager;
import org.postgresql.core.BaseConnection;
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
		Statement stmt = null;
		try {
			stmt = con.createStatement();
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
					.execute("CREATE UNIQUE INDEX channel_date ON hh_datum (channel_id, start_date);");
			stmt.execute("ALTER TABLE report ALTER COLUMN script TYPE text;");
			stmt.execute("ALTER TABLE report ALTER COLUMN template TYPE text;");
		} catch (SQLException e) {
			throw new InternalException(e);
		} finally {
			try {
				stmt.close();
			} catch (SQLException e) {
				throw new InternalException(e);
			}
		}
		Configuration.getConfiguration();
		Hiber.close();

		VoltageLevel.insertVoltageLevels();
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
		ReadType.insertReadType('A', "Actual Change of Supplier Read");
		ReadType.insertReadType('C', "Customer own read");
		ReadType
				.insertReadType('D',
						"Deemed (Settlement Registers) or Estimated (Non-Settlement Registers)");
		ReadType.insertReadType('F', "Final");
		ReadType.insertReadType('I', "Initial");
		ReadType.insertReadType('M', "MAR");
		ReadType.insertReadType('O', "Old Supplier's Estimated CoS Reading");
		ReadType.insertReadType('P', "Electronically collected via PPMIP");
		ReadType.insertReadType('Q', "Meter Reading modified manually by DC");
		ReadType.insertReadType('R', "Routine");
		ReadType.insertReadType('S', "Special");
		ReadType.insertReadType('T', "Proving Test Reading");
		ReadType.insertReadType('W', "Withdrawn");
		ReadType.insertReadType('Z', "Actual Change of Tenancy Read");
		ReadType.insertReadType('E', "Estimate");

		try {
			Debug.print("Starting to load MDD.");
			Class<?> delegatorClass = null;

			for (String className : new String[] {
					"org.apache.commons.dbcp.DelegatingConnection",
					"org.apache.tomcat.dbcp.dbcp.DelegatingConnection" }) {
				try {
					Class<?> candidateClass = Class.forName(className);
					Debug.print("Class exists "
							+ candidateClass.getCanonicalName());
					if (candidateClass.isInstance(con)) {
						Debug.print("Connection class is an instance of "
								+ candidateClass.getCanonicalName());
						delegatorClass = candidateClass;
						break;
					}
				} catch (ClassNotFoundException e) {
				}
			}
			BaseConnection baseConnection = (BaseConnection) delegatorClass
					.getMethod("getInnermostDelegate").invoke(con);

			CopyManager cm = new CopyManager(baseConnection);
			String[][] mddArray = { { "gsp_group", "GSP_Group" },
					{ "pc", "Profile_Class" },
					{ "market_role", "Market_Role" },
					{ "participant", "Market_Participant" },
					{ "party", "Market_Participant_Role-party" },
					{ "provider", "Market_Participant_Role-provider" },
					{ "dso", "Market_Participant_Role-dso" },
					{ "llfc", "Line_Loss_Factor_Class" },
					{ "meter_type", "MTC_Meter_Type" },
					{ "meter_payment_type", "MTC_Payment_Type" },
					{ "mtc", "Meter_Timeswitch_Class" },
					{ "tpr", "Time_Pattern_Regime" },
					{ "clock_interval", "Clock_Interval" },
					{ "ssc", "Standard_Settlement_Configuration" },
					{ "measurement_requirement", "Measurement_Requirement" } };
			for (String[] impArray : mddArray) {
				cm.copyIn("COPY " + impArray[0] + " FROM STDIN CSV HEADER",
						context.getResource(
								"/WEB-INF/mdd/" + impArray[1] + ".csv")
								.openStream());
			}
			Debug.print("Finished loading MDD.");
		} catch (SQLException e) {
			throw new InternalException(e);
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (MalformedURLException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (IllegalArgumentException e) {
			throw new InternalException(e);
		} catch (SecurityException e) {
			throw new InternalException(e);
		} catch (IllegalAccessException e) {
			throw new InternalException(e);
		} catch (InvocationTargetException e) {
			throw new InternalException(e);
		} catch (NoSuchMethodException e) {
			throw new InternalException(e);
		}
        Hiber.close();
		DsoContract.loadFromCsv(context);
		Report.loadReports(context);
		NonCoreContract.loadNonCoreContracts(context);
		Hiber.flush();
	}
}
