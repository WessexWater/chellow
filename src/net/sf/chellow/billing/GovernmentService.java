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

import net.sf.chellow.hhimport.HhDataImportProcesses;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class GovernmentService extends Service {

	private Government provider;

	public GovernmentService() {
		setTypeName("government-service");
	}

	public GovernmentService(String name, HhEndDate startDate,
			String chargeScript, Government provider) throws UserException,
			ProgrammerException, DesignerException {
		super(TYPE_CONTRACT, name, startDate, chargeScript);
		setProvider(provider);
	}

	public Government getProvider() {
		return provider;
	}

	void setProvider(Government provider) {
		this.provider = provider;
	}

	@SuppressWarnings("unchecked")
	public void update(String name, String chargeScript) throws UserException,
			ProgrammerException, DesignerException {
		super.update(Service.TYPE_PASS_THROUGH, name, chargeScript);
		Hiber.flush();
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof GovernmentService) {
			GovernmentService contract = (GovernmentService) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return getProvider().servicesInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void delete() throws UserException, ProgrammerException,
			DesignerException {
		super.delete();
		Hiber.session().delete(this);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendFound(getProvider().servicesInstance().getUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			if (!inv.isValid()) {
				throw UserException.newInvalidParameter(document());
			}
			try {
				update(name, chargeScript);
			} catch (UserException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(getXML(new XmlTree("provider"), doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXML(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public HhDataImportProcesses getHhDataImportProcessesInstance() {
		return new HhDataImportProcesses(this);
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else {
			throw UserException.newNotFound();
		}
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public String toString() {
		return "Service id " + getId() + " " + getProvider() + " name "
				+ getName();
	}
}