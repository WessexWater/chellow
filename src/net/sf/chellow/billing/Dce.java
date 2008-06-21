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
import net.sf.chellow.physical.ContractFrequency;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.SupplyGeneration;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dce extends ProviderOrganization {
	public static Dce getDce(Long id) throws InternalException, UserException {
		Dce dce = findDce(id);
		if (dce == null) {
			throw new UserException("There isn't a DCE with that id.");
		}
		return dce;
	}
	
	public static Dce findDce(Long id) {
		return (Dce) Hiber.session().get(Dce.class, id);
	}

	public static Dce getDce(String name) throws InternalException, UserException {
		Dce dce = findDce(name);
		if (dce == null) {
			throw new UserException("There isn't a DCE called '" + name
					+ "'.");
		}
		return dce;
	}

	public static Dce findDce(String name) throws InternalException {
		Dce dce = (Dce) Hiber.session().createQuery(
				"from Dce dce where dce.name = :name").setString("name", name)
				.uniqueResult();
		return dce;
	}

	public static void deleteDce(Dce supplier) throws InternalException {
		try {
			Hiber.session().delete(supplier);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	public Dce() {
		setTypeName("dce");
	}

	public Dce(String name, Organization organization) {
		super(name, organization);
	}

	public void httpPost(Invocation inv) throws InternalException {
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("organization")));
		return doc;
	}

	public MonadUri getUri() throws InternalException, UserException {
		return getOrganization().dcesInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (DceServices.URI_ID.equals(uriId)) {
			return new DceServices(this);
		} else if (Accounts.URI_ID.equals(uriId)) {
			return new Accounts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		deleteDce(this);
		inv.sendOk();
	}

	public DceService insertService(int type, String name, HhEndDate startDate,
			String chargeScript, ContractFrequency frequency, int lag)
			throws HttpException, InternalException, DesignerException {
		if (findService(name) != null) {
			throw new UserException
					("There's already a service with that name.");
		}
		DceService dceService = new DceService(type, name, startDate,
				chargeScript, this, frequency, lag);
		Hiber.session().save(dceService);
		Hiber.flush();
		return dceService;
	}

	public DceServices servicesInstance() {
		return new DceServices(this);
	}

	public DceService getService(String name) throws HttpException,
			InternalException {
		DceService service = findService(name);
		if (service == null) {
			throw new NotFoundException
					("There isn't a DCE service with that id.");
		}
		return service;
	}

	public DceService findService(String name) throws HttpException,
			InternalException {
		return (DceService) Hiber
				.session()
				.createQuery(
						"from DceService service where service.provider = :dce and service.name = :name")
				.setEntity("dce", this).setString("name", name).uniqueResult();
	}

	@Override
	public List<SupplyGeneration> supplyGenerations(Account account) {
		// TODO Auto-generated method stub
		return null;
	}

}