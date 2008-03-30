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
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TimeZone;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.DceService;
import net.sf.chellow.billing.SupplierService;
import net.sf.chellow.data08.Data;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Site extends PersistentEntity implements Urlable {
	public static final String EXPORT_NET_GT_IMPORT_GEN = "Export to net > import from generators.";

	public static final String EXPORT_GEN_GT_IMPORT = "Export to generators > import.";

	private Organization organization;

	private SiteCode code;

	private String name;

	private Set<SiteSupplyGeneration> siteSupplyGenerations;

	public Site() {
		setTypeName("site");
	}

	public Site(Organization organization, SiteCode code, String name)
			throws ProgrammerException, UserException {
		this();
		this.organization = organization;
		update(code, name);
	}

	public Organization getOrganization() {
		return organization;
	}

	public void setOrganization(Organization organization) {
		this.organization = organization;
	}

	public SiteCode getCode() {
		return code;
	}

	public void setCode(SiteCode code) {
		this.code = code;
		if (code != null) {
			code.setLabel("code");
		}
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

	public void update(SiteCode code, String name) throws ProgrammerException,
			UserException {
		setCode(code);
		MonadString.update("name", name, true, 200, 0,
				Character.UnicodeBlock.BASIC_LATIN, false);
		setName(name);
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttributeNode(MonadString.toXml(doc, "name", getName()));
		element.setAttributeNode((Attr) getCode().toXML(doc));
		return element;
	}

	public Supply insertSupply(SupplyName supplyName, String meterSerialNumber,
			MpanRaw importMpanRaw, DceService importContractDce,
			Account importAccountSupplier,
			SupplierService importContractSupplier,
			boolean importHasDceImportKwh, boolean importHasDceImportKvarh,
			boolean importHasDceExportKwh, boolean importHasDceExportKvarh,
			Integer importAgreedSupplyCapacity, MpanRaw exportMpanRaw,
			DceService exportContractDce, Account exportAccountSupplier,
			SupplierService exportContractSupplier,
			boolean exportHasDceImportKwh, boolean exportHasDceImportKvarh,
			boolean exportHasDceExportKwh, boolean exportHasDceExportKvarh,
			Integer exportAgreedSupplyCapacity, HhEndDate startDate,
			SourceCode sourceCode, Long id) throws ProgrammerException,
			UserException, DesignerException {
		Source source = Source.getSource(sourceCode);
		Supply supply = new Supply(supplyName, source);
		try {
			supply.setId(id);
			Hiber.session().save(supply);
			Hiber.flush();
		} catch (HibernateException e) {
			Hiber.rollBack();
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"mpan_dso_id_key\"")) {
				BatchUpdateException be = (BatchUpdateException) e.getCause();
				String message = be.getMessage();
				boolean isImport = message.charAt(message.lastIndexOf(',') - 1) == '0';
				throw UserException.newOk("An MPAN with this "
						+ (isImport ? "import" : "export")
						+ " MPAN core already exists.");
			} else {
				throw new ProgrammerException(e);
			}
		}
		supply.insertChannel(true, true);
		supply.insertChannel(true, false);
		supply.insertChannel(false, true);
		supply.insertChannel(false, false);
		if (importMpanRaw != null) {
			supply.addMpanCore(importMpanRaw.getMpanCoreRaw());
		}
		if (exportMpanRaw != null) {
			supply.addMpanCore(exportMpanRaw.getMpanCoreRaw());
		}
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
				meter, importMpanRaw, importContractDce,
				importAccountSupplier, importContractSupplier,
				importHasDceImportKwh, importHasDceImportKvarh,
				importHasDceExportKwh, importHasDceExportKvarh,
				importAgreedSupplyCapacity, exportMpanRaw, exportContractDce,
				exportAccountSupplier, exportContractSupplier,
				exportHasDceImportKwh, exportHasDceImportKvarh,
				exportHasDceExportKwh, exportHasDceExportKvarh,
				exportAgreedSupplyCapacity, null);
		supplyGeneration.update(startDate, supplyGeneration.getFinishDate(), meter);
		Hiber.flush();
		return supply;
	}

	public void hhCheck(HhEndDate from, HhEndDate to)
			throws ProgrammerException, UserException {
		Calendar cal = GregorianCalendar.getInstance(TimeZone
				.getTimeZone("GMT"), Locale.UK);
		for (SiteGroup group : groups(from, to)) {
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
			// HhEndDate ok1Start = checkFrom;
			// HhEndDate ok2Start = checkFrom;
			int i = 0;
			HhEndDate hhEndDate = group.getFrom();
			HhEndDate previousEndDate = null;
			cal.clear();
			cal.setTime(hhEndDate.getDate());
			cal.set(Calendar.DAY_OF_MONTH, 1);
			cal.set(Calendar.HOUR_OF_DAY, 0);
			cal.set(Calendar.MINUTE, 0);
			cal.set(Calendar.SECOND, 0);
			cal.set(Calendar.MILLISECOND, 0);
			DceService previousDceService = getDceService(new HhEndDate(cal
					.getTime()));
			DceService dceService = previousDceService;
			int month = cal.get(Calendar.MONTH);
			while (!hhEndDate.getDate().after(group.getTo().getDate())) {
				cal.clear();
				cal.setTime(hhEndDate.getDate());
				if (month != cal.get(Calendar.MONTH)) {
					month = cal.get(Calendar.MONTH);
					previousDceService = dceService;
					dceService = getDceService(new HhEndDate(cal.getTime()));
				}
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
				if (snag1To != null
						&& (snag1To.equals(previousEndDate) || !dceService
								.equals(previousDceService))) {
					addDceSnagSite(previousDceService,
							EXPORT_NET_GT_IMPORT_GEN, snag1From, snag1To, false);
					snag1From = null;
					snag1To = null;
				}
				if (resolve1To != null && resolve1To.equals(previousEndDate)) {
					resolveDceSnag(EXPORT_NET_GT_IMPORT_GEN, resolve1From,
							resolve1To);
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
				if (snag2To != null
						&& (snag2To.equals(previousEndDate) || !dceService
								.equals(previousDceService))) {
					addDceSnagSite(previousDceService, EXPORT_GEN_GT_IMPORT,
							snag2From, snag2To, false);
					snag2From = null;
					snag2To = null;
				}
				if (resolve2To != null && resolve2To.equals(previousEndDate)) {
					resolveDceSnag(EXPORT_GEN_GT_IMPORT, resolve2From,
							resolve2To);
					resolve2From = null;
					resolve2To = null;
				}
				i++;
				previousEndDate = hhEndDate;
				hhEndDate = hhEndDate.getNext();
			}
			if (snag1To != null && snag1To.equals(previousEndDate)) {
				addDceSnagSite(previousDceService, EXPORT_NET_GT_IMPORT_GEN,
						snag1From, snag1To, false);
			}
			if (resolve1To != null && resolve1To.equals(previousEndDate)) {
				resolveDceSnag(EXPORT_NET_GT_IMPORT_GEN, resolve1From,
						resolve1To);
			}
			if (snag2To != null && snag2To.equals(previousEndDate)) {
				addDceSnagSite(previousDceService, EXPORT_GEN_GT_IMPORT,
						snag2From, snag2To, false);
			}
			if (resolve2To != null && resolve2To.equals(previousEndDate)) {
				resolveDceSnag(EXPORT_GEN_GT_IMPORT, resolve2From, resolve2To);
			}
		}
	}

	/*
	 * private void addDceSnagSite(String type, HhEndDate from, HhEndDate to) {
	 * List<DceService> dceServices = new ArrayList<DceService>(); for
	 * (SupplyGeneration supplyGeneration : Hiber.session().createQuery("from
	 * SupplyGeneration generation join generation.siteSupplyGenerations
	 * siteSupplyGeneration where siteSupplyGeneration.site = :site and
	 * supplyGeneration.startDate <= :")) for (SiteSupplyGeneration
	 * siteSupplyGeneration : siteSupplyGenerations) { SupplyGeneration
	 * generation = siteSupplyGeneration
	 * .getSupplyGeneration().getSupply().getGeneration(date); if (generation !=
	 * null) { for (Mpan mpan : generation.getMpans()) {
	 * dceServices.add(mpan.getDceService()); } } }
	 * Collections.sort(dceServices); DceService dceService =
	 * dceServices.get(0); addDceSnagSite(dceService, EXPORT_NET_GT_IMPORT_GEN,
	 * hhEndDate, hhEndDate, false); }
	 */

	public List<SiteGroup> groups(HhEndDate from, HhEndDate to)
			throws ProgrammerException, UserException {
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
								.getCode().getString().compareTo(
										site1.getCode().getString())
								: physicalSupplies2 - physicalSupplies1;
					}
				});
				if (sites.get(0).equals(this)) {
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
		/*
		 * for (SiteSupplyGeneration siteSupplyGenerationSupply :
		 * groupSites.get( groupSites.size() - 1).getSiteSupplyGenerations()) {
		 * Supply supply = siteSupplyGenerationSupply.getSupplyGeneration()
		 * .getSupply(); if (!groupSupplies.contains(supply)) { for
		 * (SupplyGeneration generation : supply.getGenerations(from, to)) {
		 * SiteSupplyGeneration prevSiteSupplyGeneration = null; for
		 * (SiteSupplyGeneration siteSupplyGeneration : generation
		 * .getSiteSupplyGenerations()) { if (prevSiteSupplyGeneration != null &&
		 * !siteSupplyGeneration .equals(prevSiteSupplyGeneration)) { return
		 * false; } prevSiteSupplyGeneration = siteSupplyGeneration; } }
		 * groupSupplies.add(supply); for (SiteSupplyGeneration
		 * siteSupplyGenerationSite : siteSupplyGenerationSupply
		 * .getSupplyGeneration().getSiteSupplyGenerations()) { if (!groupSites
		 * .contains(siteSupplyGenerationSite.getSite())) {
		 * groupSites.add(siteSupplyGenerationSite.getSite()); if
		 * (!walkGroup(groupSites, groupSupplies, from, to)) { return false; } } } } }
		 */
		return true;
	}

	@SuppressWarnings("unchecked")
	private void resolveDceSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws ProgrammerException, UserException {
		if (!startDate.getDate().after(finishDate.getDate())) {
			for (SnagSite snag : (List<SnagSite>) Hiber
					.session()
					.createQuery(
							"from SnagSite snag where snag.site = :site and snag.description = :description and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.dateResolved is null")
					.setEntity("site", this).setString("description",
							description.toString()).setTimestamp("startDate",
							startDate.getDate()).setTimestamp("finishDate",
							finishDate.getDate()).list()) {
				addDceSnagSite(snag.getService(), description,
						snag.getStartDate().getDate().before(
								startDate.getDate()) ? startDate : snag
								.getStartDate(), snag.getFinishDate().getDate()
								.after(finishDate.getDate()) ? finishDate
								: snag.getFinishDate(), true);
			}
		}
	}

	@SuppressWarnings("unchecked")
	private DceService getDceService(HhEndDate date) {
		List<DceService> services = (List<DceService>) Hiber
				.session()
				.createQuery(
						"select distinct mpan.dceService from Mpan mpan join mpan.supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site and mpan.supplyGeneration.startDate.date <= :date and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate >= :date)")
				.setEntity("site", this).setTimestamp("date", date.getDate())
				.list();
		Collections.sort(services);
		return services.get(0);
		/*
		 * 
		 * 
		 * List<DceService> dceServices = new ArrayList<DceService>(); for
		 * (SiteSupplyGeneration siteSupplyGeneration : siteSupplyGenerations) {
		 * SupplyGeneration generation = siteSupplyGeneration
		 * .getSupplyGeneration().getSupply().getGeneration(date); if
		 * (generation != null) { for (Mpan mpan : generation.getMpans()) {
		 * dceServices.add(mpan.getDceService()); } } }
		 * Collections.sort(dceServices); return dceServices.get(0);
		 */
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

	/*
	 * @SuppressWarnings("unchecked") public List<Supply> supplysByFinishDate()
	 * throws ProgrammerException { try { return (List<Supply>) Hiber
	 * .session() .createQuery( "select distinct siteSupplyGesupply from Supply
	 * supply join supply.siteSupplyGenerations siteSupplyGeneration where
	 * siteSupply.site = :site order by supply.name.string") .setEntity("site",
	 * this).list(); } catch (HibernateException e) { throw new
	 * ProgrammerException(e); } }
	 */
	public void attachSiteSupplyGeneration(
			SiteSupplyGeneration siteSupplyGeneration) {
		siteSupplyGenerations.add(siteSupplyGeneration);
		Hiber.flush();
	}

	private void addDceSnagSite(DceService contractDce, String description,
			HhEndDate startDate, HhEndDate finishDate, boolean isResolved)
			throws ProgrammerException, UserException {
		SnagDateBounded.addSnagSite(contractDce, this, description, startDate,
				finishDate, isResolved);
	}

	/*
	 * @SuppressWarnings("unchecked") private void addSnagSite(Contract
	 * contract, MonadString description, HhEndDate startDate, HhEndDate
	 * finishDate, boolean isResolved) throws ProgrammerException, UserException {
	 * Query query = Hiber .session() .createQuery( "from SnagSite snag where
	 * snag.site = :site and snag.startDate.date <= :finishDate and
	 * snag.finishDate.date >= :startDate and snag.description.string =
	 * :description order by snag.startDate.date") .setEntity("site",
	 * this).setTimestamp("finishDate",
	 * finishDate.getDate()).setTimestamp("startDate",
	 * startDate.getDate()).setString("description", description.toString());
	 * SnagSite unresolved = new SnagSite(description, contract, this,
	 * startDate, finishDate); for (SnagSite snag : (List<SnagSite>)
	 * query.list()) { if
	 * (snag.getFinishDate().getDate().after(finishDate.getDate())) { SnagSite
	 * outerSnag = snag.copy();
	 * outerSnag.setStartDate(HhEndDate.getNext(finishDate));
	 * snag.setFinishDate(finishDate); SnagSite.insertSnagSite(outerSnag);
	 * Hiber.flush(); } if
	 * (snag.getStartDate().getDate().before(startDate.getDate())) { SnagSite
	 * outerSnag = snag.copy();
	 * outerSnag.setFinishDate(HhEndDate.getPrevious(startDate));
	 * snag.setStartDate(startDate); SnagSite.insertSnagSite(outerSnag);
	 * Hiber.flush(); unresolved.setFinishDate(HhEndDate
	 * .getNext(snag.getFinishDate())); unresolved
	 * .setStartDate(HhEndDate.getNext(snag.getFinishDate())); } if
	 * (unresolved.getStartDate().getDate().before(
	 * snag.getStartDate().getDate())) {
	 * unresolved.setFinishDate(HhEndDate.getPrevious(snag .getStartDate()));
	 * SnagSite.insertSnagSite(unresolved); unresolved = new
	 * SnagSite(description, contract, this,
	 * HhEndDate.getNext(snag.getFinishDate()), HhEndDate
	 * .getNext(snag.getFinishDate())); } else {
	 * unresolved.setFinishDate(HhEndDate .getNext(snag.getFinishDate()));
	 * unresolved .setStartDate(HhEndDate.getNext(snag.getFinishDate())); } } if
	 * (!unresolved.getStartDate().getDate().after(finishDate.getDate())) {
	 * unresolved.setFinishDate(finishDate);
	 * SnagSite.insertSnagSite(unresolved); } for (SnagSite snag : (List<SnagSite>)
	 * query.list()) { if (isResolved) { if (snag.getDateResolved() == null) {
	 * snag.resolve(false); } else if (snag.getIsIgnored().getBoolean() == true) {
	 * snag.setIsIgnored(new MonadBoolean(false)); } } else if
	 * (snag.getDateResolved() != null && !snag.getIsIgnored().getBoolean()) {
	 * snag.deResolve(); } } SnagSite previousSnag = null; for (SnagSite snag :
	 * (List<SnagSite>) query.setTimestamp("startDate",
	 * startDate.getPrevious().getDate()).setTimestamp("finishDate",
	 * finishDate.getNext().getDate()).list()) { boolean combinable = false; if
	 * (previousSnag != null) { combinable =
	 * previousSnag.getFinishDate().getDate().getTime() == snag
	 * .getStartDate().getPrevious().getDate().getTime() &&
	 * previousSnag.getContract() .equals(snag.getContract()); if (combinable) {
	 * combinable = snag.getProgress().equals( previousSnag.getProgress()); } if
	 * (combinable) { if (previousSnag.getDateResolved() == null &&
	 * snag.getDateResolved() == null) { combinable = true; } else if
	 * ((previousSnag.getDateResolved() != null && snag .getDateResolved() !=
	 * null) && previousSnag.getDateResolved().equals( snag.getDateResolved()) &&
	 * previousSnag.getIsIgnored().equals( snag.getIsIgnored())) { combinable =
	 * true; } else { combinable = false; } } if (combinable) {
	 * previousSnag.updateFinishDate(snag.getFinishDate());
	 * SnagSite.deleteSnagSite(snag); } } if (!combinable) { previousSnag =
	 * snag; } } }
	 */
	public MonadUri getUri() throws ProgrammerException, UserException {
		return organization.getSitesInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof Site) {
			isEqual = ((Site) obj).getId().equals(getId());
		}
		return isEqual;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();
		Element siteElement = (Element) getXML(new XmlTree("organization"), doc);
		source.appendChild(siteElement);
		for (SupplyGeneration generation : (List<SupplyGeneration>) Hiber
				.session()
				.createQuery(
						"select supplyGeneration from SupplyGeneration supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site order by supplyGeneration.finishDate.date")
				.setEntity("site", this).list()) {
			siteElement.appendChild(generation.getXML(new XmlTree("mpans",
					new XmlTree("mpanCore")).put("supply",
					new XmlTree("source")), doc));

		}
		return doc;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		if (inv.hasParameter("delete")) {
			Document doc = document();
			Element source = doc.getDocumentElement();

			source.appendChild(toXML(doc));
			organization.deleteSite(this);
			source.appendChild(new VFMessage("Site deleted successfully.")
					.toXML(doc));
			Hiber.commit();
			inv.sendOk(doc);
		} else {
			SiteCode code = inv.getValidatable(SiteCode.class, "code");
			String name = inv.getString("name");
			update(code, name);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public Urlable getChild(UriPathElement urlId) throws ProgrammerException,
			UserException {
		throw UserException.newNotFound();
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		throw UserException.newMethodNotAllowed();
	}

	public void detachSiteSupplyGeneration(
			SiteSupplyGeneration siteSupplyGeneration) throws UserException,
			ProgrammerException {
		siteSupplyGenerations.remove(siteSupplyGeneration);
	}
}