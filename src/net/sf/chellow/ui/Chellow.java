package net.sf.chellow.ui;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.Properties;
import java.util.logging.Level;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;

import net.sf.chellow.billing.Dcses;
import net.sf.chellow.billing.Government;
import net.sf.chellow.billing.Mops;
import net.sf.chellow.monad.BadRequestException;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.ForbiddenException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadContextParameters;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UnauthorizedException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Dsos;
import net.sf.chellow.physical.MeterTimeswitches;
import net.sf.chellow.physical.Organizations;
import net.sf.chellow.physical.Permission;
import net.sf.chellow.physical.ProfileClasses;
import net.sf.chellow.physical.Role;
import net.sf.chellow.physical.Roles;
import net.sf.chellow.physical.Sources;
import net.sf.chellow.physical.Sscs;
import net.sf.chellow.physical.Tprs;
import net.sf.chellow.physical.User;
import net.sf.chellow.physical.Users;

public class Chellow extends Monad implements Urlable {
	private static final long serialVersionUID = 1L;

	static private final HttpMethod[] ALLOWED_METHODS = { HttpMethod.GET };

	// static public final Roles REPORTS_INSTANCE = new Reports();
	static public final Roles ROLES_INSTANCE = new Roles();

	static public final Sources SOURCES_INSTANCE = new Sources();

	static public final Users USERS_INSTANCE = new Users();

	static public final Dsos DSOS_INSTANCE = new Dsos();

	static public final Mops MOPS_INSTANCE = new Mops();

	static public final Dcses DCSS_INSTANCE = new Dcses();

	static public final ProfileClasses PROFILE_CLASSES_INSTANCE = new ProfileClasses();

	static public final MeterTimeswitches METER_TIMESWITCHES_INSTANCE = new MeterTimeswitches();
	static public final Tprs TPRS_INSTANCE = new Tprs();
	static public final Sscs SSCS_INSTANCE = new Sscs();

	public static final Organizations ORGANIZATIONS_INSTANCE = new Organizations();

	public static final Government GOVERNMENT_INSTANCE;

