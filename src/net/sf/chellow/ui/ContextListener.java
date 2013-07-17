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
import java.io.InputStreamReader;
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
import java.util.Date;

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
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.UserRole;
import net.sf.chellow.physical.VoltageLevel;
import net.sf.chellow.ui.GeneralImport.Digester;

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
						.executeQuery("select * from contract where name = 'configuration';");
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
			throw new UserException("Errors in schema era.");
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

		try {
			Statement stmt = con.createStatement();
			con.setAutoCommit(false);
			stmt.executeUpdate("begin isolation level serializable read write");

			stmt.executeUpdate("alter table dno_contract drop constraint fkey_dno_contract_contract;");

			stmt.executeUpdate("alter table channel rename supply_generation_id to era_id");
			stmt.executeUpdate("alter index channel_supply_generation_id_key rename to channel_era_id_is_import_is_kwh_key");
			stmt.executeUpdate("alter table channel drop constraint fkey_channel_supply_generation;");

			stmt.executeUpdate("alter table snag add channel_id bigint default null references channel (id)");
			stmt.executeUpdate("alter table snag add site_id bigint default null references site (id)");
			stmt.executeUpdate("alter table snag add start_date timestamp with time zone default null");
			stmt.executeUpdate("alter table snag add finish_date timestamp with time zone default null");
			stmt.executeUpdate("update snag set channel_id = channel_snag.channel_id, start_date = channel_snag.start_date, finish_date = channel_snag.finish_date from channel_snag where snag.id = channel_snag.snag_id");
			stmt.executeUpdate("update snag set site_id = site_snag.site_id, start_date = site_snag.start_date, finish_date = site_snag.finish_date from site_snag where snag.id = site_snag.snag_id");
			stmt.executeUpdate("alter table snag alter channel_id drop default");
			stmt.executeUpdate("alter table snag alter site_id drop default");
			stmt.executeUpdate("alter table snag alter start_date drop default");
			stmt.executeUpdate("alter table snag alter finish_date drop default");
			stmt.executeUpdate("alter index description_idx rename to snag_description_idx");
			stmt.executeUpdate("create index snag_finish_date_idx on snag (finish_date);");
			stmt.executeUpdate("create index snag_start_date_idx on snag (start_date);");
			stmt.executeUpdate("alter index is_ignored_idx rename to snag_is_ignored_idx");

			stmt.executeUpdate("alter table bill alter net set not null");
			stmt.executeUpdate("alter table bill alter vat set not null");
			stmt.executeUpdate("alter table bill alter gross set not null");
			stmt.executeUpdate("alter table bill alter kwh set not null");
			stmt.executeUpdate("alter index finish_date_idx rename to bill_finish_date_idx");
			stmt.executeUpdate("alter index issue_date_idx rename to bill_issue_date_idx");
			stmt.executeUpdate("alter index start_date_idx rename to bill_start_date_idx");
			stmt.executeUpdate("alter table bill drop constraint fkey_bill__bill_type");
			stmt.executeUpdate("alter table bill add foreign key (bill_type_id) references bill_type(id);");
			stmt.executeUpdate("alter table bill drop constraint fkey_bill_batch");
			stmt.executeUpdate("alter table bill add foreign key (batch_id) references batch (id);");
			stmt.executeUpdate("alter table bill drop constraint fkey_bill_supply");
			stmt.executeUpdate("alter table bill add foreign key (supply_id) references supply (id);");

			stmt.executeUpdate("alter table party rename role_id to market_role_id");
			stmt.executeUpdate("alter table party add dno_code character varying(255) default null");
			stmt.executeUpdate("update party set dno_code = dno.code from dno where party.id = dno.party_id");
			stmt.executeUpdate("alter table party alter dno_code drop default");
			stmt.executeUpdate("update party set market_role_id = (select id from market_role where code = 'R') where dno_code = '99'");
			stmt.executeUpdate("alter table party drop constraint fkey_party_participant");
			stmt.executeUpdate("alter table party add foreign key (participant_id) references participant (id);");
			stmt.executeUpdate("alter table party drop constraint fkey_party_role");
			stmt.executeUpdate("alter table party add foreign key (market_role_id) references market_role (id);");

			stmt.executeUpdate("alter table contract add market_role_id bigint default null references market_role (id)");
			stmt.executeUpdate("alter table contract add is_core boolean not null default true");
			stmt.executeUpdate("alter table contract add properties text default ''");
			stmt.executeUpdate("alter table contract add state text default ''");
			stmt.executeUpdate("alter table contract add party_id bigint default null references party (id)");
			stmt.executeUpdate("update contract set market_role_id = (select id from market_role where code = 'Z'), is_core = (contract.id % 2 = 1), party_id = non_core_contract.provider_id from non_core_contract where contract.id = non_core_contract.non_core_id");
			stmt.executeUpdate("update contract set market_role_id = (select id from market_role where code = 'C'), is_core = false, party_id = hhdc_contract.provider_id from hhdc_contract where contract.id = hhdc_contract.contract_id");
			stmt.executeUpdate("update contract set market_role_id = (select id from market_role where code = 'X'), is_core = false, party_id = supplier_contract.provider_id from supplier_contract where contract.id = supplier_contract.contract_id");
			stmt.executeUpdate("update contract set market_role_id = (select id from market_role where code = 'M'), is_core = false, party_id = mop_contract.provider_id from mop_contract where contract.id = mop_contract.contract_id");
			stmt.executeUpdate("alter table contract alter market_role_id drop default");
			stmt.executeUpdate("alter table contract alter is_core drop default");
			stmt.executeUpdate("alter table contract alter properties drop default");
			stmt.executeUpdate("alter table contract alter state drop default");
			stmt.executeUpdate("alter table contract alter party_id drop default");
			stmt.executeUpdate("create sequence contract_id_sequence owned by contract.id;");
			stmt.execute("select setval('contract_id_sequence', (select max(id) + 1 from contract), false);");
			stmt.executeUpdate("update contract set start_rate_script_id = null, finish_rate_script_id = null  where id in (select contract_id from dno_contract);");
			stmt.executeUpdate("delete from rate_script where contract_id in (select contract_id from dno_contract);");
			stmt.executeUpdate("delete from contract where id in (select contract_id from dno_contract);");
			stmt.executeUpdate("alter table contract alter market_role_id set not null");
			stmt.executeUpdate("alter table contract alter party_id set not null");
			stmt.executeUpdate("alter table contract add constraint contract_market_role_id_name_key unique (market_role_id, name);");
			stmt.executeUpdate("alter table contract drop constraint fkey_contract_finish_rate_script");
			stmt.executeUpdate("alter table contract add foreign key (finish_rate_script_id) references rate_script (id);");
			stmt.executeUpdate("alter table contract drop constraint fkey_contract_start_rate_script");
			stmt.executeUpdate("alter table contract add foreign key (start_rate_script_id) references rate_script (id);");

			stmt.executeUpdate("alter table site_supply_generation rename to site_era;");
			stmt.executeUpdate("alter table site_era rename supply_generation_id to era_id");
			stmt.executeUpdate("alter sequence site_supply_generation_id_sequence rename to site_era_id_sequence;");
			stmt.executeUpdate("alter index site_supply_generation_pkey rename to site_era_pkey");
			stmt.executeUpdate("alter table site_era drop constraint fkey_site_supply_generation_site");
			stmt.executeUpdate("alter table site_era add foreign key (site_id) references site(id);");
			stmt.executeUpdate("alter table site_era drop constraint fkey_site_supply_generation_supply_generation");

			stmt.executeUpdate("alter table supply_generation rename to era;");
			stmt.executeUpdate("alter sequence supply_generation_id_sequence rename to era_id_sequence;");
			stmt.executeUpdate("alter table era drop constraint fkey_mpan_hhdc_contract;");
			stmt.executeUpdate("alter table era add foreign key (hhdc_contract_id) references contract(id);");
			stmt.executeUpdate("alter table era drop constraint fkey_mpan_mop_contract;");
			stmt.executeUpdate("alter table era add foreign key (mop_contract_id) references contract(id);");
			stmt.executeUpdate("alter table era add imp_mpan_core character varying(255) default null");
			stmt.executeUpdate("alter table era add imp_sc int default null");
			stmt.executeUpdate("alter table era add imp_llfc_id bigint default null references llfc(id)");
			stmt.executeUpdate("alter table era add imp_supplier_contract_id bigint default null references contract(id)");
			stmt.executeUpdate("alter table era add imp_supplier_account character varying(255) default null");
			stmt.executeUpdate("alter table era add exp_mpan_core character varying(255) default null");
			stmt.executeUpdate("alter table era add exp_sc int default null");
			stmt.executeUpdate("alter table era add exp_llfc_id bigint default null references llfc(id)");
			stmt.executeUpdate("alter table era add exp_supplier_contract_id bigint default null references contract(id)");
			stmt.executeUpdate("alter table era add exp_supplier_account character varying(255) default null");
			stmt.executeUpdate("update era set imp_mpan_core = (select dno.code || ' ' || substring(mpan_core.unique_part from 1 for 4) || ' ' || substring(mpan_core.unique_part from 5 for 4) || ' ' || substring(mpan_core.unique_part from 9 for 2) || mpan_core.check_digit from dno, mpan_core, mpan where mpan.id = era.import_mpan_id and mpan.core_id = mpan_core.id and mpan_core.dno_id = dno.party_id)");
			stmt.executeUpdate("update era set imp_sc = (select mpan.agreed_supply_capacity from mpan where mpan.id = era.import_mpan_id)");
			stmt.executeUpdate("update era set imp_llfc_id = (select mpan.llfc_id from mpan where mpan.id = era.import_mpan_id)");
			stmt.executeUpdate("update era set imp_supplier_contract_id = (select mpan.supplier_contract_id from mpan where mpan.id = era.import_mpan_id)");
			stmt.executeUpdate("update era set imp_supplier_account = (select mpan.supplier_account from mpan where mpan.id = era.import_mpan_id)");
			stmt.executeUpdate("update era set exp_mpan_core = (select dno.code || ' ' || substring(mpan_core.unique_part from 1 for 4) || ' ' || substring(mpan_core.unique_part from 5 for 4) || ' ' || substring(mpan_core.unique_part from 9 for 2) || mpan_core.check_digit from dno, mpan_core, mpan where mpan.id = era.export_mpan_id and mpan.core_id = mpan_core.id and mpan_core.dno_id = dno.party_id)");
			stmt.executeUpdate("update era set exp_sc = (select mpan.agreed_supply_capacity from mpan where mpan.id = era.export_mpan_id)");
			stmt.executeUpdate("update era set exp_llfc_id = (select mpan.llfc_id from mpan where mpan.id = era.export_mpan_id)");
			stmt.executeUpdate("update era set exp_supplier_contract_id = (select mpan.supplier_contract_id from mpan where mpan.id = era.export_mpan_id)");
			stmt.executeUpdate("update era set exp_supplier_account = (select mpan.supplier_account from mpan where mpan.id = era.export_mpan_id)");
			stmt.executeUpdate("alter table era drop import_mpan_id");
			stmt.executeUpdate("alter table era drop export_mpan_id");
			stmt.executeUpdate("alter table era alter imp_mpan_core drop default");
			stmt.executeUpdate("alter table era alter exp_mpan_core drop default");
			stmt.executeUpdate("alter table era alter imp_supplier_account drop default");
			stmt.executeUpdate("alter table era alter exp_supplier_account drop default");
			stmt.executeUpdate("alter table era rename meter_serial_number to msn");
			stmt.executeUpdate("alter index supply_generation_pkey rename to era_pkey");
			stmt.executeUpdate("alter table era drop constraint fkey_supply_generation_supply");
			stmt.executeUpdate("alter table era add foreign key (supply_id) references supply(id);");
			stmt.executeUpdate("alter index supply_generation__finish_date__idx rename to era_finish_date_idx");
			stmt.executeUpdate("alter index supply_generation__start_date__idx rename to era_start_date_idx");
			stmt.executeUpdate("alter table era drop constraint fkey_generation__cop");
			stmt.executeUpdate("alter table era add foreign key (cop_id) references cop (id);");
			stmt.executeUpdate("alter table era drop constraint fkey_generation__mtc");
			stmt.executeUpdate("alter table era add foreign key (mtc_id) references mtc (id);");
			stmt.executeUpdate("alter table era drop constraint fkey_generation__pc");
			stmt.executeUpdate("alter table era add foreign key (pc_id) references pc (id);");
			stmt.executeUpdate("alter table era drop constraint fkey_generation__ssc");
			stmt.executeUpdate("alter table era add foreign key (ssc_id) references ssc (id);");

			stmt.executeUpdate("create sequence rate_script_id_sequence owned by rate_script.id;");
			stmt.execute("select setval('rate_script_id_sequence', (select max(id) + 1 from rate_script), false);");
			stmt.execute("alter table rate_script add constraint rate_script_contract_id_start_date_key unique (contract_id, start_date)");
			stmt.executeUpdate("alter table rate_script drop constraint fkey_rate_script_contract");
			stmt.executeUpdate("alter table rate_script add foreign key (contract_id) references contract (id);");

			stmt.executeUpdate("alter table pc alter code type character varying(255) using to_char(code, 'FM00')");

			stmt.executeUpdate("alter table llfc alter code type character varying(255) using to_char(code, 'FM000')");
			stmt.executeUpdate("alter table llfc drop constraint fkey_llfc_dno;");
			stmt.executeUpdate("alter table llfc add foreign key (dno_id) references party(id);");
			stmt.executeUpdate("alter table llfc drop constraint fkey_llfc_voltage_level;");
			stmt.executeUpdate("alter table llfc add foreign key (voltage_level_id) references voltage_level (id);");

			stmt.executeUpdate("alter table mtc rename payment_type_id to meter_payment_type_id");
			stmt.executeUpdate("alter table mtc alter code type character varying(255) using to_char(code, 'FM000')");
			stmt.executeUpdate("alter table mtc drop constraint fkey_mtc_dno;");
			stmt.executeUpdate("alter table mtc add foreign key (dno_id) references party(id);");
			stmt.executeUpdate("alter index mtc_dno_id_key rename to mtc_dno_id_code_key");
			stmt.executeUpdate("alter table mtc drop constraint fkey_mtc_meter_type;");
			stmt.executeUpdate("alter table mtc add foreign key (meter_type_id) references meter_type (id);");
			stmt.executeUpdate("alter table mtc drop constraint fkey_mtc_payment_type;");
			stmt.executeUpdate("alter table mtc add foreign key (meter_payment_type_id) references meter_payment_type (id);");

			stmt.executeUpdate("alter table ssc alter code type character varying(255) using to_char(code, 'FM0000')");

			stmt.executeUpdate("alter table \"user\" rename role_id to user_role_id");

			stmt.executeUpdate("alter table supply alter note drop default");
			stmt.executeUpdate("alter table supply alter note set not null");
			stmt.executeUpdate("alter table supply add dno_contract_id bigint default null references contract(id)");
			stmt.executeUpdate("alter table supply drop constraint fkey_supply_generation__gsp_group;");
			stmt.executeUpdate("alter table supply add foreign key (gsp_group_id) references gsp_group(id);");
			stmt.executeUpdate("alter table supply drop constraint fkey_supply_generator_type;");
			stmt.executeUpdate("alter table supply add foreign key (generator_type_id) references generator_type (id);");
			stmt.executeUpdate("alter table supply drop constraint fkey_supply_source;");
			stmt.executeUpdate("alter table supply add foreign key (source_id) references source (id);");

			stmt.executeUpdate("alter table register_read rename meter_serial_number to msn");
			stmt.executeUpdate("alter index meter_serial_number__idx rename to register_read_msn_idx");
			stmt.executeUpdate("alter index present_date__idx rename to register_read_present_date_idx");
			stmt.executeUpdate("alter index previous_date__idx rename to register_read_previous_date_idx");
			stmt.executeUpdate("alter table register_read drop constraint fkey_bill__register_read;");
			stmt.executeUpdate("alter table register_read add foreign key (bill_id) references bill(id);");
			stmt.executeUpdate("alter table register_read drop constraint fkey_present_type__register_read;");
			stmt.executeUpdate("alter table register_read add foreign key (present_type_id) references read_type (id);");
			stmt.executeUpdate("alter table register_read drop constraint fkey_previous_type__register_read;");
			stmt.executeUpdate("alter table register_read add foreign key (previous_type_id) references read_type (id);");
			stmt.executeUpdate("alter table register_read drop constraint fkey_tpr__register_read;");
			stmt.executeUpdate("alter table register_read add foreign key (tpr_id) references tpr (id);");
			stmt.executeUpdate("alter table register_read drop constraint register_read_bill_id_fkey;");
			stmt.executeUpdate("alter table register_read add foreign key (bill_id) references bill (id) on delete cascade;");

			stmt.executeUpdate("alter table batch drop constraint fkey_batch_contract;");
			stmt.executeUpdate("alter table batch add foreign key (contract_id) references contract(id);");

			stmt.executeUpdate("alter index batch_contract_id_key rename to batch_contract_id_reference_key");

			stmt.executeUpdate("drop table mpan cascade;");
			stmt.executeUpdate("drop sequence mpan_id_sequence cascade;");
			stmt.executeUpdate("drop table mpan_core cascade;");
			stmt.executeUpdate("drop sequence mpan_core_id_sequence cascade;");
			stmt.executeUpdate("drop table non_core_contract cascade;");
			stmt.executeUpdate("drop table hhdc_contract cascade;");
			stmt.executeUpdate("drop table supplier_contract cascade;");
			stmt.executeUpdate("drop table mop_contract cascade;");
			stmt.executeUpdate("drop table dno_contract cascade;");

			stmt.executeUpdate("drop table provider cascade;");
			stmt.executeUpdate("drop table dno cascade;");
			stmt.executeUpdate("drop table channel_snag cascade;");
			stmt.executeUpdate("drop table site_snag cascade;");

			stmt.executeUpdate("alter table site_era add foreign key (era_id) references era(id);");
			stmt.executeUpdate("alter table channel add foreign key (era_id) references era (id);");

			stmt.executeUpdate("alter index hh_datum_channel_id_key rename to hh_datum_channel_id_start_date_key;");

			stmt.executeUpdate("alter table clock_interval drop constraint fkey_clock_interval_tpr;");
			stmt.executeUpdate("alter table clock_interval add foreign key (tpr_id) references tpr (id);");

			// takes ages
			stmt.executeUpdate("alter table hh_datum add last_modified timestamp with time zone not null default 'epoch'");
			stmt.executeUpdate("alter table hh_datum alter last_modified drop default");
			stmt.executeUpdate("commit");
			con.setAutoCommit(false);
		} catch (SQLException sqle) {
			throw new InternalException(sqle);
		}
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

		try {
			Statement stmt = con.createStatement();
			con.setAutoCommit(false);

			stmt.executeUpdate("update supply set dno_contract_id = (select id from contract where name = (select substring(imp_mpan_core from 1 for 2) from era where supply_id = supply.id and imp_mpan_core is not null limit 1)) where supply.dno_contract_id is null");
			stmt.executeUpdate("update supply set dno_contract_id = (select id from contract where name = (select substring(exp_mpan_core from 1 for 2) from era where supply_id = supply.id and exp_mpan_core is not null limit 1)) where supply.dno_contract_id is null");
			stmt.executeUpdate("alter table supply alter dno_contract_id set not null"); //
			stmt.executeUpdate("update contract set charge_script = E'def on_start_up(ctx):\n    pass' where name = 'startup'");
			stmt.executeUpdate("commit");
			con.setAutoCommit(false);
			con.close();
		} catch (SQLException sqle) {
			throw new InternalException(sqle);
		}

		String name = null;
		try {
			Hiber.setReadWrite();
			Digester digester = null;
			try {
				digester = new Digester(new InputStreamReader(context
						.getResource("/WEB-INF/non-core-contracts.xml")
						.openStream(), "UTF-8"), "xml");
			} catch (UnsupportedEncodingException e) {
				throw new InternalException(e);
			} catch (MalformedURLException e) {
				throw new InternalException(e);
			} catch (IOException e) {
				throw new InternalException(e);
			}
			String[] values = digester.getLine();

			while (values != null) {
				if (values.length < 2) {
					throw new UserException(
							"There must be an 'Action' field followed "
									+ "by a 'Type' field.");
				}
				Hiber.setReadWrite();
				String action = values[0].trim().toLowerCase();
				String type = values[1].trim().toLowerCase();
				if (action.equals("insert") && type.equals("non-core-contract")) {
					name = values[4];
					String script = values[5];
					Contract contract = Contract.findNonCoreContract(name);
					if (contract == null) {
						Contract.insertNonCoreContract(true,
								Participant.getParticipant("CALB"), name,
								HhStartDate.roundDown(new Date()), null,
								script, "");
					} else {
						contract.update(contract.getParty(),
								contract.getName(), script);
					}
				}
				Hiber.commit();
				values = digester.getLine();
			}
			Hiber.setReadWrite();
			digester = null;
			try {
				digester = new Digester(new InputStreamReader(context
						.getResource("/WEB-INF/reports.xml").openStream(),
						"UTF-8"), "xml");
			} catch (UnsupportedEncodingException e) {
				throw new InternalException(e);
			} catch (MalformedURLException e) {
				throw new InternalException(e);
			} catch (IOException e) {
				throw new InternalException(e);
			}
			values = digester.getLine();
			while (values != null) {
				if (values.length < 2) {
					throw new UserException(
							"There must be an 'Action' field followed "
									+ "by a 'Type' field.");
				}
				Hiber.setReadWrite();
				String action = values[0].trim().toLowerCase();
				String type = values[1].trim().toLowerCase();
				if (action.equals("insert") && type.equals("report")) {
					String idStr = values[2];
					long id = Long.parseLong(idStr.trim());
					Report report = Report.findReport(id);
					if (report != null) {
						name = values[4];
						String script = values[5];
						String template = values[6];
						report.update(name, script, template);
					}
				}
				Hiber.commit();
				values = digester.getLine();
			}
		} catch (Throwable e) {
			throw new InternalException("Problem with name '" + name + "'", e);
		}
		Hiber.commit();
		Hiber.close();
	}
}
