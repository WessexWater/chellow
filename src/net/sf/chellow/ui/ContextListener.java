/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2013 Wessex Water Services Limited
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
import java.net.MalformedURLException;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
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

import net.sf.chellow.billing.BillType;
import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.MonadFormatter;
import net.sf.chellow.monad.MonadHandler;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.Cop;
import net.sf.chellow.physical.GeneratorType;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.UserRole;
import net.sf.chellow.physical.VoltageLevel;

import org.hibernate.Session;
import org.hibernate.jdbc.Work;
import org.hibernate.tool.hbm2ddl.SchemaUpdate;
import org.postgresql.copy.CopyManager;
import org.postgresql.core.BaseConnection;
import org.python.util.PythonInterpreter;

public class ContextListener implements ServletContextListener {
	public static final String CONTEXT_REQUEST_MAP = "net.sf.chellow.request_map";
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
			DataSource ds = (DataSource) cxt
					.lookup("java:/comp/env/jdbc/chellow");

			if (ds == null) {
				throw new Exception("Data source not found!");
			}
			Connection con = ds.getConnection();
			Statement stmt = con.createStatement();
			boolean shouldInitialize = false;
			try {
				// Find if DB has been created
				ResultSet rs = stmt
						.executeQuery("select * from contract where name = 'system';");
				boolean upgrade = true;
				while (rs.next()) {
					upgrade = false;
				}
				if (upgrade) {
					upgradeFrom666(con);
				}
			} catch (SQLException sqle) {
				shouldInitialize = true;
				String db_name = null;
				stmt = con.createStatement();
				ResultSet rs = stmt.executeQuery("select current_database()");
				while (rs.next()) {
					db_name = rs.getString("current_database");
				}
				stmt.executeUpdate("alter database " + db_name
						+ " set default_transaction_isolation = 'serializable'");
				stmt.executeUpdate("alter database " + db_name
						+ " set default_transaction_deferrable = on;");
				stmt.executeUpdate("alter database " + db_name
						+ " SET DateStyle TO 'ISO, YMD'");
				stmt.executeUpdate("alter database " + db_name
						+ " set default_transaction_read_only = on;");
			} finally {
				con.close();
			}
			if (shouldInitialize) {
				initializeDatabase();
			}
			Hiber.session().doWork(new Work() {
				public void execute(Connection con) throws SQLException {
					if (con.getTransactionIsolation() != Connection.TRANSACTION_SERIALIZABLE) {
						throw new SQLException(
								"The transaction isolation level isn't serializable.");
					}
				}
			});
			Contract startupContract = Contract.getNonCoreContract("startup");
			List<Object> args = new ArrayList<Object>();
			args.add(context);
			startupContract.callFunction("on_start_up", args.toArray());
			Properties postProps = new Properties();
			PythonInterpreter.initialize(System.getProperties(), postProps,
					new String[] {});

