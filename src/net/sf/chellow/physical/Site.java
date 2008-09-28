/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.physical;

import java.sql.BatchUpdateException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Site extends PersistentEntity {
	static public Site insertSite(String code, String name)
			throws HttpException {
		Site site = null;
		try {
			site = new Site(code, name);
			Hiber.session().save(site);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException("A site with this code already exists.");
		}
		return site;
	}

	static public Site getSite(Long id) throws HttpException {
		Site site = (Site) Hiber.session().get(Site.class, id);
		if (site == null) {
			throw new NotFoundException("There isn't a site with the id " + id
					+ ".");
		}
		return site;
	}

	static public Site findSite(String siteCode) throws HttpException {
		return (Site) Hiber.session().createQuery(
				"from Site as site where site.code = :siteCode").setString(
				"siteCode", siteCode).uniqueResult();
	}

	static public Site getSite(String code) throws HttpException {
		Site site = findSite(code);
		if (site == null) {
			throw new NotFoundException("The site '" + code
					+ "' cannot be found.");
		}
		return site;
	}

	@SuppressWarnings("unchecked")
	static public void deleteSite(Site site) throws HttpException {
		if (Hiber.session().createQuery(
				"from SiteSupplyGeneration ssg where ssg.site = :site")
				.setEntity("site", site).list().size() > 0) {
			throw new UserException(
					"This site can't be deleted while there are still supply generations attached to it.");
		}
		for (SiteSnag snag : (List<SiteSnag>) Hiber.session().createQuery(
				"from SiteSnag snag where site = :site")
				.setEntity("site", site).list()) {
			snag.delete();
		}
		Hiber.session().delete(site);
		Hiber.flush();
	}

	private String code;

	private String name;

	private Set<SiteSupplyGeneration> siteSupplyGenerations;

	public Site() {
	}

	public Site(String code, String name) throws HttpException {
		update(code, name);
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public Set<SiteSupplyGeneration> getSiteSupplyGenerations() {
		return siteSupplyGenerations;
	}

	protected void setSiteSupplyGenerations(
			Set<SiteSupplyGeneration> siteSupplyGenerations) {
		this.siteSupplyGenerations = siteSupplyGenerations;
	}

	public void update(String code, String name) throws HttpException {
		setCode(code);
		MonadString.update("name", name, true, 200, 0,
				Character.UnicodeBlock.BASIC_LATIN, false);
		setName(name);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "site");

		element.setAttribute("name", name);
		element.setAttribute("code", code);
		return element;
	}

	public Supply insertSupply(String supplyName, String meterSerialNumber,
			String importMpanStr, String importSscCode,
			String importHhdcContractName, String importHhdcAccountReference,
			String importSupplierContractName,
			String importSupplierAccountReference,
			String importAgreedSupplyCapacityStr, String exportMpanStr,
			String exportSscCode, String exportHhdcContractName,
			String exportHhdcAccountReference,
			String exportSupplierContractName,
			String exportSupplierAccountReference,
			String exportAgreedSupplyCapacityStr, HhEndDate startDate,
			String sourceCode) throws HttpException {
		Integer importAgreedSupplyCapacity = null;
		HhdcContract importHhdcContract = null;
		Account importHhdcAccount = null;
		SupplierContract importSupplierContract = null;
		Account importSupplierAccount = null;
		Ssc importSsc = null;

		if (importMpanStr != null && importMpanStr.length() != 0) {
			importSsc = importSscCode.trim().length() == 0 ? null : Ssc
					.getSsc(importSscCode);
			try {
				importAgreedSupplyCapacity = new Integer(
						importAgreedSupplyCapacityStr);
			} catch (NumberFormatException e) {
				throw new UserException(
						"The import supply capacity must be an integer."
								+ e.getMessage());
			}
			importHhdcContract = importHhdcContractName.trim().length() == 0 ? null
					: HhdcContract.getHhdcContract(importHhdcContractName);
			if (importHhdcContract != null) {
				importHhdcAccount = importHhdcContract
						.getAccount(importHhdcAccountReference);
			}
			importSupplierContract = SupplierContract
					.getSupplierContract(importSupplierContractName);
			importSupplierAccount = importSupplierContract
					.getAccount(importSupplierAccountReference);
		}
		HhdcContract exportHhdcContract = null;
		Account exportHhdcAccount = null;
		SupplierContract exportSupplierContract = null;
		Account exportAccountSupplier = null;
		Integer exportAgreedSupplyCapacity = null;
		Ssc exportSsc = null;
		if (exportMpanStr != null && exportMpanStr.length() != 0) {
			exportSsc = exportSscCode.trim().length() == 0 ? null : Ssc
					.getSsc(exportSscCode);
			try {
				exportAgreedSupplyCapacity = new Integer(
						exportAgreedSupplyCapacityStr);
			} catch (NumberFormatException e) {
				throw new UserException(
						"The export agreed supply capacity must be an integer."
								+ e.getMessage());
			}
			exportHhdcContract = exportHhdcContractName.length() == 0 ? null
					: HhdcContract.getHhdcContract(exportHhdcContractName);
			if (exportHhdcContract != null) {
				exportHhdcAccount = exportHhdcContract
						.getAccount(exportHhdcAccountReference);
			}
			exportSupplierContract = SupplierContract
					.getSupplierContract(exportSupplierContractName);
			exportAccountSupplier = exportSupplierContract
					.getAccount(exportSupplierAccountReference);
		}
		return insertSupply(supplyName, meterSerialNumber, importMpanStr,
				importSsc, importHhdcAccount, importSupplierAccount,
				importHhdcAccount == null ? false : true,
				importHhdcAccount == null ? false : true, false,
				importHhdcAccount == null ? false : true,
				importAgreedSupplyCapacity, exportMpanStr, exportSsc,
				exportHhdcAccount, exportAccountSupplier, false,
				exportHhdcAccount == null ? false : true,
				exportHhdcAccount == null ? false : true,
				exportHhdcAccount == null ? false : true,
				exportAgreedSupplyCapacity, startDate, sourceCode);
	}

	public Supply insertSupply(String supplyName, String meterSerialNumber,
			String importMpanStr, Ssc importSsc, Account importHhdcAccount,
			Account importAccountSupplier, boolean importHasImportKwh,
			boolean importHasImportKvarh, boolean importHasExportKwh,
			boolean importHasExportKvarh, Integer importAgreedSupplyCapacity,
			String exportMpanStr, Ssc exportSsc, Account exportHhdcAccount,
			Account exportAccountSupplier, boolean exportHasImportKwh,
			boolean exportHasImportKvarh, boolean exportHasExportKwh,
			boolean exportHasExportKvarh, Integer exportAgreedSupplyCapacity,
			HhEndDate startDate, String sourceCode) throws HttpException {
		Source source = Source.getSource(sourceCode);
		Supply supply = new Supply(supplyName, source);
		try {
			// supply.setId(id);
			Hiber.session().save(supply);
			Hiber.flush();
		} catch (HibernateException e) {
			Hiber.rollBack();
			if (HttpException
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"mpan_dso_id_key\"")) {
				BatchUpdateException be = (BatchUpdateException) e.getCause();
				String message = be.getMessage();
				boolean isImport = message.charAt(message.lastIndexOf(',') - 1) == '0';
				throw new UserException("An MPAN with this "
						+ (isImport ? "import" : "export")
						+ " MPAN core already exists.");
			} else {
				throw new InternalException(e);
			}
		}
		/*
		if (importMpanRaw != null) {
			supply.addMpanCore(importMpanRaw.getMpanCoreRaw());
		}
		if (exportMpanRaw != null) {
			supply.addMpanCore(exportMpanRaw.getMpanCoreRaw());
		}
		*/
		Map<Site, Boolean> siteMap = new HashMap<Site, Boolean>();
		siteMap.put(this, true);
		Meter meter = null;
		if (meterSerialNumber != null && meterSerialNumber.length() != 0) {
			meter = supply.findMeter(meterSerialNumber);
			if (meter == null) {
				meter = supply.insertMeter(meterSerialNumber);
			}
		}
		SupplyGeneration supplyGeneration = supply.addGeneration(siteMap,
				meter, importMpanStr, importSsc, importHhdcAccount,
				importAccountSupplier, importHasImportKwh,
				importHasImportKvarh, importHasExportKwh, importHasExportKvarh,
				importAgreedSupplyCapacity, exportMpanStr, exportSsc,
				exportHhdcAccount, exportAccountSupplier, exportHasImportKwh,
				exportHasImportKvarh, exportHasExportKwh, exportHasExportKvarh,
				exportAgreedSupplyCapacity, null);
		supplyGeneration.update(startDate, supplyGeneration.getFinishDate(),
				meter);
		Hiber.flush();
		return supply;
	}

	public void hhCheck(HhEndDate from, HhEndDate to) throws HttpException {
		// Calendar cal = GregorianCalendar.getInstance(TimeZone
		// .getTimeZone("GMT"), Locale.UK);
		for (SiteGroup group : groups(from, to, false)) {
			// long now = System.currentTimeMillis();
			// Debug.print("About to go checking: "
			// + (System.currentTimeMillis() - now));
			Map<String, List<Float>> map = group.hhData();

			List<Float> importFromNet = map.get("import-from-net");
			List<Float> exportToNet = map.get("export-to-net");
			List<Float> importFromGen = map.get("import-from-gen");
			List<Float> exportToGen = map.get("export-to-gen");
			// Debug.print("Got to vague midpoint. "
			// + (System.currentTimeMillis() - now));
			HhEndDate resolve1From = null;
			HhEndDate resolve1To = null;
			HhEndDate snag1From = null;
			HhEndDate snag1To = null;
			HhEndDate resolve2From = null;
			HhEndDate resolve2To = null;
			HhEndDate snag2From = null;
			HhEndDate snag2To = null;
			int i = 0;
			HhEndDate hhEndDate = group.getFrom();
			HhEndDate previousEndDate = null;
			// cal.clear();
			// cal.setTime(hhEndDate.getDate());
			// cal.set(Calendar.DAY_OF_MONTH, 1);
			// cal.set(Calendar.HOUR_OF_DAY, 0);
			// cal.set(Calendar.MINUTE, 0);
			// cal.set(Calendar.SECOND, 0);
			// cal.set(Calendar.MILLISECOND, 0);
			// DceService previousDceService = getDceService(new HhEndDate(cal
			// .getTime()));
			// DceService dceService = previousDceService;
			// int month = cal.get(Calendar.MONTH);
			while (!hhEndDate.getDate().after(group.getTo().getDate())) {
				// cal.clear();
				// cal.setTime(hhEndDate.getDate());
				// if (month != cal.get(Calendar.MONTH)) {
				// month = cal.get(Calendar.MONTH);
				// previousDceService = dceService;
				// dceService = getDceService(new HhEndDate(cal.getTime()));
				// }
				if (exportToNet.get(i) > importFromGen.get(i)) {
					if (snag1From == null) {
						snag1From = hhEndDate;
					}
					snag1To = hhEndDate;
				} else {
					if (resolve1From == null) {
						resolve1From = hhEndDate;
					}
					resolve1To = hhEndDate;
				}
				if (snag1To != null && (snag1To.equals(previousEndDate))) {
					group.addHhdcSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
							snag1From, snag1To, false);
					snag1From = null;
					snag1To = null;
				}
				if (resolve1To != null && resolve1To.equals(previousEndDate)) {
					group.resolveHhdcSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
							resolve1From, resolve1To);
					resolve1From = null;
					resolve1To = null;
				}
				if (exportToGen.get(i) > importFromNet.get(i)
						+ importFromGen.get(i)) {
					if (snag2From == null) {
						snag2From = hhEndDate;
					}
					snag2To = hhEndDate;
				} else {
					if (resolve2From == null) {
						resolve2From = hhEndDate;
					}
					resolve2To = hhEndDate;
				}
				if (snag2To != null && snag2To.equals(previousEndDate)) {
					group.addHhdcSnag(SiteGroup.EXPORT_GEN_GT_IMPORT,
							snag2From, snag2To, false);
					snag2From = null;
					snag2To = null;
				}
				if (resolve2To != null && resolve2To.equals(previousEndDate)) {
					group.resolveHhdcSnag(SiteGroup.EXPORT_GEN_GT_IMPORT,
							resolve2From, resolve2To);
					resolve2From = null;
					resolve2To = null;
				}
				i++;
				previousEndDate = hhEndDate;
				hhEndDate = hhEndDate.getNext();
			}
			if (snag1To != null && snag1To.equals(previousEndDate)) {
				group.addHhdcSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
						snag1From, snag1To, false);
			}
			if (resolve1To != null && resolve1To.equals(previousEndDate)) {
				group.resolveHhdcSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
						resolve1From, resolve1To);
			}
			if (snag2To != null && snag2To.equals(previousEndDate)) {
				group.addHhdcSnag(SiteGroup.EXPORT_GEN_GT_IMPORT, snag2From,
						snag2To, false);
			}
			if (resolve2To != null && resolve2To.equals(previousEndDate)) {
				group.resolveHhdcSnag(SiteGroup.EXPORT_GEN_GT_IMPORT,
						resolve2From, resolve2To);
			}
		}
	}

	public List<SiteGroup> groups(HhEndDate from, HhEndDate to,
			boolean primaryOnly) throws HttpException {
		List<SiteGroup> groups = new ArrayList<SiteGroup>();
		HhEndDate checkFrom = from;
		HhEndDate checkTo = to;
		while (!checkFrom.getDate().after(to.getDate())) {
			List<Site> sites = new ArrayList<Site>();
			List<Supply> supplies = new ArrayList<Supply>();
			sites.add(this);
			if (walkGroup(sites, supplies, checkFrom, checkTo)) {
				Collections.sort(sites, new Comparator<Site>() {
					public int compare(Site site1, Site site2) {
						int physicalSupplies1 = site1.physicalSupplies();
						int physicalSupplies2 = site2.physicalSupplies();
						return physicalSupplies1 == physicalSupplies2 ? site2
								.getCode().compareTo(site1.getCode())
								: physicalSupplies2 - physicalSupplies1;
					}
				});
				if (!primaryOnly || sites.get(0).equals(this)) {
					groups.add(new SiteGroup(checkFrom, checkTo, sites,
							supplies));
				}
				checkFrom = checkTo.getNext();
				checkTo = to;
			} else {
				checkTo = HhEndDate
						.roundDown(new Date(
								(long) Math.floor(((double) (checkTo.getDate()
										.getTime() - checkFrom.getDate()
										.getTime())) / 2)));
			}
		}
		return groups;
	}

	// return true if the supply is continuously attached to the site for the
	// given period.
	@SuppressWarnings("unchecked")
	private boolean walkGroup(List<Site> groupSites,
			List<Supply> groupSupplies, HhEndDate from, HhEndDate to) {
		// Debug.print("Started walking group");
		Site newSite = groupSites.get(groupSites.size() - 1);
		for (Supply candidateSupply : (List<Supply>) Hiber
				.session()
				.createQuery(
						"select distinct supply from Supply supply join supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site and supplyGeneration.startDate.date <= :to and (supplyGeneration.finishDate.date is null or supplyGeneration.finishDate.date >= :from)")
				.setEntity("site", newSite)
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate()).list()) {
			if (!groupSupplies.contains(candidateSupply)) {
				// check if continuously attached.
				if (candidateSupply.getGenerations(from, to).size() == Hiber
						.session()
						.createQuery(
								"select distinct generation from SupplyGeneration generation join generation.siteSupplyGenerations siteSupplyGeneration where generation.supply = :supply and siteSupplyGeneration.site = :site and generation.startDate.date <= :to and (generation.finishDate.date is null or generation.finishDate.date >= :from)")
						.setEntity("supply", candidateSupply).setEntity("site",
								newSite).setTimestamp("from", from.getDate())
						.setTimestamp("to", to.getDate()).list().size()) {
					groupSupplies.add(candidateSupply);
					for (Site site : (List<Site>) Hiber
							.session()
							.createQuery(
									"select distinct siteSupplyGeneration.site from SupplyGeneration generation join generation.siteSupplyGenerations siteSupplyGeneration where generation.supply = :supply and generation.startDate.date <= :to and (generation.finishDate.date is null or generation.finishDate.date >= :from)")
							.setEntity("supply", candidateSupply).setTimestamp(
									"from", from.getDate()).setTimestamp("to",
									to.getDate()).list()) {
						// Debug.print("About to test if " +
						// site.getCode().toString() + " is contained in " +
						// groupSites.toString());
						if (!groupSites.contains(site)) {
							groupSites.add(site);
							// Debug.print("Added " + site.getCode().toString()
							// + " ");
							if (!walkGroup(groupSites, groupSupplies, from, to)) {
								return false;
							}
						} else {
							// Debug.print("Not added.");
						}
					}
				} else {
					return false;
				}
			}
		}
		return true;
	}

	public int physicalSupplies() {
		int physicalSupplies = 0;
		for (SiteSupplyGeneration siteSupplyGeneration : siteSupplyGenerations) {
			if (siteSupplyGeneration.getIsPhysical()) {
				physicalSupplies++;
			}
		}
		return physicalSupplies;
	}

	public void attachSiteSupplyGeneration(
			SiteSupplyGeneration siteSupplyGeneration) {
		siteSupplyGenerations.add(siteSupplyGeneration);
		Hiber.flush();
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.SITES_INSTANCE.getUri().resolve(getUriId()).append("/");
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof Site) {
			isEqual = ((Site) obj).getId().equals(getId());
		}
		return isEqual;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element docElem = doc.getDocumentElement();
		Element siteElement = (Element) toXml(doc, new XmlTree("organization"));
		docElem.appendChild(siteElement);
		for (SupplyGeneration generation : (List<SupplyGeneration>) Hiber
				.session()
				.createQuery(
						"select supplyGeneration from SupplyGeneration supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site order by supplyGeneration.finishDate.date")
				.setEntity("site", this).list()) {
			siteElement.appendChild(generation.toXml(doc,
					new XmlTree("mpans", new XmlTree("mpanCore").put("mpanTop",
							new XmlTree("llfc"))).put("supply", new XmlTree(
							"source"))));
		}
		for (Source source : (List<Source>) Hiber.session().createQuery(
				"from Source source order by source.code").list()) {
			docElem.appendChild(source.toXml(doc));
		}
		docElem.appendChild(MonadDate.getMonthsXml(doc));
		docElem.appendChild(MonadDate.getDaysXml(doc));
		docElem.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			Document doc = document();
			Element source = doc.getDocumentElement();

			source.appendChild(toXml(doc));
			try {
				Site.deleteSite(this);
			} catch (HttpException e) {
				e.setDocument(doc);
				throw e;
			}
			source.appendChild(new MonadMessage("Site deleted successfully.")
					.toXml(doc));
			Hiber.commit();
			inv.sendOk(doc);
		} else if (inv.hasParameter("update")) {
			String code = inv.getString("code");
			String name = inv.getString("name");
			update(code, name);
			Hiber.commit();
			inv.sendOk(document());
		} else if (inv.hasParameter("insert")) {
			String name = inv.getString("name");
			String meterSerialNumber = inv.getString("meter-serial-number");
			String importMpanStr = inv.getString("import-mpan");
			String importSscCode = inv.getString("import-ssc");
			String importHhdcContractName = inv
					.getString("import-hhdc-contract-name");
			String importHhdcAccountReference = inv
					.getString("import-hhdc-account-reference");
			String importSupplierContractName = inv
					.getString("import-supplier-contract-name");
			String importSupplierAccountReference = inv
					.getString("import-supplier-account-reference");
			String importAgreedSupplyCapacityStr = inv
					.getString("import-agreed-supply-capacity");
			String exportMpanStr = inv.getString("export-mpan-str");
			String exportSscCode = inv.getString("export-ssc-code");
			String exportHhdcContractName = inv
					.getString("export-hhdc-contract-name");
			String exportHhdcAccountReference = inv
					.getString("export-hhdc-account-reference");
			String exportSupplierContractName = inv
					.getString("export-supplier-contract-name");
			String exportSupplierAccountReference = inv
					.getString("export-supplier-account-reference");
			String exportAgreedSupplyCapacityStr = inv
					.getString("export-agreed-supply-capacity");
			Date startDate = inv.getDate("start-date");
			String sourceCode = inv.getString("source-code");
			try {
				Supply supply = insertSupply(name, meterSerialNumber,
						importMpanStr, importSscCode, importHhdcContractName,
						importHhdcAccountReference, importSupplierContractName,
						importSupplierAccountReference,
						importAgreedSupplyCapacityStr, exportMpanStr,
						exportSscCode, exportHhdcContractName,
						exportHhdcAccountReference, exportSupplierContractName,
						exportSupplierAccountReference,
						exportAgreedSupplyCapacityStr,
						new HhEndDate(startDate), sourceCode);
				Hiber.commit();
				inv.sendCreated(supply.getUri());
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
		}
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		throw new NotFoundException();
	}

	public void detachSiteSupplyGeneration(
			SiteSupplyGeneration siteSupplyGeneration) throws HttpException {
		siteSupplyGenerations.remove(siteSupplyGeneration);
	}
}