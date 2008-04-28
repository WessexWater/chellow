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

package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.SupplyGeneration;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Supplier extends ProviderOrganization {
	public static Supplier findSupplier(Long id) throws UserException,
			ProgrammerException {
		return (Supplier) Hiber.session().get(Supplier.class, id);
	}

	public static void deleteSupplier(Supplier supplier)
			throws ProgrammerException {
		try {
			Hiber.session().delete(supplier);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	Supplier() {
	}

	public Supplier(Organization organization, String name) {
		super(name, organization);
	}

	public SupplierService getService(String name) throws UserException,
			ProgrammerException {
		SupplierService service = (SupplierService) Hiber
				.session()
				.createQuery(
						"from SupplierService service where service.provider = :provider and service.name = :name")
				.setEntity("provider", this).setString("name", name)
				.uniqueResult();
		if (service == null) {
			throw UserException.newOk("The supplier '" + getName()
					+ "' doesn't have " + "the service '" + name + "'.");
		}
		return service;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		if (inv.hasParameter("delete")) {
			getOrganization().deleteSupplier(this);
			Hiber.commit();
			inv.sendSeeOther(getOrganization().suppliersInstance().getUri());
		} else if (inv.hasParameter("name")) {
			String name = inv.getString("name");
			if (!inv.isValid()) {
				throw UserException.newInvalidParameter(document());
			}
			update(name);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(getXML(new XmlTree("organization"), doc));
		return doc;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return getOrganization().suppliersInstance().getUri().resolve(
				getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (SupplierServices.URI_ID.equals(uriId)) {
			return new SupplierServices(this);
		} else if (Accounts.URI_ID.equals(uriId)) {
			return new Accounts(this);
		} else {
			throw UserException.newNotFound();
		}
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		deleteSupplier(this);
		inv.sendOk();
	}

	public SupplierService insertService(String name, HhEndDate startDate,
			String chargeScript) throws UserException, ProgrammerException,
			DesignerException {
		SupplierService service = new SupplierService(name, startDate,
				chargeScript, this);
		Hiber.session().save(service);
		Hiber.flush();
		return service;
	}

	public SupplierServices servicesInstance() {
		return new SupplierServices(this);
	}

	public void deleteAccount(String reference) throws UserException,
			ProgrammerException {
		Account account = getAccount(reference);
		if (((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from Mpan mpan where mpan.supplierAccount = :supplierAccount")
				.setEntity("supplierAccount", account).uniqueResult()) > 0) {
			throw UserException
					.newInvalidParameter("An account can't be deleted if there are still MPANs attached to it.");
		}
		Hiber.session().delete(account);
		Hiber.flush();
	}

	@SuppressWarnings("unchecked")
	@Override
	public List<SupplyGeneration> supplyGenerations(Account account) {
		return Hiber
				.session()
				.createQuery(
						"select mpan.supplyGeneration from Mpan mpan where mpan.supplierAccount = :account order by mpan.supplyGeneration.startDate.date")
				.setEntity("account", account).list();
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		setTypeName("supplier");
		return super.toXML(doc);
	}
}