	static {
		try {
			GOVERNMENT_INSTANCE = Government.getGovernment();
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
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
			throws HttpException, InternalException {
		try {
			return methodAllowed(user, new URI(inv.getRequest().getPathInfo()),
					inv.getMethod());
		} catch (URISyntaxException e) {
			throw new BadRequestException();
		}
	}

	public static boolean methodAllowed(User user, URI uri, HttpMethod method) {
		if (user.getId().equals(new Long(1))) {
			return true;
		}
		String longestUriPattern = null;
		boolean methodAllowed = false;
		String uriPath = uri.getPath().toString();
		for (Role role : user.getRoles()) {
			for (Permission permission : role.getPermissions()) {
				String uriPattern = permission.getUriPattern().toString();
				if (uriPath.startsWith(uriPattern)
						&& (longestUriPattern == null ? true : uriPattern
								.length() > longestUriPattern.length())) {
					methodAllowed = permission.isMethodAllowed(method);
					longestUriPattern = uriPattern;
				}
			}
		}
		return methodAllowed;
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

	/*
	 * public void service(HttpServletRequest req, HttpServletResponse res)
	 * throws IOException, ServletException { Debug.print("Doing service
	 * method."); super.service(req, res); Invocation inv = null;
	 * Debug.print("Doing service method 2."); try { try { inv = new
	 * Invocation(req, res, this); Debug.print("Trying to find urlable.");
	 * Urlable urlable = inv.dereferenceUrl(); Debug.print("Found urlable."); if
	 * (urlable == null) { Debug.print("urlable is null");
	 * StaticServlet.process(req.getPathInfo(),
	 * getServletConfig().getServletContext(), req, res); } String method =
	 * req.getMethod(); if (method.equals("GET")) { urlable.httpGet(inv); } else
	 * if (method.equals("POST")) { urlable.httpPost(inv); } else if
	 * (method.equals("DELETE")) { urlable.httpDelete(inv); } } catch
	 * (UserException e) { res.setHeader("WWW-Authenticate", "Basic realm=\"" +
	 * getRealmName() + "\""); try {
	 * res.sendError(HttpServletResponse.SC_UNAUTHORIZED); } catch (IOException
	 * e) { throw new ProgrammerException(e); } inv.sendOk(e.getDocument(),
	 * e.getTemplateName()); } } catch (Throwable e) { try { new
	 * InternetAddress("tlocke@tlocke.org.uk"); } catch (AddressException ae) { }
	 * logger.logp(Level.SEVERE, "uk.org.tlocke.monad.Monad", "service", "Can't
	 * process request", e); res .sendError(
	 * HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "There has been an error
	 * with our software. The " + "administrator has been informed, and the
	 * problem will " + "be put right as soon as possible."); } finally {
	 * Hiber.getUtil().rollbackTransaction(); Hiber.getUtil().closeSession(); } }
	 */
	/*
	 * public void updateSupply(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } Supply
	 * supply = Supply.getSupply(id); SupplyName name =
	 * inv.getValidatable(SupplyName.class, "name"); MonadLong sourceId =
	 * inv.getMonadLong("sourceId"); if (!inv.isValid()) { throw new
	 * UserException(getSupplyDocument(supply), "supply"); } try {
	 * supply.update(name, Source.getSource(sourceId)); } catch
	 * (InvalidArgumentException e) { throw new
	 * UserException(getSupplyDocument(supply), e.getVFMessage(), "supply"); }
	 * Hiber.close(); inv.seeOther("/editor/showSupply?id=" + id); }
	 */

	/*
	 * public void updateSource(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } Source
	 * source = Source.getSource(id); SourceCode code =
	 * inv.getValidatable(SourceCode.class, "code"); SourceName name =
	 * inv.getValidatable(SourceName.class, "name"); if (!inv.isValid()) { throw
	 * UserException.newOk(doc, "source"); } source.update(code, name);
	 * Hiber.commit(); sourceElement.appendChild(source.toXML(doc));
	 * returnPage(inv, doc, "source"); }
	 */

	/*
	 * public void updateSupplier(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); }
	 * Supplier supplier = Supplier.getSupplier(id); MonadString name =
	 * inv.getMonadString("name"); if (!inv.isValid()) { throw new
	 * UserException(doc, "supplier"); } supplier.setName(name); Hiber.flush();
	 * sourceElement.appendChild(supplier.toXML(doc)); returnPage(inv, doc,
	 * "supplier"); Hiber.close(); }
	 */
	/*
	 * public void updateContract(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); }
	 * Contract contract = Contract.getContract(id); ContractName name =
	 * inv.getValidatable(ContractName.class, "name"); ContractFrequency
	 * frequency = inv.getValidatable( ContractFrequency.class, "frequency");
	 * MonadInteger lag = inv.getMonadInteger("lag"); if (!inv.isValid()) {
	 * throw UserException.newOk(doc, "supplier"); } contract.update(name,
	 * frequency, lag); source.appendChild(new VFMessage("Contract updated
	 * successfully.") .toXML(doc)); source.appendChild(contract.getXML(new
	 * XMLTree("supplier"), doc)); returnPage(inv, doc, "contract");
	 * Hiber.close(); }
	 */
	/*
	 * public void updateSupplyGeneration(Invocation inv) throws
	 * DesignerException, ProgrammerException, UserException, DeployerException {
	 * Document doc = MonadUtilsUI.newSourceDocument(); MonadLong id =
	 * inv.getMonadLong("id"); if (!inv.isValid()) { throw new
	 * UserException(doc, "supplyGeneration"); } SupplyGeneration generation =
	 * SupplyGeneration.getSupplyGeneration(id); MeterTimeswitch
	 * importMeterTimeswitch = null; LineLossFactor importLineLossFactor = null;
	 * MpanCore importMpanCore = null; HhdceChannels importHhdceChannels = null;
	 * MonadInteger importAgreedSupplyCapacity = null; MonadBoolean
	 * hasImportMpan = inv.getMonadBoolean("hasImportMpan"); if
	 * (hasImportMpan.getBoolean()) { MonadLong importMpanCoreId =
	 * inv.getMonadLong("importMpanCoreId"); importMpanCore =
	 * MpanCore.getMpanCore(importMpanCoreId); MonadLong importProfileClassId =
	 * inv .getMonadLong("importProfileClassId"); ProfileClass
	 * importProfileClass = ProfileClass .getProfileClass(importProfileClassId);
	 * LineLossFactorCode importLineLossFactorCode = inv.getValidatable(
	 * LineLossFactorCode.class, "importLineLossFactorCode");
	 * importLineLossFactor = LineLossFactor.getLineLossFactor(
	 * importMpanCore.getDso(), importProfileClass, importLineLossFactorCode);
	 * MeterTimeswitchCode importMeterTimeswitchCode = inv.getValidatable(
	 * MeterTimeswitchCode.class, "importMeterTimeswitchCode");
	 * importMeterTimeswitch = MeterTimeswitch.getMeterTimeswitch(
	 * importMpanCore.getDso(), importProfileClass, importMeterTimeswitchCode);
	 * importAgreedSupplyCapacity = inv
	 * .getMonadInteger("importAgreedSupplyCapacity"); MonadBoolean
	 * importIsImportKwh = inv .getMonadBoolean("importIsImportKwh");
	 * MonadBoolean importIsImportKvarh = inv
	 * .getMonadBoolean("importIsImportKvarh"); MonadBoolean importIsExportKwh =
	 * inv .getMonadBoolean("importIsExportKwh"); MonadBoolean
	 * importIsExportKvarh = inv .getMonadBoolean("importIsExportKvarh");
	 * Contract importContract = null; if (importIsImportKwh.getBoolean() ||
	 * importIsImportKvarh.getBoolean() || importIsExportKwh.getBoolean() ||
	 * importIsExportKvarh.getBoolean()) { importContract =
	 * Contract.getContract(inv .getMonadLong("importContractId")); }
	 * importHhdceChannels = HhdceChannels.getHhdceChannels( importContract,
	 * importIsImportKwh, importIsImportKvarh, importIsExportKwh,
	 * importIsExportKvarh); } MeterTimeswitch exportMeterTimeswitch = null;
	 * LineLossFactor exportLineLossFactor = null; MpanCore exportMpanCore =
	 * null; HhdceChannels exportHhdceChannels = null; MonadInteger
	 * exportAgreedSupplyCapacity = null; MonadBoolean hasExportMpan =
	 * inv.getMonadBoolean("hasExportMpan"); if (hasExportMpan.getBoolean()) {
	 * MonadLong exportMpanCoreId = inv.getMonadLong("exportMpanCoreId");
	 * exportMpanCore = MpanCore.getMpanCore(exportMpanCoreId); MonadLong
	 * exportProfileClassId = inv .getMonadLong("exportProfileClassId");
	 * ProfileClass exportProfileClass = ProfileClass
	 * .getProfileClass(exportProfileClassId); LineLossFactorCode
	 * exportLineLossFactorCode = inv.getValidatable( LineLossFactorCode.class,
	 * "exportLineLossFactorId"); importLineLossFactor =
	 * LineLossFactor.getLineLossFactor( exportMpanCore.getDso(),
	 * exportProfileClass, exportLineLossFactorCode); MeterTimeswitchCode
	 * exportMeterTimeswitchCode = inv.getValidatable(
	 * MeterTimeswitchCode.class, "exportMeterTimeswitchCode");
	 * exportMeterTimeswitch = MeterTimeswitch.getMeterTimeswitch(
	 * exportMpanCore.getDso(), exportProfileClass, exportMeterTimeswitchCode);
	 * exportAgreedSupplyCapacity = inv
	 * .getMonadInteger("exportAgreedSupplyCapacity"); MonadBoolean
	 * exportIsImportKwh = inv .getMonadBoolean("exportIsImportKwh");
	 * MonadBoolean exportIsImportKvarh = inv
	 * .getMonadBoolean("exportIsImportKvarh"); MonadBoolean exportIsExportKwh =
	 * inv .getMonadBoolean("exportIsExportKwh"); MonadBoolean
	 * exportIsExportKvarh = inv .getMonadBoolean("exportIsExportKvarh");
	 * Contract exportContract = null; if (exportIsImportKwh.getBoolean() ||
	 * exportIsImportKvarh.getBoolean() || exportIsExportKwh.getBoolean() ||
	 * exportIsExportKvarh.getBoolean()) { exportContract =
	 * Contract.getContract(inv .getMonadLong("exportContractId")); }
	 * exportHhdceChannels = HhdceChannels.getHhdceChannels( exportContract,
	 * exportIsImportKwh, exportIsImportKvarh, exportIsExportKwh,
	 * exportIsExportKvarh); }
	 * generation.addOrUpdateMpans(importMeterTimeswitch, importLineLossFactor,
	 * importMpanCore, importHhdceChannels, importAgreedSupplyCapacity,
	 * exportMeterTimeswitch, exportLineLossFactor, exportMpanCore,
	 * exportHhdceChannels, exportAgreedSupplyCapacity);
	 * inv.seeOther("/editor/showSupplyGeneration?id=" + id.getLong());
	 * Hiber.close(); }
	 */
	/*
	 * public void showSite(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Site site =
	 * Site.getSite(id); source.appendChild(site.getXML(new
	 * XMLTree("suppliesByStartDate", new XMLTree("generationLast", new
	 * XMLTree("mpans", new XMLTree( "mpanCore"))).put("source")), doc));
	 * returnPage(inv, doc, "site"); }
	 */
	/*
	 * public void showHhData(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id"); MonadBoolean
	 * hasHhFinishDate = inv.getMonadBoolean("hasHhFinishDate");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Supply
	 * supply = Supply.getSupply(id); Element supplyElement = (Element)
	 * supply.getXML(new XMLTree( "siteSupplies", new
	 * XMLTree("site")).put("source").put( "generations", new XMLTree("mpans",
	 * new XMLTree("mpanCore"))), doc); source.appendChild(supplyElement);
	 * addSourcesXML(source); source.appendChild(MonadDate.getMonthsXML(doc));
	 * source.appendChild(MonadDate.getDaysXML(doc)); source.appendChild(new
	 * MonadDate().toXML(doc)); MonadDate hhFinishDate; if
	 * (hasHhFinishDate.getBoolean().booleanValue()) { hhFinishDate =
	 * inv.getMonadDate("hhFinishDate"); } else { hhFinishDate = new
	 * MonadDate(); } for (Channel channel : supply.getChannels()) { Element
	 * channelElement = (Element) channel.toXML(doc);
	 * supplyElement.appendChild(channelElement); for (HhDatum hhDatum :
	 * channel.getHhData(hhFinishDate)) {
	 * channelElement.appendChild(hhDatum.toXML(doc)); } } returnPage(inv, doc,
	 * "hhData"); }
	 */
	/*
	 * public void showInsertSupplyGeneration(Invocation inv) throws
	 * DesignerException, ProgrammerException, UserException, DeployerException {
	 * Document doc = MonadUtilsUI.newSourceDocument(); Element source =
	 * (Element) doc.getFirstChild(); MonadLong supplyId =
	 * inv.getMonadLong("supplyId");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Supply
	 * supply = Supply.getSupply(supplyId); Element supplyElement = (Element)
	 * supply.getXML(new XMLTree("sites") .put("source").put( "generations", new
	 * XMLTree("voltageLevel").put("mpans", new XMLTree( "mpan"))).put("mpans"),
	 * doc); source.appendChild(supplyElement); addSourcesXML(source);
	 * source.appendChild(MonadDate.getMonthsXML(doc));
	 * source.appendChild(MonadDate.getDaysXML(doc)); source.appendChild(new
	 * MonadDate().toXML(doc)); returnPage(inv, doc, "supplyGenerationInsert"); }
	 */
	/*
	 * public void showSupply(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Supply
	 * supply = Supply.getSupply(id); returnPage(inv, getSupplyDocument(supply),
	 * "supply"); }
	 */
	/*
	 * @SuppressWarnings("unchecked") public void
	 * showSupplyGeneration(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); }
	 * SupplyGeneration generation = SupplyGeneration.getSupplyGeneration(id);
	 * source.appendChild(generation.getXML(new XMLTree("supply", new XMLTree(
	 * "siteSupplies", new XMLTree("site")).put("source").put(
	 * "mpanCores")).put("mpans", new XMLTree("mpanCore").put(
	 * "meterTimeswitch").put("lineLossFactor").put("hhdceChannels", new
	 * XMLTree("contract"))), doc)); // addVoltageLevelsXML(source); for
	 * (Supplier supplier : (List<Supplier>) Hiber.session().createQuery( "from
	 * Supplier").list()) { source.appendChild(supplier.getXML(new
	 * XMLTree("contracts"), doc)); }
	 * source.appendChild(MonadDate.getMonthsXML(doc));
	 * source.appendChild(MonadDate.getDaysXML(doc)); source.appendChild(new
	 * MonadDate().toXML(doc)); for (ProfileClass profileClass :
	 * ProfileClass.findAll()) { source.appendChild(profileClass.toXML(doc)); }
	 * returnPage(inv, doc, "supplyGeneration"); }
	 */

	/*
	 * public void showSource(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Source
	 * source = Source.getSource(id);
	 * sourceElement.appendChild(source.toXML(doc)); returnPage(inv, doc,
	 * "source"); }
	 */
	/*
	 * @SuppressWarnings("unchecked") public void showSupplier(Invocation inv)
	 * throws DesignerException, ProgrammerException, UserException,
	 * DeployerException { Document doc = MonadUtilsUI.newSourceDocument();
	 * Element source = (Element) doc.getFirstChild(); MonadLong id =
	 * inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Supplier
	 * supplier = Supplier.getSupplier(id);
	 * source.appendChild(supplier.getXML(new XMLTree("contracts"), doc));
	 * returnPage(inv, doc, "supplier"); }
	 */
	/*
	 * public void showDso(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Dso dso =
	 * Dso.getDso(id); source.appendChild(dso.getXML(new
	 * XMLTree("lineLossFactors", new
	 * XMLTree("meterTimeswitches").put("profileClass")), doc)); returnPage(inv,
	 * doc, "dso"); }
	 */

	/*
	 * public void showContract(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Contract
	 * contract = Contract.getContract(id);
	 * source.appendChild(contract.getXML(new XMLTree("supplier"), doc));
	 * returnPage(inv, doc, "contract"); }
	 */
	/*
	 * public void showInsertSource(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument();
	 * 
	 * returnPage(inv, doc, "sourceInsert"); }
	 */
	/*
	 * public void insertSiteSupply(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { MonadLong
	 * supplyId = inv.getMonadLong("supplyId"); SiteCode siteCode =
	 * inv.getValidatable(SiteCode.class, "siteCode"); Supply supply =
	 * Supply.getSupply(supplyId); supply.addSiteSupply(Site.getSite(siteCode));
	 * inv.seeOther("/editor/showSupply?id=" + supply.getId()); Hiber.close(); }
	 */
	/*
	 * public void deleteSiteSupply(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { MonadLong
	 * siteSupplyId = inv.getMonadLong("siteSupplyId"); SiteSupply siteSupply =
	 * SiteSupply.getSiteSupply(siteSupplyId);
	 * siteSupply.getSupply().detachSiteSupply(siteSupply); Hiber.close();
	 * inv.seeOther("/editor/showSupply?id=" + siteSupply.getSupply().getId()); }
	 */
	/*
	 * public void showInsertSite(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument();
	 * 
	 * returnPage(inv, doc, "siteInsert"); }
	 */
	/*
	 * public void showInsertSupplier(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument();
	 * 
	 * returnPage(inv, doc, "supplierInsert"); } /* public void
	 * showInsertContract(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("supplierId");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); } Supplier
	 * supplier = Supplier.getSupplier(id);
	 * source.appendChild(supplier.toXML(doc)); returnPage(inv, doc,
	 * "contractInsert"); }
	 * 
	 * private void addVoltageLevelsXML(Element element) throws
	 * ProgrammerException, UserException { for (VoltageLevel voltageLevel :
	 * VoltageLevel.getVoltageLevels()) {
	 * element.appendChild(voltageLevel.toXML(element.getOwnerDocument())); } }
	 * 
	 * @SuppressWarnings("unchecked") public void showMpanCore(Invocation inv)
	 * throws DesignerException, ProgrammerException, UserException,
	 * DeployerException { Document doc = MonadUtilsUI.newSourceDocument();
	 * MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); }
	 * returnPage(inv, getShowMpanCoreDocument(MpanCore.getMpanCore(id)),
	 * "mpanCore"); } /* @SuppressWarnings("unchecked") public void
	 * showMpanGeneration(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "home"); }
	 * returnPage(inv, getShowMpanGenerationDocument(MpanGeneration
	 * .getMpanGeneration(id)), "mpanGeneration"); }
	 * 
	 * @SuppressWarnings("unchecked") private Document
	 * getShowMpanGenerationDocument(MpanGeneration mpanGeneration) throws
	 * ProgrammerException, UserException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild();
	 * 
	 * source.appendChild(mpanGeneration.getXML(new XMLTree("mpanCore").put(
	 * "supplyGeneration", new XMLTree("supply", new XMLTree("siteSupplies", new
	 * XMLTree( "site")).put("source").put("mpanCores")).put( "mpanGenerations",
	 * new XMLTree("mpanCore"))).put( "hhdceChannels", new XMLTree("contract",
	 * new XMLTree("supplier"))), doc)); for (MeterTimeswitch meterTimeswitch :
	 * mpanGeneration .getLineLossFactor().getMeterTimeswitches()) {
	 * source.appendChild(meterTimeswitch.toXML(doc)); } for (LineLossFactor
	 * lineLossFactor : mpanGeneration.getMpanCore()
	 * .getDso().getLineLossFactors(
	 * mpanGeneration.getLineLossFactor().getProfileClass())) {
	 * source.appendChild(lineLossFactor.toXML(doc)); } return doc; }
	 */
	/*
	 * @SuppressWarnings("unchecked") private Document
	 * getShowMpanCoreDocument(MpanCore mpanCore) throws ProgrammerException,
	 * UserException { Document doc = MonadUtilsUI.newSourceDocument(); Element
	 * source = (Element) doc.getFirstChild();
	 * 
	 * source.appendChild(mpanCore.getXML(new XMLTree("supply", new XMLTree(
	 * "siteSupplies", new XMLTree("site")).put("source")).put("dso"), doc));
	 * return doc; }
	 */
	/*
	 * @SuppressWarnings("unchecked") public void showSnags(Invocation inv)
	 * throws DesignerException, ProgrammerException, UserException,
	 * DeployerException { Document doc = MonadUtilsUI.newSourceDocument();
	 * Element source = (Element) doc.getFirstChild();
	 * 
	 * for (Contract contract : (List<Contract>) Hiber.session().createQuery(
	 * "select distinct snag.contract from Snag snag)").list()) {
	 * source.appendChild(contract.getXML(new XMLTree("supplier")
	 * .put("numberOfSnags"), doc)); } returnPage(inv, doc, "snags"); }
	 */
	/*
	 * private Document getSiteDocument(Site site) throws ProgrammerException,
	 * UserException { Document doc = MonadUtilsUI.newSourceDocument(); Element
	 * source = (Element) doc.getFirstChild();
	 * source.appendChild(site.toXML(doc)); return doc; }
	 */
	/*
	 * public void showImport(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { returnPage(inv,
	 * MonadUtilsUI.newSourceDocument(), "import"); }
	 */
	/*
	 * public void showHHImport(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { returnPage(inv,
	 * MonadUtilsUI.newSourceDocument(), "hhImport"); }
	 */

	/*
	 * public void siteSearchCode(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); SiteCode searchTerm =
	 * inv.getValidatable(SiteCode.class, "codeTerm");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } for
	 * (Site site : Site.getSites(searchTerm)) {
	 * source.appendChild(site.toXML(doc)); } returnPage(inv, doc, "sites"); }
	 */

	/*
	 * public void showSources(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild();
	 * 
	 * addSourcesXML(source); returnPage(inv, doc, "sources"); }
	 */

	/*
	 * public void showVoltageLevels(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild();
	 * 
	 * addVoltageLevelsXML(source); returnPage(inv, doc, "voltageLevels"); }
	 */
	/*
	 * public void showDsos(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild();
	 * 
	 * for (Dso dso : Dso.getDsos()) { source.appendChild(dso.toXML(doc)); }
	 * returnPage(inv, doc, "dsos"); }
	 */
	/*
	 * @SuppressWarnings("unchecked") public void showSuppliers(Invocation inv)
	 * throws DesignerException, ProgrammerException, UserException,
	 * DeployerException { Document doc = MonadUtilsUI.newSourceDocument();
	 * Element source = (Element) doc.getFirstChild();
	 * 
	 * addSuppliersXML(source); returnPage(inv, doc, "suppliers"); }
	 */
	/*
	 * public void siteSearch(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadString searchTerm =
	 * inv.getMonadString("searchTerm");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } for
	 * (Site site : Site.findSites(searchTerm)) {
	 * source.appendChild(site.toXML(doc)); } returnPage(inv, doc, "sites"); }
	 */

	/*
	 * public void mpanSearch(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MpanCoreTerm coreTerm =
	 * inv.getValidatable(MpanCoreTerm.class, "coreTerm");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } for
	 * (MpanCore mpan : MpanCore.getMpanCores(coreTerm)) {
	 * source.appendChild(mpan.getXML(new XMLTree("supply", new XMLTree(
	 * "siteSupplies", new XMLTree("site"))).put("dso"), doc)); }
	 * returnPage(inv, doc, "mpans"); }
	 */
	/*
	 * public void importHeaderCancel(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); HeaderImportThread importThread =
	 * (HeaderImportThread) inv.getRequest()
	 * .getSession().getAttribute(IMPORT_THREAD); if (importThread == null) {
	 * throw UserException .newOk("No header data is being imported at the
	 * moment."); } importThread.halt();
	 * inv.getRequest().getSession().setAttribute(IMPORT_THREAD, null);
	 * source.appendChild(new VFMessage("Import cancelled successfully.")
	 * .toXML(doc)); returnPage(inv, doc, "import"); }
	 */

	/*
	 * public void importHeader(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); final String IMPORT_THREAD = "importThread";
	 * HeaderImportThread importThread = (HeaderImportThread) inv.getRequest()
	 * .getSession().getAttribute(IMPORT_THREAD); if (importThread == null) {
	 * try { importThread = new HeaderImportThread(inv
	 * .getFileItem("importFile")); } catch (UserException e) {
	 * source.appendChild(e.getVFMessage().toXML(doc)); e.setDocument(doc);
	 * e.setTemplateName("import"); throw e; }
	 * inv.getRequest().getSession().setAttribute(IMPORT_THREAD, importThread);
	 * importThread.start(); } if (importThread.isAlive()) {
	 * source.setAttribute("progress", "Reached line number " +
	 * importThread.getLineNumber() + ".");
	 * inv.getResponse().setHeader("Refresh", "5"); returnPage(inv, doc,
	 * "importWait"); } else { ProgrammerException programmerException =
	 * importThread .getProgrammerException(); if (programmerException != null) {
	 * throw programmerException; } returnPage(inv, importThread.getDocument(),
	 * "import"); inv.getRequest().getSession().setAttribute(IMPORT_THREAD,
	 * null); } }
	 */
	/*
	 * public void hhImport(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); if
	 * (HhImportThread.buildHhImportDocument(inv, doc)) { returnPage(inv, doc,
	 * "hhImport"); } else { returnPage(inv, doc, "importWait"); } }
	 */
	/*
	 * public void confirmDeleteSite(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } Site
	 * site = Site.getSite(id);
	 * 
	 * source.appendChild(site.toXML(doc)); returnPage(inv, doc,
	 * "confirmDeleteSite"); }
	 */

	/*
	 * public void deleteSite(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } Site
	 * site = Site.getSite(id); Site.deleteSite(site); source.appendChild(new
	 * VFMessage("Site deleted successfully.") .toXML(doc)); returnPage(inv,
	 * doc, "home"); Hiber.close(); }
	 */
	/*
	 * public void deleteMpanGeneration(Invocation inv) throws
	 * DesignerException, ProgrammerException, UserException, DeployerException {
	 * Document doc = MonadUtilsUI.newSourceDocument(); MonadLong id =
	 * inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); }
	 * MpanGeneration generation = MpanGeneration.getMpanGeneration(id);
	 * SupplyGeneration supplyGeneration = generation.getSupplyGeneration();
	 * supplyGeneration.deleteMpanGeneration(generation);
	 * inv.seeOther("/editor/showSupplyGeneration?id=" +
	 * supplyGeneration.getId()); Hiber.close(); }
	 */
	/*
	 * public void confirmDeleteSource(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } Source
	 * source = Source.getSource(id);
	 * 
	 * sourceElement.appendChild(source.toXML(doc)); returnPage(inv, doc,
	 * "sourceConfirmDelete"); }
	 */
	/*
	 * public void confirmDeleteSupplier(Invocation inv) throws
	 * DesignerException, ProgrammerException, UserException, DeployerException {
	 * Document doc = MonadUtilsUI.newSourceDocument(); Element sourceElement =
	 * (Element) doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); }
	 * Supplier supplier = Supplier.getSupplier(id);
	 * 
	 * sourceElement.appendChild(supplier.toXML(doc)); returnPage(inv, doc,
	 * "supplierConfirmDelete"); }
	 */
	/*
	 * public void confirmDeleteSupply(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * sourceElement.appendChild(Supply.getSupply(id).toXML(doc));
	 * returnPage(inv, doc, "supplyConfirmDelete"); }
	 */
	/*
	 * public void deleteSupply(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); }
	 * Supply.deleteSupply(Supply.getSupply(id)); Hiber.close();
	 * inv.seeOther("mpanSearch?coreTerm="); }
	 */
	/*
	 * public void deleteSource(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); } Source
	 * source = Source.getSource(id); data.deleteSource(source);
	 * sourceElement.appendChild(new VFMessage("Source deleted successfully.")
	 * .toXML(doc)); addSourcesXML(sourceElement); returnPage(inv, doc,
	 * "sources"); }
	 */
	/*
	 * public void deleteSupplier(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); MonadLong id = inv.getMonadLong("id");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "message"); }
	 * Supplier supplier = Supplier.getSupplier(id);
	 * Supplier.deleteSupplier(supplier); sourceElement.appendChild(new
	 * VFMessage( "Supplier deleted successfully.").toXML(doc));
	 * addSuppliersXML(sourceElement); returnPage(inv, doc, "suppliers"); }
	 */
	/*
	 * public void insertSource(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element sourceElement = (Element)
	 * doc.getFirstChild(); SourceCode code =
	 * inv.getValidatable(SourceCode.class, "code"); SourceName name =
	 * inv.getValidatable(SourceName.class, "name"); if (!inv.isValid()) { throw
	 * UserException.newOk(doc, "sourceInsert"); }
	 * 
	 * try { Source.insertSource(code, name); } catch
	 * (MonadInstantiationException e) {
	 * sourceElement.appendChild(e.toXML(doc)); throw UserException.newOk(doc,
	 * "sourceInsert"); } sourceElement .appendChild(new VFMessage("Source
	 * inserted successfully.") .toXML(doc)); Hiber.commit();
	 * addSourcesXML(sourceElement); returnPage(inv, doc, "sources"); }
	 */
	/*
	 * public void insertSupplyGeneration(Invocation inv) throws
	 * DesignerException, ProgrammerException, UserException, DeployerException {
	 * MonadLong supplyId = inv.getMonadLong("supplyId"); MonadBoolean isOngoing =
	 * inv.getMonadBoolean("isOngoing"); HhEndDate finishDate = null; if
	 * (!isOngoing.getBoolean()) { finishDate =
	 * HhEndDate.roundDown(inv.getMonadDate("finishDate") .getDate()); } Supply
	 * supply = Supply.getSupply(supplyId); supply.addGeneration(finishDate);
	 * Hiber.commit(); inv.seeOther("/editor/showSupply?id=" + supplyId); }
	 */
	/*
	 * public void insertSite(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); SiteCode code =
	 * inv.getValidatable(SiteCode.class, "code");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "siteInsert"); } try {
	 * Site.insertSite(code); } catch (UserException e) {
	 * e.setTemplateName("siteInsert"); throw e; }
	 * inv.seeOther("/editor/siteSearch?searchTerm="); }
	 */
	/*
	 * public void insertSupplier(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); MonadString name =
	 * inv.getMonadString("name"); if (!inv.isValid()) { throw new
	 * UserException(doc, "sourceInsert"); } Supplier.insertSupplier(name);
	 * Hiber.close(); inv.seeOther("/editor/showSuppliers"); }
	 */
	/*
	 * public void insertMpanGeneration(Invocation inv) throws
	 * DesignerException, ProgrammerException, UserException, DeployerException {
	 * Document doc = MonadUtilsUI.newSourceDocument(); MonadLong
	 * supplyGenerationId = inv.getMonadLong("supplyGenerationId"); if
	 * (!inv.isValid()) { throw UserException.newOk(doc, "mpan"); }
	 * SupplyGeneration supplyGeneration = SupplyGeneration
	 * .getSupplyGeneration(supplyGenerationId); MonadLong mpanCoreId =
	 * inv.getMonadLong("mpanCoreId"); MpanCore mpanCore =
	 * MpanCore.getMpanCore(mpanCoreId); MonadInteger agreedSupplyCapacity =
	 * inv.getMonadInteger("agreedSupplyCapacity"); ProfileClassCode
	 * profileClassCode = (ProfileClassCode) inv
	 * .getValidatable(ProfileClassCode.class, "profileClassCode"); ProfileClass
	 * profileClass = ProfileClass .getProfileClass(profileClassCode);
	 * MeterTimeswitchCode meterTimeswitchCode = (MeterTimeswitchCode) inv
	 * .getValidatable(MeterTimeswitchCode.class, "meterTimeswitchCode");
	 * MeterTimeswitch meterTimeswitch = MeterTimeswitch.getMeterTimeswitch(
	 * mpanCore.getDso(), profileClass, meterTimeswitchCode); LineLossFactorCode
	 * lineLossFactorCode = (LineLossFactorCode) inv
	 * .getValidatable(LineLossFactorCode.class, "LineLossFactorCode");
	 * LineLossFactor lineLossFactor = LineLossFactor.getLineLossFactor(
	 * mpanCore.getDso(), profileClass, lineLossFactorCode); MonadBoolean
	 * isImportKwh = inv.getMonadBoolean("isImportKwh"); MonadBoolean
	 * isImportKvarh = inv.getMonadBoolean("isImportKvarh"); MonadBoolean
	 * isExportKwh = inv.getMonadBoolean("isExportKwh"); MonadBoolean
	 * isExportKvar = inv.getMonadBoolean("isExportKvar"); Contract contract =
	 * null; if (isImportKwh.getBoolean() || isImportKvarh.getBoolean() ||
	 * isExportKwh.getBoolean() || isExportKvar.getBoolean()) { contract =
	 * Contract.getContract(inv.getMonadLong("contractId")); }
	 * supplyGeneration.addOrUpdateMpanGeneration(meterTimeswitch,
	 * lineLossFactor, mpanCore, HhdceChannels.getHhdceChannels( contract,
	 * isImportKwh, isImportKvarh, isExportKwh, isExportKvar),
	 * agreedSupplyCapacity); inv.seeOther("/editor/showSupplyGeneration?id=" +
	 * supplyGeneration.getId()); Hiber.close(); }
	 */

	/*
	 * public void insertContract(Invocation inv) throws DesignerException,
	 * ProgrammerException, UserException, DeployerException { Document doc =
	 * MonadUtilsUI.newSourceDocument(); Element source = (Element)
	 * doc.getFirstChild(); MonadLong supplierId =
	 * inv.getMonadLong("supplierId");
	 * 
	 * if (!inv.isValid()) { throw UserException.newOk(doc, "contractInsert"); }
	 * ContractName name = inv.getValidatable(ContractName.class, "name");
	 * ContractFrequency frequency = inv.getValidatable(
	 * ContractFrequency.class, "frequency"); MonadInteger lag =
	 * inv.getMonadInteger("lag"); Supplier supplier =
	 * Supplier.getSupplier(supplierId); if (!inv.isValid()) {
	 * source.appendChild(supplier.getXML(new XMLTree("contracts"), doc)); throw
	 * UserException.newOk(doc, "contractInsert"); }
	 * supplier.insertContract(name, frequency, lag);
	 * inv.seeOther("/editor/showSupplier?id=" + supplier.getId());
	 * Hiber.close(); }
	 */

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		/*
		 * Configuration conf = new Configuration()
		 * .configure("hibernate/08/hibernate.cfg.xml"); SessionFactory
		 * sessionFactoryOne = conf.buildSessionFactory();
		 * 
		 * Session firstSession = sessionFactoryOne.openSession(); Transaction
		 * firstTransaction = firstSession.beginTransaction(); Source
		 * firstSource = (Source) firstSession.get(Source.class, 1L); try {
		 * firstSource.setCode(new SourceCode("kkkk")); } catch
		 * (MonadInstantiationException e) { // TODO Auto-generated catch block
		 * e.printStackTrace(); } //firstSession.delete(firstSource);
		 * firstSession.flush(); SessionFactory sessionFactoryTwo =
		 * conf.buildSessionFactory(); Session secondSession =
		 * sessionFactoryTwo.openSession(); Transaction secondTransaction =
		 * secondSession.beginTransaction();
		 * 
		 * Source secondSource = (Source) firstSession.get(Source.class, 1L);
		 * try { secondSource.setCode(new SourceCode("hellow")); } catch
		 * (MonadInstantiationException e) { // TODO Auto-generated catch block
		 * e.printStackTrace(); } secondTransaction.commit();
		 * secondSession.close();
		 * 
		 * try { firstSource.setCode(new SourceCode("kkkk")); } catch
		 * (MonadInstantiationException e) { // TODO Auto-generated catch block
		 * e.printStackTrace(); } firstTransaction.commit();
		 * firstSession.close();
		 */
		inv.sendOk();
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		inv.sendMethodNotAllowed(ALLOWED_METHODS);
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		if (Sources.URI_ID.equals(uriId)) {
			return SOURCES_INSTANCE;
		} else if (Organizations.URI_ID.equals(uriId)) {
			return ORGANIZATIONS_INSTANCE;
		} else if (Dsos.URI_ID.equals(uriId)) {
			return DSOS_INSTANCE;
		} else if (Users.URI_ID.equals(uriId)) {
			return USERS_INSTANCE;
		} else if (Roles.URI_ID.equals(uriId)) {
			return ROLES_INSTANCE;
		} else if (Government.URI_ID.equals(uriId)) {
			return GOVERNMENT_INSTANCE;
		} else if (ProfileClasses.URI_ID.equals(uriId)) {
			return PROFILE_CLASSES_INSTANCE;
		} else if (MeterTimeswitches.URI_ID.equals(uriId)) {
			return METER_TIMESWITCHES_INSTANCE;
		} else if (Tprs.URI_ID.equals(uriId)) {
			return TPRS_INSTANCE;
		} else if (Sscs.URI_ID.equals(uriId)) {
			return SSCS_INSTANCE;
		} else {
			return null;
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
}