			context.setAttribute(CONTEXT_REQUEST_MAP,
					Collections.synchronizedMap(new HashMap<Long, String>()));
		} catch (Throwable e) {
			Debug.print("Problem. " + HttpException.getStackTraceString(e));
			throw new RuntimeException(e);
		} finally {
			Hiber.close();
		}
	}

	public void contextDestroyed(ServletContextEvent event) {
		try {
			ServletContext context = event.getServletContext();
			Contract startupContract = Contract.getNonCoreContract("shutdown");
			List<Object> args = new ArrayList<Object>();
			args.add(context);
			startupContract.callFunction("on_shut_down", args.toArray());
			context.removeAttribute(CONTEXT_REQUEST_MAP);
		} catch (Throwable e) {
			Debug.print("Problem. " + HttpException.getStackTraceString(e));
			throw new RuntimeException(e);
		}
	}

	@SuppressWarnings("unchecked")
	private void initializeDatabase() throws HttpException {
		SchemaUpdate su = new SchemaUpdate(Hiber.getConfiguration());
		su.execute(false, true);

		Session s = Hiber.session();

		List<Exception> exceptions = su.getExceptions();
		if (exceptions.size() > 0) {
			for (Exception exception : exceptions) {
				exception.printStackTrace();
			}
			throw new UserException("Errors in schema generation.");
		}
		Hiber.setReadWrite();
		Configuration.getConfiguration();

		VoltageLevel.insertVoltageLevels();
		UserRole.insertUserRole(UserRole.EDITOR);

		UserRole.insertUserRole(UserRole.PARTY_VIEWER);
		UserRole.insertUserRole(UserRole.VIEWER);
		Hiber.commit();
		Hiber.setReadWrite();
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
		Hiber.setReadWrite();
		ReadType.insertReadType("N", "Normal");
		ReadType.insertReadType("N3", "Normal 3rd Party");
		ReadType.insertReadType("C", "Customer");
		ReadType.insertReadType("E", "Estimated");
		ReadType.insertReadType("E3", "Estimated 3rd Party");
		ReadType.insertReadType("EM", "Estimated Manual");
		ReadType.insertReadType("W", "Withdrawn");
		ReadType.insertReadType("X", "Exchange");
		ReadType.insertReadType("CP", "Computer");
		ReadType.insertReadType("IF", "Information");
		Hiber.commit();
		Hiber.setReadWrite();
		Cop.insertCop(Cop.COP_1, "CoP 1");
		Cop.insertCop(Cop.COP_2, "CoP 2");
		Cop.insertCop(Cop.COP_3, "CoP 3");
		Cop.insertCop(Cop.COP_4, "CoP 4");
		Cop.insertCop(Cop.COP_5, "CoP 5");
		Cop.insertCop(Cop.COP_6A, "CoP 6a 20 day memory");
		Cop.insertCop(Cop.COP_6B, "CoP 6b 100 day memory");
		Cop.insertCop(Cop.COP_6C, "CoP 6c 250 day memory");
		Cop.insertCop(Cop.COP_6D, "CoP 6d 450 day memory");
		Cop.insertCop(Cop.COP_7, "CoP 7");
		Hiber.commit();
		Hiber.setReadWrite();
		BillType.insertBillType("F", "Final");
		BillType.insertBillType("N", "Normal");
		BillType.insertBillType("W", "Withdrawn");
		Hiber.commit();

		s.doWork(new Work() {
			public void execute(Connection con) throws SQLException {
				try {
					CopyManager cm = new CopyManager(con
							.unwrap(BaseConnection.class));
					String[][] mddArray = {
							{ "gsp_group", "GSP_Group" },
							{ "pc", "Profile_Class" },
							{ "market_role", "Market_Role" },
							{ "participant", "Market_Participant" },
							{ "party", "Market_Participant_Role" },
							{ "llfc", "Line_Loss_Factor_Class" },
							{ "meter_type", "MTC_Meter_Type" },
							{ "meter_payment_type", "MTC_Payment_Type" },
							{ "mtc", "Meter_Timeswitch_Class" },
							{ "tpr", "Time_Pattern_Regime" },
							{ "clock_interval", "Clock_Interval" },
							{ "ssc", "Standard_Settlement_Configuration" },
							{ "measurement_requirement",
									"Measurement_Requirement" } };
					for (String[] impArray : mddArray) {
						cm.copyIn(
								"COPY " + impArray[0]
										+ " FROM STDIN CSV HEADER",
								context.getResource(
										"/WEB-INF/mdd/" + impArray[1] + ".csv")
										.openStream());
					}
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
				}
			}
		});

		Hiber.commit();
		Hiber.setReadWrite();
		try {
			GeneralImport process = new GeneralImport(null, context
					.getResource("/WEB-INF/dno-contracts.xml").openStream(),
					"xml");
			process.run();
			List<MonadMessage> errors = process.getErrors();
			if (!errors.isEmpty()) {
				throw new InternalException(errors.get(0).getDescription());
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
		Report.loadReports(context);
		try {
			GeneralImport process = new GeneralImport(null, context
					.getResource("/WEB-INF/non-core-contracts.xml")
					.openStream(), "xml");
			process.run();
			List<MonadMessage> errors = process.getErrors();
			if (!errors.isEmpty()) {
				throw new InternalException(errors.get(0).getDescription());
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
		Hiber.commit();
		Hiber.close();
	}

	private void upgradeFrom666(Connection con) throws HttpException {
		/*
		 * try { Statement stmt = con.createStatement();
		 * con.setAutoCommit(false);
		 * stmt.executeUpdate("begin isolation level serializable read write");
		 * stmt.executeUpdate(
		 * "alter table supply_generation alter column mop_contract_id set not null"
		 * ); stmt.executeUpdate(
		 * "alter table supply_generation alter column mop_account set not null"
		 * ); stmt.executeUpdate(
		 * "alter table supply_generation alter column hhdc_contract_id set not null"
		 * ); stmt.executeUpdate(
		 * "alter table supply_generation alter column hhdc_account set not null"
		 * ); stmt.executeUpdate("commit"); con.setAutoCommit(false);
		 * con.close(); } catch (SQLException sqle) { throw new
		 * InternalException(sqle); }
		 */
	}
}
