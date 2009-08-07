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

import java.util.Properties;
import java.util.logging.Level;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import net.sf.chellow.billing.Dsos;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.HhdcContracts;
import net.sf.chellow.billing.MopContracts;
import net.sf.chellow.billing.NonCoreContracts;
import net.sf.chellow.billing.Party;
import net.sf.chellow.billing.Providers;
import net.sf.chellow.billing.SupplierContracts;
import net.sf.chellow.monad.ForbiddenException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.UnauthorizedException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.GeneratorTypes;
import net.sf.chellow.physical.GspGroups;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.MarketRoles;
import net.sf.chellow.physical.MeterPaymentTypes;
import net.sf.chellow.physical.MeterTypes;
import net.sf.chellow.physical.Mtcs;
import net.sf.chellow.physical.Participants;
import net.sf.chellow.physical.Pcs;
import net.sf.chellow.physical.ReadTypes;
import net.sf.chellow.physical.SiteSnags;
import net.sf.chellow.physical.Sites;
import net.sf.chellow.physical.Sources;
import net.sf.chellow.physical.Sscs;
import net.sf.chellow.physical.Supplies;
import net.sf.chellow.physical.Tprs;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.UserRole;
import net.sf.chellow.physical.UserRoles;
import net.sf.chellow.physical.Users;

public class Chellow extends Monad implements Urlable {
	private static final long serialVersionUID = 1L;

	static public final MonadUri ROOT_URI;

	static public final Sources SOURCES_INSTANCE = new Sources();

	static public final Users USERS_INSTANCE = new Users();

	static public final Providers PROVIDERS_INSTANCE = new Providers();

	static public final Pcs PROFILE_CLASSES_INSTANCE = new Pcs();

	static public final Mtcs MTCS_INSTANCE = new Mtcs();

	static public final Tprs TPRS_INSTANCE = new Tprs();

	static public final Sscs SSCS_INSTANCE = new Sscs();

	public static final HhdcContracts HHDC_CONTRACTS_INSTANCE = new HhdcContracts();

	public static final MopContracts MOP_CONTRACTS_INSTANCE = new MopContracts();

	public static final SupplierContracts SUPPLIER_CONTRACTS_INSTANCE = new SupplierContracts();

	public static final Participants PARTICIPANTS_INSTANCE = new Participants();

	public static final MarketRoles MARKET_ROLES_INSTANCE = new MarketRoles();

	public static final Dsos DSOS_INSTANCE = new Dsos();

	public static final NonCoreContracts NON_CORE_SERVICES_INSTANCE = new NonCoreContracts();

	static public final MeterTypes METER_TYPES_INSTANCE = new MeterTypes();

	static public final MeterPaymentTypes MTC_PAYMENT_TYPES_INSTANCE = new MeterPaymentTypes();

	static public final ReadTypes READ_TYPES_INSTANCE = new ReadTypes();

	static public final Reports REPORTS_INSTANCE = new Reports();

	static public final Supplies SUPPLIES_INSTANCE = new Supplies();

	static public final Sites SITES_INSTANCE = new Sites();

	static public final GeneralImports GENERAL_IMPORT_PROCESSES = new GeneralImports();

	static public final GspGroups GSP_GROUPS_INSTANCE = new GspGroups();

	static public final UserRoles USER_ROLES_INSTANCE = new UserRoles();

	static public final SiteSnags SITE_SNAGS_INSTANCE = new SiteSnags();

	static public final GeneratorTypes GENERATOR_TYPES_INSTANCE = new GeneratorTypes();

