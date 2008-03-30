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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Mop extends ProviderOrganization {
	public static Mop getMop(Long id) throws UserException,
			ProgrammerException {
		Mop mop = (Mop) Hiber.session().get(Mop.class, id);
		if (mop == null) {
			throw UserException.newOk("There isn't a meter operator with that id.");
		}
		return mop;
	}

	public static void deleteMop(Mop mop)
			throws ProgrammerException {
		try {
			Hiber.session().delete(mop);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	public Mop() {
		setTypeName("mop");
	}

	public Mop(String name, Organization organization) {
		super(name, organization);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}
	
	private Document document() throws ProgrammerException, UserException, DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXML(doc));
		return doc;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return Chellow.MOPS_INSTANCE.getUri().resolve(getUriId())
				.append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		throw UserException.newNotFound();
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		deleteMop(this);
		inv.sendOk();
	}
	
	public MopServices contractsInstance() {
		return new MopServices(this);
	}
	
	public MopService insertService(int type, String name, HhEndDate startDate, String chargeScript) throws UserException, ProgrammerException, DesignerException {
		MopService service = new MopService(type, name, startDate, chargeScript, this);
		Hiber.session().save(service);
		Hiber.flush();
		return service;
	}

	@Override
	public List<SupplyGeneration> supplyGenerations(Account account) {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public MopService getService(String name) throws UserException, ProgrammerException {
		return (MopService) Hiber.session().createQuery("from MopService service where service.provider = :provider and service.name = :serviceName").setEntity("provider", this).setString("serviceName", name).uniqueResult();
	}
}