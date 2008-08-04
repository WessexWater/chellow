package net.sf.chellow.ui;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Properties;
import java.util.logging.Level;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import net.sf.chellow.billing.Dsos;
import net.sf.chellow.billing.NonCoreServices;
import net.sf.chellow.billing.Providers;
import net.sf.chellow.monad.BadRequestException;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.ForbiddenException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.UnauthorizedException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.MarketRoles;
import net.sf.chellow.physical.MeterTypes;
import net.sf.chellow.physical.MeterPaymentTypes;
import net.sf.chellow.physical.Mtcs;
import net.sf.chellow.physical.Organizations;
import net.sf.chellow.physical.Participants;
import net.sf.chellow.physical.Pcs;
import net.sf.chellow.physical.Roles;
import net.sf.chellow.physical.Sources;
import net.sf.chellow.physical.Sscs;
import net.sf.chellow.physical.Tprs;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.Users;

public class Chellow extends Monad implements Urlable {
	private static final long serialVersionUID = 1L;

	static private final HttpMethod[] ALLOWED_METHODS = { HttpMethod.GET };

	static public final MonadUri ROOT_URI;
	static public final Roles ROLES_INSTANCE = new Roles();

	static public final Sources SOURCES_INSTANCE = new Sources();

	static public final Users USERS_INSTANCE = new Users();

	static public final Providers PROVIDERS_INSTANCE = new Providers();

	static public final Pcs PROFILE_CLASSES_INSTANCE = new Pcs();

	static public final Mtcs MTCS_INSTANCE = new Mtcs();
	static public final Tprs TPRS_INSTANCE = new Tprs();
	static public final Sscs SSCS_INSTANCE = new Sscs();

	public static final Organizations ORGANIZATIONS_INSTANCE = new Organizations();

	public static final Participants PARTICIPANTS_INSTANCE = new Participants();
	public static final MarketRoles MARKET_ROLES_INSTANCE = new MarketRoles();
	public static final Dsos DSOS_INSTANCE = new Dsos();
	public static final NonCoreServices NON_CORE_SERVICES_INSTANCE = new NonCoreServices();
	static public final MeterTypes METER_TYPES_INSTANCE = new MeterTypes();
	static public final MeterPaymentTypes MTC_PAYMENT_TYPES_INSTANCE = new MeterPaymentTypes();

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
		Monad.setConfigDir(ChellowConfiguration.getConfigurationDirectory());
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

	private boolean requestAllowed(User user, Invocation inv)
			throws HttpException {
		try {
			return user.methodAllowed(new URI(inv.getRequest().getPathInfo()),
					inv.getMethod());
		} catch (URISyntaxException e) {
			throw new BadRequestException();
		}
	}

	protected void checkPermissions(Invocation inv) throws HttpException,
			InternalException {
		User user = ImplicitUserSource.getUser(inv);
		if (requestAllowed(user, inv)) {
			return;
		}
		user = inv.getUser();
		if (user == null) {
			throw new UnauthorizedException();
		}
		if (requestAllowed(user, inv)) {
			return;
		}
		throw new ForbiddenException();
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk();
	}

	public void httpPost(Invocation inv) throws HttpException {
		inv.sendMethodNotAllowed(ALLOWED_METHODS);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Sources.URI_ID.equals(uriId)) {
			return SOURCES_INSTANCE;
		} else if (Organizations.URI_ID.equals(uriId)) {
			return ORGANIZATIONS_INSTANCE;
		} else if (Users.URI_ID.equals(uriId)) {
			return USERS_INSTANCE;
		} else if (Roles.URI_ID.equals(uriId)) {
			return ROLES_INSTANCE;
		} else if (NonCoreServices.URI_ID.equals(uriId)) {
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
		} else {
			return null;
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
}