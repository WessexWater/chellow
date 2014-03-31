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

package net.sf.chellow.physical;

import java.net.URI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
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
import net.sf.chellow.ui.GeneralImport;

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
			throw new UserException(
					"Problem saving site, perhaps there's a duplicate code or name. "
							+ HttpException.getUserMessage(e));
		}
		return site;
	}

	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		Site site = null;
		String code = GeneralImport
				.addField(csvElement, "Site Code", values, 0);
		if (action.equals("insert")) {
			String name = GeneralImport.addField(csvElement, "Site name",
					values, 1);
			insertSite(code, name);
		} else {
			site = Site.getSite(code);
			if (site == null) {
				throw new UserException("There is no site with this code.");
			}
			if (action.equals("delete")) {
				Site.deleteSite(site);
			} else if (action.equals("update")) {
				String newCode = GeneralImport.addField(csvElement,
						"New Site Code", values, 2);
				String name = GeneralImport.addField(csvElement,
						"New site name", values, 3);
				site.update(newCode, name);
			}
		}
	}

	static public Site findSite(String siteCode) throws HttpException {
		return (Site) Hiber.session()
				.createQuery("from Site as site where site.code = :siteCode")
				.setString("siteCode", siteCode).uniqueResult();
	}

	static public Site getSite(String code) throws HttpException {
		Site site = findSite(code);
		if (site == null) {
			throw new NotFoundException("The site '" + code
					+ "' cannot be found.");
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

	private String code;

	private String name;

	private Set<SiteEra> siteEras;

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

	public Set<SiteEra> getSiteEras() {
		return siteEras;
	}

	protected void setSiteEras(Set<SiteEra> siteEras) {
		this.siteEras = siteEras;
	}

	public void update(String code, String name) throws HttpException {
		setCode(code);
		MonadString.update("name", name, true, 200, 0,
				Character.UnicodeBlock.BASIC_LATIN, false);
		setName(name);
	}

	@SuppressWarnings("unchecked")
	static public void deleteSite(Site site) throws HttpException {
		if (Hiber.session()
				.createQuery("from SiteEra ssg where ssg.site = :site")
				.setEntity("site", site).list().size() > 0) {
			throw new UserException(
					"This site can't be deleted while there are still supply eras attached to it.");
		}
		for (Snag snag : (List<Snag>) Hiber.session()
				.createQuery("from Snag snag where site = :site")
				.setEntity("site", site).list()) {
			snag.delete();
		}
		Hiber.session().delete(site);
		Hiber.flush();
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.SITES_INSTANCE.getUrlPath().resolve(getUriId())
				.append("/");
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "site");

		element.setAttribute("name", name);
		element.setAttribute("code", code);
		return element;
	}

	public void attachSiteEra(SiteEra siteEra) {
		siteEras.add(siteEra);
		Hiber.flush();
	}

	public List<SiteGroup> groups(HhStartDate from, HhStartDate to,
			boolean primaryOnly) throws HttpException {
		List<SiteGroup> groups = new ArrayList<SiteGroup>();
		HhStartDate checkFrom = from;
		HhStartDate checkTo = to;
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
				checkTo = HhStartDate
						.roundDown(new Date(
								(long) Math.floor(((double) (checkTo.getDate()
										.getTime() - checkFrom.getDate()
										.getTime())) / 2)));
			}
		}
		return groups;
	}

	public void hhCheck(HhStartDate from, HhStartDate to) throws HttpException {
		// Calendar cal = GregorianCalendar.getInstance(TimeZone
		// .getTimeZone("GMT"), Locale.UK);
		for (SiteGroup group : groups(from, to, false)) {
			if (group.getSupplies().size() == 1) {
				continue;
			}
			// long now = System.currentTimeMillis();
			// Debug.print("About to go checking: "
			// + (System.currentTimeMillis() - now));
			Map<String, List<Double>> map = group.hhData();

			List<Double> importFromNet = map.get("import-net");
			List<Double> exportToNet = map.get("export-net");
			List<Double> importFromGen = map.get("import-gen");
			List<Double> exportToGen = map.get("export-gen");

			HhStartDate resolve1From = null;
			HhStartDate resolve1To = null;
			HhStartDate snag1From = null;
			HhStartDate snag1To = null;
			HhStartDate resolve2From = null;
			HhStartDate resolve2To = null;
			HhStartDate snag2From = null;
			HhStartDate snag2To = null;
			int i = 0;
			HhStartDate previousStartDate = null;
			HhStartDate hhStartDate = group.getFrom();
			while (!hhStartDate.getDate().after(group.getTo().getDate())) {
				if (exportToNet.get(i) > importFromGen.get(i)) {
					if (snag1From == null) {
						snag1From = hhStartDate;
					}
					snag1To = hhStartDate;
				} else {
					if (resolve1From == null) {
						resolve1From = hhStartDate;
					}
					resolve1To = hhStartDate;
				}
				if (snag1To != null && (snag1To.equals(previousStartDate))) {
					group.addSiteSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
							snag1From, snag1To);
					snag1From = null;
					snag1To = null;
				}
				if (resolve1To != null && resolve1To.equals(previousStartDate)) {
					group.deleteHhdcSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
							resolve1From, resolve1To);
					resolve1From = null;
					resolve1To = null;
				}
				if (exportToGen.get(i) > importFromNet.get(i)
						+ importFromGen.get(i)) {
					if (snag2From == null) {
						snag2From = hhStartDate;
					}
					snag2To = hhStartDate;
				} else {
					if (resolve2From == null) {
						resolve2From = hhStartDate;
					}
					resolve2To = hhStartDate;
				}
				if (snag2To != null && snag2To.equals(previousStartDate)) {
					group.addSiteSnag(SiteGroup.EXPORT_GEN_GT_IMPORT,
							snag2From, snag2To);
					snag2From = null;
					snag2To = null;
				}
				if (resolve2To != null && resolve2To.equals(previousStartDate)) {
					group.deleteHhdcSnag(SiteGroup.EXPORT_GEN_GT_IMPORT,
							resolve2From, resolve2To);
					resolve2From = null;
					resolve2To = null;
				}
				i++;
				previousStartDate = hhStartDate;
				hhStartDate = hhStartDate.getNext();
			}
			if (snag1To != null) {
				group.addSiteSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
						snag1From, snag1To);
			}
			if (resolve1To != null) {
				group.deleteHhdcSnag(SiteGroup.EXPORT_NET_GT_IMPORT_GEN,
						resolve1From, resolve1To);
			}
			if (snag2To != null) {
				group.addSiteSnag(SiteGroup.EXPORT_GEN_GT_IMPORT, snag2From,
						snag2To);
			}
			if (resolve2To != null) {
				group.deleteHhdcSnag(SiteGroup.EXPORT_GEN_GT_IMPORT,
						resolve2From, resolve2To);
			}
		}
	}

	public int physicalSupplies() {
		int physicalSupplies = 0;
		for (SiteEra siteEra : siteEras) {
			if (siteEra.getIsPhysical()) {
				physicalSupplies++;
			}
		}
		return physicalSupplies;
	}

	@SuppressWarnings("unchecked")
	private boolean walkGroup(List<Site> groupSites,
			List<Supply> groupSupplies, HhStartDate from, HhStartDate to) {
		// Debug.print("Started walking group");
		Site newSite = groupSites.get(groupSites.size() - 1);
		for (Supply candidateSupply : (List<Supply>) Hiber
				.session()
				.createQuery(
						"select distinct supply from Supply supply join supply.eras era join era.siteEras siteEra where siteEra.site = :site and era.startDate.date <= :to and (era.finishDate.date is null or era.finishDate.date >= :from)")
				.setEntity("site", newSite)
				.setTimestamp("from", from.getDate())
				.setTimestamp("to", to.getDate()).list()) {
			if (!groupSupplies.contains(candidateSupply)) {
				// check if continuously attached.
				if (candidateSupply.getEras(from, to).size() == Hiber
						.session()
						.createQuery(
								"select distinct era from Era era join era.siteEras siteEra where era.supply = :supply and siteEra.site = :site and era.startDate.date <= :to and (era.finishDate.date is null or era.finishDate.date >= :from)")
						.setEntity("supply", candidateSupply)
						.setEntity("site", newSite)
						.setTimestamp("from", from.getDate())
						.setTimestamp("to", to.getDate()).list().size()) {
					groupSupplies.add(candidateSupply);
					for (Site site : (List<Site>) Hiber
							.session()
							.createQuery(
									"select distinct siteEra.site from Era era join era.siteEras siteEra where era.supply = :supply and era.startDate.date <= :to and (era.finishDate.date is null or era.finishDate.date >= :from)")
							.setEntity("supply", candidateSupply)
							.setTimestamp("from", from.getDate())
							.setTimestamp("to", to.getDate()).list()) {
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

	public void detachSiteEra(SiteEra siteEra) throws HttpException {
		siteEras.remove(siteEra);
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element docElem = doc.getDocumentElement();
		Element siteElement = toXml(doc);
		docElem.appendChild(siteElement);
		for (Era era : (List<Era>) Hiber
				.session()
				.createQuery(
						"select era from Era era join era.siteEras siteEra where siteEra.site = :site order by era.finishDate.date")
				.setEntity("site", this).list()) {
			siteElement.appendChild(era.toXml(doc, new XmlTree("supply",
					new XmlTree("source"))));
		}
		for (Source source : (List<Source>) Hiber.session()
				.createQuery("from Source source order by source.code").list()) {
			docElem.appendChild(source.toXml(doc));
		}
		for (GeneratorType genType : (List<GeneratorType>) Hiber
				.session()
				.createQuery("from GeneratorType genType order by genType.code")
				.list()) {
			docElem.appendChild(genType.toXml(doc));
		}
		for (GspGroup group : (List<GspGroup>) Hiber.session()
				.createQuery("from GspGroup group order by group.code").list()) {
			docElem.appendChild(group.toXml(doc));
		}

		for (Pc pc : (List<Pc>) Hiber.session()
				.createQuery("from Pc pc order by pc.code").list()) {
			docElem.appendChild(pc.toXml(doc));
		}

		for (Cop cop : (List<Cop>) Hiber.session()
				.createQuery("from Cop cop order by cop.code").list()) {
			docElem.appendChild(cop.toXml(doc));
		}

		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'M' order by contract.name")
				.list()) {
			docElem.appendChild(contract.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'C' order by contract.name")
				.list()) {
			docElem.appendChild(contract.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'X' order by contract.name")
				.list()) {
			docElem.appendChild(contract.toXml(doc));
		}
		docElem.appendChild(MonadDate.getMonthsXml(doc));
		docElem.appendChild(MonadDate.getDaysXml(doc));
		docElem.appendChild(new MonadDate().toXml(doc));
		return doc;
	}
}
