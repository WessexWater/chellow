package net.sf.chellow.ui;

import java.util.Properties;
import java.util.logging.Level;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import net.sf.chellow.billing.Dsos;
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
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.MarketRoles;
import net.sf.chellow.physical.MeterPaymentTypes;
import net.sf.chellow.physical.MeterTypes;
import net.sf.chellow.physical.Mtcs;
import net.sf.chellow.physical.Participants;
import net.sf.chellow.physical.Pcs;
import net.sf.chellow.physical.ReadTypes;
import net.sf.chellow.physical.Sites;
import net.sf.chellow.physical.Sources;
import net.sf.chellow.physical.Sscs;
import net.sf.chellow.physical.Supplies;
import net.sf.chellow.physical.Tprs;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.Users;

public class Chellow extends Monad implements Urlable {
	private static final long serialVersionUID = 1L;

	// static private final HttpMethod[] ALLOWED_METHODS = { HttpMethod.GET };

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
		User user = inv.getUser();
		if (user == null) {
			user = ImplicitUserSource.getUser(inv);
		}
		if (user == null) {
			throw new UnauthorizedException();
		}
		int role = user.getRole();
		HttpMethod method = inv.getMethod();
		String pathInfo = inv.getRequest().getPathInfo();
		if (role == User.VIEWER) {
			if (method.equals(HttpMethod.GET) || method.equals(HttpMethod.HEAD)) {
				return;
			}
		} else if (role == User.EDITOR) {
			return;
		} else if (role == User.PARTY_VIEWER) {
			if (method.equals(HttpMethod.GET) || method.equals(HttpMethod.HEAD)) {
				Party party = user.getParty();
				char marketRoleCode = party.getRole().getCode();
				if (marketRoleCode == MarketRole.HHDC) {
					if (pathInfo.startsWith("/hhdc-contracts/" + party.getId())) {
						return;
					}
				} else if (marketRoleCode == MarketRole.SUPPLIER) {
					if (pathInfo.startsWith("/supplier-contracts/"
							+ party.getId())) {
						return;
					}
				}
			} else {
				return;
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
		if (Sources.URI_ID.equals(uriId)) {
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
		} else if (Reports.URI_ID.equals(uriId)) {
			return REPORTS_INSTANCE;
		} else if (Configuration.URI_ID.equals(uriId)) {
			return Configuration.getConfiguration();
		} else if (GeneralImports.URI_ID.equals(uriId)) {
			return GENERAL_IMPORT_PROCESSES;
		} else if (Sites.URI_ID.equals(uriId)) {
			return SITES_INSTANCE;
		} else {
			return null;
		}
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
}