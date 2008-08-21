/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.GenDeltas;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.HhdcContracts;
import net.sf.chellow.billing.MopContract;
import net.sf.chellow.billing.MopContracts;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.billing.SupplierContracts;
import net.sf.chellow.billing.UseDeltas;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.HeaderImportProcesses;
import net.sf.chellow.ui.Reports;

import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Organization extends PersistentEntity {
	static public Organization findOrganization(MonadUri urlId)
			throws InternalException, HttpException {
		Organization organization = (Organization) Hiber.session().createQuery(
				"from Organization as organization where "
						+ "organization.urlId.string = :urlId").setString(
				"urlId", urlId.toString()).uniqueResult();
		return organization;
	}

	public static Organization getOrganization(MonadLong id)
			throws InternalException, HttpException {
		return getOrganization(id.getLong());
	}

	public static Organization getOrganization(Long id)
			throws InternalException, HttpException {
		Organization organization = (Organization) Hiber.session().get(
				Organization.class, id);
		if (organization == null) {
			throw new NotFoundException(
					"There isn't an organization with that id.");
		}
		return organization;
	}

	private String name;

	private Set<User> users;

	public Organization() {
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

	public void update(String name) {
		setName(name);
		Hiber.flush();
	}

	public String toString() {
		return super.toString() + " Name: " + getName();
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "org");

		element.setAttribute("name", name);
		return element;
	}

	public Site insertSite(String code, String name) throws HttpException {
		Site site = null;
		try {
			site = new Site(this, code, name);
			Hiber.session().save(site);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException("A site with this code already exists.");
		}
		/*
		 * } catch (HibernateException e) { if (Data .isSQLException(e, "ERROR:
		 * duplicate key violates unique constraint
		 * \"site_organization_id_key\"")) { throw UserException
		 * .newInvalidParameter("A site with this code already exists."); } else {
		 * throw new ProgrammerException(e); } }
		 */
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
	public Site findSite(String siteCode) throws HttpException {
		return (Site) Hiber
				.session()
				.createQuery(
						"from Site as site where site.organization = :organization and site.code.string = :siteCode")
				.setEntity("organization", this).setString("siteCode",
						siteCode.toString()).uniqueResult();
	}

	public Site getSite(Long siteId) throws HttpException {
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
						"from Site site where site.organization = :organization order by site.code")
				.setEntity("organization", this).setMaxResults(50).list();
	}

	@SuppressWarnings("unchecked")
	public List<Site> findSites(String searchTerm) throws HttpException {
		return (List<Site>) Hiber
				.session()
				.createQuery(
						"from Site site where site.organization = :organization and lower(site.code || ' ' || site.name) like '%' || lower(:searchTerm) || '%' order by site.code")
				.setEntity("organization", this).setString("searchTerm",
						searchTerm).setMaxResults(50).list();
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ORGANIZATIONS_INSTANCE.getUri().resolve(getUriId())
				.append("/");
	}

	public Sites getSitesInstance() {
		return new Sites(this);
	}

	public Supplies suppliesInstance() {
		return new Supplies(this);
	}

	public HhdcContracts hhdcContractsInstance() {
		return new HhdcContracts(this);
	}

	public SupplierContracts supplierContractsInstance() {
		return new SupplierContracts(this);
	}

	public MopContracts mopContractsInstance() {
		return new MopContracts(this);
	}

	public UseDeltas useDeltasInstance() {
		return new UseDeltas(this);
	}

	public GenDeltas genDeltasInstance() {
		return new GenDeltas(this);
	}

	public HhdcContract getHhdcContract(long id) throws HttpException {
		HhdcContract contract = (HhdcContract) Hiber
				.session()
				.createQuery(
						"from HhdcContract contract where contract.organization = :organization and contract.id = :contractId")
				.setEntity("organization", this).setLong("contractId", id)
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException(
					"There isn't an HHDC contract with the id " + id);
		}
		return contract;
	}

	public HhdcContract getHhdcContract(String name) throws HttpException {
		HhdcContract contract = (HhdcContract) Hiber
				.session()
				.createQuery(
						"from HhdcContract contract where contract.organization = :organization and contract.name = :name")
				.setEntity("organization", this).setString("name", name)
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException("There isn't an HHDC contract called '"
					+ name + "'");
		}
		return contract;
	}

	public SupplierContract getSupplierContract(String name)
			throws HttpException {
		SupplierContract contract = (SupplierContract) Hiber
				.session()
				.createQuery(
						"from SupplierContract contract where contract.organization = :organization and contract.name = :name")
				.setEntity("organization", this).setString("name", name)
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException("There's no supplier contract named '"
					+ name + "' for this organization.");
		}
		return contract;
	}

	public Supply getSupply(long id) throws InternalException,
			NotFoundException {
		Supply supply = findSupply(id);
		if (supply == null) {
			throw new NotFoundException("There is no supply with that id.");
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
	/*
	 * public Supplier getSupplier(long supplierId) throws HttpException,
	 * InternalException { Supplier supplier = findSupplier(supplierId); if
	 * (supplier == null) { throw new NotFoundException( "There isn't a supplier
	 * attached to this organization with the id '" + supplierId + "'."); }
	 * return supplier; }
	 * 
	 * public Supplier findSupplier(long supplierId) throws HttpException,
	 * InternalException { return (Supplier) Hiber .session() .createQuery(
	 * "from Supplier supplier where supplier.organization = :organization and
	 * supplier.id = :supplierId") .setEntity("organization",
	 * this).setLong("supplierId", supplierId).uniqueResult(); }
	 */
	public void httpPost(Invocation inv) throws HttpException {
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

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Sites.URI_ID.equals(uriId)) {
			return new Sites(this);
		} else if (Supplies.URI_ID.equals(uriId)) {
			return new Supplies(this);
		} else if (HeaderImportProcesses.URI_ID.equals(uriId)) {
			return new HeaderImportProcesses(this);
		} else if (Reports.URI_ID.equals(uriId)) {
			return new Reports(this);
		} else if (UseDeltas.URI_ID.equals(uriId)) {
			return new UseDeltas(this);
		} else if (GenDeltas.URI_ID.equals(uriId)) {
			return new GenDeltas(this);
		} else if (HhdcContracts.URI_ID.equals(uriId)) {
			return new HhdcContracts(this);
		} else if (SupplierContracts.URI_ID.equals(uriId)) {
			return new SupplierContracts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException {
		// TODO Auto-generated method stub
	}

	public Site getSite(String code) throws HttpException {
		Site site = findSite(code);
		if (site == null) {
			throw new NotFoundException("The site '" + code
					+ "' cannot be found.");
		}
		return site;
	}

	@SuppressWarnings("unchecked")
	public void deleteSite(Site site) throws InternalException, HttpException {
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

	public Account getAccount(Provider provider, String accountReference)
			throws HttpException {
		Account account = (Account) Hiber
				.session()
				.createQuery(
						"from Account account where account.organization = :organization and account.provider = :provider and account.reference = :accountReference")
				.setEntity("organization", this)
				.setEntity("provider", provider).setString("accountReference",
						accountReference).uniqueResult();
		if (account == null) {
			throw new NotFoundException();
		}
		return account;
	}

	/*
	 * public void deleteSupplier(Supplier supplier) throws InternalException,
	 * HttpException { if (supplier.getOrganization().equals(this)) {
	 * Hiber.session().delete(supplier); } else { throw new UserException( "This
	 * supplier doesn't belong to this organization."); } }
	 */
	/*
	 * public Supplier insertSupplier(String name) throws HttpException,
	 * InternalException { if (findSupplier(name) == null) { Supplier supplier =
	 * new Supplier(this, name); Hiber.session().save(supplier); Hiber.flush();
	 * return supplier; } else { throw new UserException( "There's already a
	 * supplier with this name."); } }
	 * 
	 * public Supplier findSupplier(String name) { return (Supplier) Hiber
	 * .session() .createQuery( "from Supplier supplier where
	 * supplier.organization = :organization and supplier.name = :name")
	 * .setEntity("organization", this).setString("name", name) .uniqueResult(); }
	 */
	public HhdcContract insertHhdcContract(Provider provider, String name,
			HhEndDate startDate, String chargeScript,
			ContractFrequency frequency, int lag) throws HttpException {
		HhdcContract contract = new HhdcContract(provider, this, name,
				startDate, chargeScript, frequency, lag);
		Hiber.session().save(contract);
		Hiber.flush();
		return contract;
	}

	public SupplierContract insertSupplierContract(Provider provider,
			String name, HhEndDate startDate, String chargeScript)
			throws HttpException {
		SupplierContract contract = new SupplierContract(provider, this, name,
				startDate, chargeScript);
		Hiber.session().save(contract);
		Hiber.flush();
		return contract;
	}

	/*
	 * public Dcs insertDcs(String name) { Dcs dcs = new Dcs(name, this);
	 * Hiber.session().save(dcs); Hiber.flush(); return dcs; }
	 */
	public MopContract insertMopContract(Provider provider, String name,
			HhEndDate startDate, String chargeScript) throws HttpException {
		MopContract contract = new MopContract(provider, this, name, startDate,
				chargeScript);
		Hiber.session().save(contract);
		Hiber.flush();
		return contract;
	}

	@SuppressWarnings("unchecked")
	public MpanCore findMpanCore(MpanCoreRaw core) throws InternalException,
			HttpException {
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

	public MpanCore getMpanCore(MpanCoreRaw coreRaw) throws HttpException,
			InternalException {
		MpanCore core = findMpanCore(coreRaw);
		if (core == null) {
			throw new UserException("There isn't an MPAN with the core " + core);
		}
		return core;
	}

	/*
	 * public Supplier getSupplier(String name) throws HttpException,
	 * InternalException { Supplier supplier = (Supplier) Hiber .session()
	 * .createQuery( "from Supplier supplier where supplier.organization =
	 * :organization and supplier.name = :name") .setEntity("organization",
	 * this).setString("name", name) .uniqueResult(); if (supplier == null) {
	 * throw new NotFoundException( "There isn't a supplier with the name '" +
	 * name + "'."); } return supplier; }
	 */
}