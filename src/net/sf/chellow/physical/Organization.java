/*
 
 Copyright 2005 Meniscus Systems Ltd
 
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

import java.util.List;
import java.util.Set;

import net.sf.chellow.billing.Dce;
import net.sf.chellow.billing.Dces;
import net.sf.chellow.billing.Dcs;
import net.sf.chellow.billing.GenDeltas;
import net.sf.chellow.billing.Mop;
import net.sf.chellow.billing.Supplier;
import net.sf.chellow.billing.Suppliers;
import net.sf.chellow.billing.UseDeltas;
import net.sf.chellow.data08.Data;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.HeaderImportProcesses;
import net.sf.chellow.ui.Reports;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Organization extends PersistentEntity {
	static public Organization findOrganization(MonadUri urlId)
			throws ProgrammerException, UserException {
		Organization organization = (Organization) Hiber.session().createQuery(
				"from Organization as organization where "
						+ "organization.urlId.string = :urlId").setString(
				"urlId", urlId.toString()).uniqueResult();
		return organization;
	}

	public static Organization getOrganization(MonadLong id)
			throws ProgrammerException, UserException {
		return getOrganization(id.getLong());
	}

	public static Organization getOrganization(Long id)
			throws ProgrammerException, UserException {
		Organization organization = (Organization) Hiber.session().get(
				Organization.class, id);
		if (organization == null) {
			throw UserException
					.newNotFound("There isn't an organization with that id.");
		}
		return organization;
	}

	private String name;

	private Set<User> users;

	private Set<Dce> suppliers;

	public Organization() {
		setTypeName("organization");
	}

	public Organization(String name) {
		this(null, name);
	}

	public Organization(String label, String name) {
		this();
		setLabel(label);
		update(name);
	}

	void setName(String name) {
		this.name = name;
	}

	public String getName() {
		return name;
	}

	void setUsers(Set<User> users) {
		this.users = users;
	}

	public Set<User> getUsers() {
		return users;
	}

	void setSuppliers(Set<Dce> suppliers) {
		this.suppliers = suppliers;
	}

	public Set<Dce> getSuppliers() {
		return suppliers;
	}

	public void update(String name) {
		setName(name);
		Hiber.flush();
	}

	public String toString() {
		return super.toString() + " Name: " + getName();
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttributeNode(MonadString.toXml(doc, "name", name));
		return element;
	}

	public Site insertSite(SiteCode code, String name)
			throws ProgrammerException, UserException {
		Site site = null;
		try {
			site = new Site(this, code, name);
			Hiber.session().save(site);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_organization_id_key\"")) {
				throw UserException
						.newInvalidParameter("A site with this code already exists.");
			} else {
				throw new ProgrammerException(e);
			}
		}
		return site;
	}

	/*
	 * public Site insertSite(SiteCode code, Long id) throws
	 * ProgrammerException, UserException { Site site = null; try { site = new
	 * Site(this, code); site.setId(id); Hiber.session().save(site);
	 * Hiber.flush(); } catch (HibernateException e) { if (Data
	 * .isSQLException(e, "ERROR: duplicate key violates unique constraint
	 * \"site_code_key\"")) { throw UserException .newOk("A site with this code
	 * already exists."); } else { throw new ProgrammerException(e); } } return
	 * site; }
	 */
	public Site findSite(SiteCode siteCode) throws UserException,
			ProgrammerException {
		return (Site) Hiber
				.session()
				.createQuery(
						"from Site as site where site.organization = :organization and site.code.string = :siteCode")
				.setEntity("organization", this).setString("siteCode",
						siteCode.toString()).uniqueResult();
	}

	public Site getSite(Long siteId) throws UserException, ProgrammerException {
		return (Site) Hiber
				.session()
				.createQuery(
						"from Site as site where site.organization = :organization and site.id = :siteId")
				.setEntity("organization", this).setLong("siteId", siteId)
				.uniqueResult();
	}

	@SuppressWarnings("unchecked")
	public List<Site> findSites() {
		return (List<Site>) Hiber
				.session()
				.createQuery(
						"from Site site where site.organization = :organization order by site.code.string")
				.setEntity("organization", this).setMaxResults(50).list();
	}

	@SuppressWarnings("unchecked")
	public List<Site> findSites(String searchTerm) throws ProgrammerException,
			UserException {
		return (List<Site>) Hiber
				.session()
				.createQuery(
						"from Site site where site.organization = :organization and lower(site.code.string || ' ' || site.name) like '%' || lower(:searchTerm) || '%' order by site.code.string")
				.setEntity("organization", this).setString("searchTerm",
						searchTerm).setMaxResults(50).list();
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();

		source.appendChild(toXML(doc));
		inv.sendOk(doc);
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return Chellow.ORGANIZATIONS_INSTANCE.getUri().resolve(getUriId())
				.append("/");
	}

	public Sites getSitesInstance() {
		return new Sites(this);
	}

	public MpanCores getMpanCoresInstance() {
		return new MpanCores(this);
	}

	public Supplies suppliesInstance() {
		return new Supplies(this);
	}

	public Suppliers suppliersInstance() {
		return new Suppliers(this);
	}

	public Dces dcesInstance() {
		return new Dces(this);
	}

	public UseDeltas useDeltasInstance() {
		return new UseDeltas(this);
	}

	public GenDeltas genDeltasInstance() {
		return new GenDeltas(this);
	}

	public Dce getDce(UriPathElement urlId) throws UserException,
			ProgrammerException {
		Dce supplier = (Dce) Hiber
				.session()
				.createQuery(
						"from Supplier supplier where supplier.organization = :organization and supplier.id = :supplierId")
				.setEntity("organization", this).setLong("supplierId",
						Long.parseLong(urlId.getString())).uniqueResult();
		if (supplier == null) {
			throw UserException.newNotFound();
		}
		return supplier;
	}

	public Supply getSupply(long id) throws UserException, ProgrammerException {
		Supply supply = findSupply(id);
		if (supply == null) {
			throw UserException.newNotFound("There is no supply with that id.");
		}
		return supply;
	}

	public Supply findSupply(Long id) {
		return (Supply) Hiber
				.session()
				.createQuery(
						"select supply from Supply supply join supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and supply.id = :supplyId")
				.setEntity("organization", this).setLong("supplyId", id)
				.uniqueResult();
	}

	/*
	 * public Supply findSupply(UriPathElement uriId) { return
	 * findSupply(Long.parseLong(uriId.getString())); }
	 */
	public Supplier getSupplier(long supplierId) throws UserException,
			ProgrammerException {
		Supplier supplier = findSupplier(supplierId);
		if (supplier == null) {
			throw UserException
					.newNotFound("There isn't a supplier attached to this organization with the id '"
							+ supplierId + "'.");
		}
		return supplier;
	}

	public Supplier findSupplier(long supplierId) throws UserException,
			ProgrammerException {
		return (Supplier) Hiber
				.session()
				.createQuery(
						"from Supplier supplier where supplier.organization = :organization and supplier.id = :supplierId")
				.setEntity("organization", this).setLong("supplierId",
						supplierId).uniqueResult();
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		if (inv.hasParameter("delete")) {
			Hiber.session().delete(this);
			Hiber.close();
			inv.sendSeeOther(Chellow.ORGANIZATIONS_INSTANCE.getUri());
		} else if (inv.hasParameter("name")) {
			String name = inv.getString("name");
			update(name);
			Hiber.close();
			inv.sendSeeOther(getUri());
		}
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		Urlable urlable = null;
		if (Sites.URI_ID.equals(uriId)) {
			urlable = new Sites(this);
		} else if (Supplies.URI_ID.equals(uriId)) {
			urlable = new Supplies(this);
		} else if (HeaderImportProcesses.URI_ID.equals(uriId)) {
			urlable = new HeaderImportProcesses(this);
		} else if (MpanCores.URI_ID.equals(uriId)) {
			urlable = new MpanCores(this);
		} else if (Reports.URI_ID.equals(uriId)) {
			urlable = new Reports(this);
		} else if (UseDeltas.URI_ID.equals(uriId)) {
			urlable = new UseDeltas(this);
		} else if (GenDeltas.URI_ID.equals(uriId)) {
			urlable = new GenDeltas(this);
		} else if (Dces.URI_ID.equals(uriId)) {
			return new Dces(this);
		} else if (Suppliers.URI_ID.equals(uriId)) {
			return new Suppliers(this);
		}
		return urlable;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public Site getSite(SiteCode code) throws UserException,
			ProgrammerException {
		Site site = (Site) Hiber
				.session()
				.createQuery(
						"from Site site where site.organization = :organization and site.code.string = :siteCode")
				.setEntity("organization", this).setString("siteCode",
						code.getString()).uniqueResult();
		if (site == null) {
			throw UserException.newNotFound("The site '" + code
					+ "' cannot be found.");
		}
		return site;
	}

	public void deleteSite(Site site) throws ProgrammerException {
		try {
			Hiber.session().delete(site);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	@SuppressWarnings("unchecked")
	public void deleteSupply(Supply supply) throws ProgrammerException,
			UserException {
		long reads = (Long) Hiber
				.session()
				.createQuery(
						"select count(*) from RegisterRead read where read.supplyGeneration.supply = :supply")
				.setEntity("supply", supply).uniqueResult();
		if (reads > 0) {
			throw UserException
					.newInvalidParameter("One can't delete a supply if there are still register reads attached to it.");
		}
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from HhDatum datum where datum.channel.supply = :supply")
				.setEntity("supply", supply).uniqueResult() > 0) {
			throw UserException
					.newInvalidParameter("One can't delete a supply if there are still HH data attached to it.");
		}
		for (SupplyGeneration generation : supply.getGenerations()) {
			generation.delete();
		}
		// delete all the snags
		for (SnagChannel snag : (List<SnagChannel>) Hiber
				.session()
				.createQuery(
						"from SnagChannel snag where snag.channel.supply = :supply")
				.setEntity("supply", supply).list()) {
			Hiber.session().delete(snag);
			Hiber.flush();
		}
		// Hiber.session().createQuery("delete from SnagChannel snag where
		// snag.channel.supply = :supply").setEntity("supply",
		// supply).executeUpdate();
		Hiber.session().delete(supply);
	}

	public void deleteSupplier(Supplier supplier) throws ProgrammerException,
			UserException {
		if (supplier.getOrganization().equals(this)) {
			Hiber.session().delete(supplier);
		} else {
			throw UserException
					.newInvalidParameter("This supplier doesn't belong to this organization.");
		}
	}

	public Supplier insertSupplier(String name) throws UserException,
			ProgrammerException {
		if (findSupplier(name) == null) {
			Supplier supplier = new Supplier(this, name);
			Hiber.session().save(supplier);
			Hiber.flush();
			return supplier;
		} else {
			throw UserException
					.newInvalidParameter("There's already a supplier with this name.");
		}
	}

	public Supplier findSupplier(String name) {
		return (Supplier) Hiber
				.session()
				.createQuery(
						"from Supplier supplier where supplier.organization = :organization and supplier.name = :name")
				.setEntity("organization", this).setString("name", name)
				.uniqueResult();
	}

	public Dce insertDce(String name) {
		Dce dce = new Dce(name, this);
		Hiber.session().save(dce);
		Hiber.flush();
		return dce;
	}

	public Dcs insertDcs(String name) {
		Dcs dcs = new Dcs(name, this);
		Hiber.session().save(dcs);
		Hiber.flush();
		return dcs;
	}

	public Mop insertMop(String name) {
		Mop mop = new Mop(name, this);
		Hiber.session().save(mop);
		Hiber.flush();
		return mop;
	}

	@SuppressWarnings("unchecked")
	public MpanCore findMpanCore(MpanCoreRaw core) throws ProgrammerException,
			UserException {
		for (MpanCore mpanCore : (List<MpanCore>) Hiber
				.session()
				.createQuery(
						"from MpanCore mpanCore where mpanCore.dso.code.string = :dsoCode and mpanCore.uniquePart.string = :uniquePart")
				.setString("dsoCode", core.getDsoCode().getString()).setString(
						"uniquePart", core.getUniquePart().getString()).list()) {
			Set<SupplyGeneration> supplyGenerations = mpanCore.getSupply()
					.getGenerations();
			if (supplyGenerations == null || supplyGenerations.isEmpty()) {
				return mpanCore;
			}
			Set<SiteSupplyGeneration> siteSupplyGenerations = supplyGenerations
					.iterator().next().getSiteSupplyGenerations();
			if (siteSupplyGenerations == null) {
				return mpanCore;
			}
			if (siteSupplyGenerations.iterator().next().getSite()
					.getOrganization().equals(this)) {
				return mpanCore;
			}
		}
		return null;
	}

	public MpanCore getMpanCore(MpanCoreRaw coreRaw) throws UserException,
			ProgrammerException {
		MpanCore core = findMpanCore(coreRaw);
		if (core == null) {
			throw UserException.newOk("There isn't an MPAN with the core "
					+ core);
		}
		return core;
	}

	public Supplier getSupplier(String name) throws UserException,
			ProgrammerException {
		Supplier supplier = (Supplier) Hiber
				.session()
				.createQuery(
						"from Supplier supplier where supplier.organization = :organization and supplier.name = :name")
				.setEntity("organization", this).setString("name", name)
				.uniqueResult();
		if (supplier == null) {
			throw UserException
					.newNotFound("There isn't a supplier with the name '"
							+ name + "'.");
		}
		return supplier;
	}
}