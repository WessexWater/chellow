/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.Properties;
import java.util.logging.Level;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.billing.HhdcContracts;
import net.sf.chellow.billing.MopContracts;
import net.sf.chellow.billing.NonCoreContracts;
import net.sf.chellow.billing.Party;
import net.sf.chellow.billing.SupplierContracts;
import net.sf.chellow.monad.ForbiddenException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.UnauthorizedException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.GeneratorTypes;
import net.sf.chellow.physical.GspGroups;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.SiteSnags;
import net.sf.chellow.physical.Sites;
import net.sf.chellow.physical.Supplies;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.UserRole;
import net.sf.chellow.ui.GeneralImports;

public class Chellow extends Monad implements Urlable {
	private static final long serialVersionUID = 1L;

	static public final MonadUri ROOT_URI;

	static public final Reports REPORTS_INSTANCE = new Reports();

	static public final NonCoreContracts NON_CORE_CONTRACTS_INSTANCE = new NonCoreContracts();

	static public final GeneralImports GENERAL_IMPORTS_INSTANCE = new GeneralImports();

	static public final Supplies SUPPLIES_INSTANCE = new Supplies();

	static public final SiteSnags SITE_SNAGS_INSTANCE = new SiteSnags();

	static public final GeneratorTypes GENERATOR_TYPES_INSTANCE = new GeneratorTypes();

	static public final GspGroups GSP_GROUPS_INSTANCE = new GspGroups();

	static public final Sites SITES_INSTANCE = new Sites();

	static public final SupplierContracts SUPPLIER_CONTRACTS_INSTANCE = new SupplierContracts();

	static public final MopContracts MOP_CONTRACTS_INSTANCE = new MopContracts();

	static public final HhdcContracts HHDC_CONTRACTS_INSTANCE = new HhdcContracts();

	static {
		try {
			ROOT_URI = new MonadUri("/");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
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
				&& (pathInfo.equals("/")
						|| pathInfo.equals("/reports/1/output/") || pathInfo
							.startsWith("/reports/19/output/"))) {
			return;
		}
		User user = inv.getUser();
		if (user == null) {
			user = ImplicitUserSource.getUser(inv);
		}
		if (user == null) {
			try {
				Long userCount = (Long) Hiber.session()
						.createQuery("select count(*) from User user")
						.uniqueResult();
				if (userCount == null
						|| userCount == 0
						&& InetAddress.getByName(
								inv.getRequest().getRemoteAddr())
								.isLoopbackAddress()) {
					return;
				}
			} catch (UnknownHostException e) {
				throw new InternalException(e);
			}
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
					Contract hhdcContract = Contract
							.getHhdcContract(hhdcContractId);
					if (!hhdcContract.getParty().equals(party)) {
						throw new ForbiddenException(
								"The party associated with the contract you're trying to view doesn't match your party.");
					}
					if ((pathInfo + "?" + inv.getRequest().getQueryString())
							.startsWith("/reports/37/output/?hhdc-contract-id="
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
		inv.sendMovedPermanently("/reports/1/output/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Reports.URI_ID.equals(uriId)) {
			return REPORTS_INSTANCE;
		} else if (NonCoreContracts.URI_ID.equals(uriId)) {
			return NON_CORE_CONTRACTS_INSTANCE;
		} else if (GeneralImports.URI_ID.equals(uriId)) {
			return GENERAL_IMPORTS_INSTANCE;
		} else if (Supplies.URI_ID.equals(uriId)) {
			return SUPPLIES_INSTANCE;
		} else if (Sites.URI_ID.equals(uriId)) {
			return SITES_INSTANCE;
		} else if (SupplierContracts.URI_ID.equals(uriId)) {
			return SUPPLIER_CONTRACTS_INSTANCE;
		} else if (MopContracts.URI_ID.equals(uriId)) {
			return MOP_CONTRACTS_INSTANCE;
		} else if (HhdcContracts.URI_ID.equals(uriId)) {
			return HHDC_CONTRACTS_INSTANCE;
		} else if (SiteSnags.URI_ID.equals(uriId)) {
			return SITE_SNAGS_INSTANCE;
		} else if (Configuration.URI_ID.equals(uriId)) {
			return Configuration.getConfiguration();
		} else {
			return null;
		}
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	@Override
	public java.net.URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
