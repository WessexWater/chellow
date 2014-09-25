/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2014 Wessex Water Services Limited
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

import java.io.File;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Properties;
import java.util.Set;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.Logger;

import javax.management.MBeanServer;
import javax.management.MBeanServerFactory;
import javax.management.MalformedObjectNameException;
import javax.management.ObjectName;
import javax.naming.InitialContext;
import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import javax.sql.DataSource;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.MonadFormatter;
import net.sf.chellow.monad.MonadHandler;
import net.sf.chellow.monad.UserException;

import org.hibernate.jdbc.Work;
import org.python.core.PyString;
import org.python.core.PySystemState;
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

			Hiber.session().doWork(new Work() {
				public void execute(Connection con) throws SQLException {

					Statement stmt = con.createStatement();
					ResultSet rs = stmt.executeQuery("select current_database()");
					String dbName = null;
					while (rs.next()) {
				     dbName = rs.getString("current_database");
					}
					con.rollback();
					
					// get db hostname

					ArrayList<MBeanServer> server_list = MBeanServerFactory.findMBeanServer(null);
					MBeanServer server = server_list.get(0);
					Set<ObjectName> beans;
					try {
						beans = server.queryNames(new ObjectName("Catalina:type=DataSource,context=/chellow,class=javax.sql.DataSource,name=\"jdbc/chellow\",*"), null);
					} catch (MalformedObjectNameException e1) {
						throw new InternalException(e1);
					}
					ObjectName bean = beans.toArray(new ObjectName[]{})[0];

					String hostName = null;
					try {
					    String url = (String) server.getAttribute(bean, "url");

					    int i = url.indexOf("//");
					    url = url.substring(i + 2);
					    i = url.indexOf(":");
					    hostName = url.substring(0, i);
					} catch (Exception e) {
					    for (String attr : bean.toString().split(",")) {
					        if (attr.startsWith("host=")) {
					            hostName = attr.substring(5);
					        }
					    }
					}

					PythonInterpreter interp = new PythonInterpreter();
					PySystemState sysState = interp.getSystemState();

					String libPath = context.getRealPath("/WEB-INF/lib-python");
					if (libPath != null) {
						File libDir = new File(libPath);
						if (libDir.exists()) {
							PyString pyLibPath = new PyString(libPath);
							if (!sysState.path.contains(pyLibPath)) {
								sysState.path.append(pyLibPath);
							}
						}
					}
					String username = context.getInitParameter("db.username");
					String password = context.getInitParameter("db.password");

					try {
						interp.setOut(System.out);
						interp.setErr(System.err);
						interp.set("root_path", context.getRealPath("/"));
						interp.set("user_name", username);
						interp.set("password", password);
						interp.set("host_name", hostName);
						interp.set("password", password);
						interp.set("db_name", dbName);
						
						interp.execfile(context
								.getResourceAsStream("/WEB-INF/bootstrap.py"));
						
					} catch (Throwable e) {
						throw new UserException(e.getMessage() + " "
								+ HttpException.getStackTraceString(e));
					} finally {
						interp.cleanup();
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
}