	static {
		try {
			ROOT_URI = new MonadUri("/");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
		/*
		 * try { GOVERNMENT_INSTANCE = Government.getGovernment(); } catch
		 * (HttpException e) { throw new RuntimeException(e); }
		 */
	}

	public Chellow() {
		super();
		setTemplateDirName("");
		setRealmName("Chellow");
	}

	public void init(ServletConfig conf) throws ServletException {
		super.init(conf);
		ServletContext context = getServletContext();
		Properties mailProperties = new Properties();

		// setHibernateUtil(Hiber.getUtil());
		try {
			MonadContextParameters monadParameters = (MonadContextParameters) context
					.getAttribute("monadParameters");
			String mailHost = monadParameters.getMailHost();
			if (mailHost != null) {
				mailProperties.setProperty("mail.host", mailHost);
			}
		} catch (Throwable e) {
			logger.logp(Level.SEVERE, "net.sf.theelected.ui.Chellow", "init",
					"Can't initialize servlet.", e);
			throw new ServletException(e.getMessage());
		}
	}

	/**
	 * returns information about the servlet
	 */
	public String getServletInfo() {
		return "Chellow electricity billing and reporting.";
	}

	protected void checkPermissions(Invocation inv) throws HttpException {
		HttpMethod method = inv.getMethod();
		String pathInfo = inv.getRequest().getPathInfo();
		if (method.equals(HttpMethod.GET)
				&& (pathInfo.equals("/") || pathInfo.startsWith("/logo/") || pathInfo
						.startsWith("/style/"))) {
			return;
		}
		User user = inv.getUser();
		if (user == null) {
			user = ImplicitUserSource.getUser(inv);
		}
		if (user == null) {
			throw new UnauthorizedException();
		}
		UserRole role = user.getRole();
		String roleCode = role.getCode();
		if (roleCode.equals(UserRole.VIEWER)) {
			if (pathInfo.startsWith("/reports/")
					&& pathInfo.endsWith("/output/")
					&& (method.equals(HttpMethod.GET) || method
							.equals(HttpMethod.HEAD))) {
				return;
			}
		} else if (roleCode.equals(UserRole.EDITOR)) {
			return;
		} else if (roleCode.equals(UserRole.PARTY_VIEWER)) {
			if (method.equals(HttpMethod.GET) || method.equals(HttpMethod.HEAD)) {
				Party party = user.getParty();
				char marketRoleCode = party.getRole().getCode();
				if (marketRoleCode == MarketRole.HHDC) {
					Long hhdcContractId = inv.getLong("hhdc-contract-id");
					if (!inv.isValid()) {
						throw new ForbiddenException(
								"Need the parameter hhdc-contract-id.");
					}
					HhdcContract hhdcContract = HhdcContract
							.getHhdcContract(hhdcContractId);
					if (!hhdcContract.getParty().equals(party)) {
						throw new ForbiddenException(
								"The party associated with the contract you're trying to view doesn't match your party.");
					}
					if ((pathInfo + "?" + inv.getRequest().getQueryString())
							.equals("/reports/37/output/?hhdc-contract-id="
									+ hhdcContract.getId())) {
						return;
					}
				} else if (marketRoleCode == MarketRole.SUPPLIER) {
					if (pathInfo.startsWith("/supplier-contracts/"
							+ party.getId())) {
						return;
					}
				}
			}
		}
		if (inv.getUser() == null) {
			throw new UnauthorizedException();
		}
		throw new ForbiddenException();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk();
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Reports.URI_ID.equals(uriId)) {
			return REPORTS_INSTANCE;
		} else if (Sources.URI_ID.equals(uriId)) {
			return SOURCES_INSTANCE;
		} else if (Users.URI_ID.equals(uriId)) {
			return USERS_INSTANCE;
		} else if (NonCoreContracts.URI_ID.equals(uriId)) {
			return NON_CORE_SERVICES_INSTANCE;
		} else if (Pcs.URI_ID.equals(uriId)) {
			return PROFILE_CLASSES_INSTANCE;
		} else if (Mtcs.URI_ID.equals(uriId)) {
			return MTCS_INSTANCE;
		} else if (Tprs.URI_ID.equals(uriId)) {
			return TPRS_INSTANCE;
		} else if (Sscs.URI_ID.equals(uriId)) {
			return SSCS_INSTANCE;
		} else if (Participants.URI_ID.equals(uriId)) {
			return PARTICIPANTS_INSTANCE;
		} else if (MarketRoles.URI_ID.equals(uriId)) {
			return MARKET_ROLES_INSTANCE;
		} else if (MeterTypes.URI_ID.equals(uriId)) {
			return METER_TYPES_INSTANCE;
		} else if (MeterPaymentTypes.URI_ID.equals(uriId)) {
			return MTC_PAYMENT_TYPES_INSTANCE;
		} else if (Providers.URI_ID.equals(uriId)) {
			return PROVIDERS_INSTANCE;
		} else if (Dsos.URI_ID.equals(uriId)) {
			return DSOS_INSTANCE;
		} else if (ReadTypes.URI_ID.equals(uriId)) {
			return READ_TYPES_INSTANCE;
		} else if (Configuration.URI_ID.equals(uriId)) {
			return Configuration.getConfiguration();
		} else if (GeneralImports.URI_ID.equals(uriId)) {
			return GENERAL_IMPORT_PROCESSES;
		} else if (Sites.URI_ID.equals(uriId)) {
			return SITES_INSTANCE;
		} else if (HhdcContracts.URI_ID.equals(uriId)) {
			return HHDC_CONTRACTS_INSTANCE;
		} else if (SupplierContracts.URI_ID.equals(uriId)) {
			return SUPPLIER_CONTRACTS_INSTANCE;
		} else if (Supplies.URI_ID.equals(uriId)) {
			return SUPPLIES_INSTANCE;
		} else if (GspGroups.URI_ID.equals(uriId)) {
			return GSP_GROUPS_INSTANCE;
		} else if (UserRoles.URI_ID.equals(uriId)) {
			return USER_ROLES_INSTANCE;
		} else if (SiteSnags.URI_ID.equals(uriId)) {
			return SITE_SNAGS_INSTANCE;
		} else if (GeneratorTypes.URI_ID.equals(uriId)) {
			return GENERATOR_TYPES_INSTANCE;
		} else {
			return null;
		}
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
}
