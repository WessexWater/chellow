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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dcs extends ProviderOrganization {
	public static Dcs getSupplier(Long id) throws HttpException {
		Dcs dcs = (Dcs) Hiber.session().get(Dcs.class, id);
		if (dcs == null) {
			throw new UserException("There isn't a DCS with that id.");
		}
		return dcs;
	}

	public static void deleteDcs(Dcs dcs) throws InternalException {
		try {
			Hiber.session().delete(dcs);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	public Dcs() {
		setTypeName("dcs");
	}

	public Dcs(String name, Organization organization) {
		super(name, organization);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		String name = inv.getString("name");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		update(name);
		Hiber.commit();
		inv.sendOk(document());
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		return doc;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.DCSS_INSTANCE.getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		throw new NotFoundException();
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		deleteSupplier(this);
		inv.sendOk();
	}

	public DcsServices contractsInstance() {
		return new DcsServices(this);
	}

	public DcsService insertContract(int type, String name, HhEndDate startDate,
			HhEndDate finishDate, String chargeScript) throws HttpException, InternalException, DesignerException {
		DcsService contract = new DcsService(type, name, startDate, finishDate, chargeScript,
				this);
		Hiber.session().save(contract);
		Hiber.flush();
		return contract;
	}

	@Override
	public List<SupplyGeneration> supplyGenerations(Account account) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public DcsService getService(String name) throws HttpException, InternalException {
		return (DcsService) Hiber.session().createQuery("from DcsService service where service.provider = :provider and service.name = :serviceName").setEntity("provider", this).setString("serviceName", name).uniqueResult();
	}
}