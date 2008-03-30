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

import java.util.Date;
import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

@SuppressWarnings("serial")
public class RateScripts implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("rate-scripts");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	private Service service;

	public RateScripts(Service service) {
		setService(service);
	}

	public Service getService() {
		return service;
	}

	void setService(Service service) {
		this.service = service;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return service.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		String script = inv.getString("script");
		Date startDate = inv.getDate("start-date");
		if (!inv.isValid()) {
			throw UserException.newInvalidParameter(document());
		}
		try {
			RateScript rateScript = service.insertRateScript(HhEndDate
					.roundDown(startDate).getNext(), script);
			Hiber.commit();
			Hiber.flush();
			inv.sendCreated(document(), rateScript.getUri());
		} catch (UserException e) {
			Hiber.rollBack();
			e.setDocument(document());
			throw e;
		}
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public RateScript getChild(UriPathElement uriId) throws UserException,
			ProgrammerException {
		RateScript script = (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.service = :service and script.id = :scriptId")
				.setEntity("service", service).setLong("scriptId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (script == null) {
			throw UserException.newNotFound();
		}
		return script;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element batchesElement = doc.createElement("rate-scripts");
		return batchesElement;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		return null;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element batchesElement = (Element) toXML(doc);
		source.appendChild(batchesElement);
		Provider provider = service.getProvider();
		if (provider instanceof ProviderOrganization) {
			batchesElement.appendChild(service.getXML(new XmlTree("provider",
					new XmlTree("organization")), doc));
		} else {
			batchesElement.appendChild(service.getXML(new XmlTree("provider"),
					doc));
		}
		for (RateScript script : (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.service = :service order by script.startDate.date")
				.setEntity("service", service).list()) {
			batchesElement.appendChild(script.toXML(doc));
		}
		source.appendChild(new MonadDate().toXML(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}
}