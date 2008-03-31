/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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
import net.sf.chellow.physical.Dso;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Mpan;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class DnoService extends Service {
	public static DnoService getDsoService(Long id) throws UserException,
			ProgrammerException {
		DnoService service = findDsoService(id);
		if (service == null) {
			throw UserException
					.newOk("There isn't a DSO service with that id.");
		}
		return service;
	}

	public static DnoService findDsoService(Long id) throws UserException,
			ProgrammerException {
		return (DnoService) Hiber.session().get(DnoService.class, id);
	}

	private Dso provider;

	public DnoService() {
		setTypeName("dso-service");
	}

	public DnoService(String name, HhEndDate startDate, String chargeScript,
			Dso provider) throws UserException, ProgrammerException,
			DesignerException {
		super(Service.TYPE_PASS_THROUGH, name, startDate, chargeScript);
		setProvider(provider);
	}

	public Dso getProvider() {
		return provider;
	}

	void setProvider(Dso provider) {
		this.provider = provider;
	}

	@SuppressWarnings("unchecked")
	public void update(String name, String chargeScript) throws UserException,
			ProgrammerException, DesignerException {
		super.update(Service.TYPE_PASS_THROUGH, name, chargeScript);
		Hiber.flush();
		/*
		 * Long numInSpace = null; if (finishDate == null) { numInSpace = (Long)
		 * Hiber .session() .createQuery( "select count(*) from DsoService
		 * service where service.provider = :dso and (service.finishDate.date is
		 * null or service.finishDate.date >= :startDate)") .setEntity("dso",
		 * getProvider()).setTimestamp("startDate",
		 * startDate.getDate()).uniqueResult(); } else { numInSpace = (Long)
		 * Hiber .session() .createQuery( "select count(*) from DsoService
		 * service where service.dso = :dso and service.startDate.date <=
		 * :finishDate and (service.finishDate.date is null or
		 * service.finishDate.date >= :startDate)") .setEntity("provider",
		 * getProvider()).setTimestamp( "startDate",
		 * startDate.getDate()).setTimestamp( "finishDate",
		 * finishDate.getDate()).uniqueResult(); } if (numInSpace > 1) { throw
		 * UserException .newInvalidParameter("With these start and finish
		 * dates, the service would overlap with other services and that can't
		 * happen with DSOs"); }
		 */
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof DnoService) {
			DnoService contract = (DnoService) obj;
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

	@Override
	public List<Mpan> getMpans(Account account, HhEndDate from, HhEndDate to) {
		// TODO Auto-generated method stub
		return null;
	}
}