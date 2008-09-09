/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
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
public class DsoService extends Service {
	public static DsoService getDsoService(Long id) throws HttpException {
		DsoService service = findDsoService(id);
		if (service == null) {
			throw new UserException("There isn't a DSO service with that id.");
		}
		return service;
	}

	public static DsoService findDsoService(Long id) throws HttpException {
		return (DsoService) Hiber.session().get(DsoService.class, id);
	}
	
	private Dso dso;

	public DsoService() {
	}

	public DsoService(Dso dso, String name, HhEndDate startDate,
			String chargeScript) throws HttpException {
		super(name, startDate,
				chargeScript);
		internalUpdate(dso, name, startDate, chargeScript);
	}
	
	void setDso(Dso dso) {
		this.dso = dso;
	}
	
	public Dso getDso() {
		return dso;
	}

	protected void internalUpdate(Dso dso, String name,
			HhEndDate startDate, String chargeScript) throws HttpException {
		setDso(dso);
		super.internalUpdate(name, chargeScript);
	}

	@SuppressWarnings("unchecked")
	public void update(String name, String chargeScript) throws HttpException {
		super.update(name, chargeScript);
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
		if (obj instanceof DsoService) {
			DsoService contract = (DsoService) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws HttpException {
		return dso.servicesInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void delete() throws HttpException {
		super.delete();
		Hiber.session().delete(this);
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendFound(dso.servicesInstance().getUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			try {
				update(name, chargeScript);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("dso")));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public String toString() {
		return "Service id " + getId() + " " + dso + " name "
				+ getName();
	}

	public Element toXml(Document doc) throws HttpException {
		return super.toXml(doc, "dso-service");
	}
}