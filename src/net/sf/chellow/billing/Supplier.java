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
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
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
	public static Supplier findSupplier(Long id) throws InternalException {
		return (Supplier) Hiber.session().get(Supplier.class, id);
	}

	public static void deleteSupplier(Supplier supplier)
			throws InternalException {
		try {
			Hiber.session().delete(supplier);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	Supplier() {
	}

	public Supplier(Organization organization, String name) {
		super(name, organization);
	}

	public SupplierService getService(String name) throws HttpException,
			InternalException {
		SupplierService service = (SupplierService) Hiber
				.session()
				.createQuery(
						"from SupplierService service where service.provider = :provider and service.name = :name")
				.setEntity("provider", this).setString("name", name)
				.uniqueResult();
		if (service == null) {
			throw new UserException("The supplier '" + getName()
					+ "' doesn't have " + "the service '" + name + "'.");
		}
		return service;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			getOrganization().deleteSupplier(this);
			Hiber.commit();
			inv.sendSeeOther(getOrganization().suppliersInstance().getUri());
		} else if (inv.hasParameter("name")) {
			String name = inv.getString("name");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(name);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("organization")));
		return doc;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return getOrganization().suppliersInstance().getUri().resolve(
				getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		if (SupplierServices.URI_ID.equals(uriId)) {
			return new SupplierServices(this);
		} else if (Accounts.URI_ID.equals(uriId)) {
			return new Accounts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		deleteSupplier(this);
		inv.sendOk();
	}

	public SupplierService insertService(String name, HhEndDate startDate,
			String chargeScript) throws HttpException, InternalException,
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

	public void deleteAccount(String reference) throws HttpException,
			InternalException {
		Account account = getAccount(reference);
		if (((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from Mpan mpan where mpan.supplierAccount = :supplierAccount")
				.setEntity("supplierAccount", account).uniqueResult()) > 0) {
			throw new UserException
					("An account can't be deleted if there are still MPANs attached to it.");
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

	public Element toXml(Document doc) throws InternalException,
			HttpException {
		setTypeName("supplier");
		return super.toXml(doc);
	}
}