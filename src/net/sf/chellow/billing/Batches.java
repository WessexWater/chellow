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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;


@SuppressWarnings("serial")
public class Batches implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("batches");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	private Service service;

	public Batches(Service service) {
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
		String reference = inv.getString("reference");
		if (!inv.isValid()) {
			throw UserException.newInvalidParameter(document());
		}
		Batch batch = service.insertBatch(reference);
		Hiber.commit();
		inv.sendCreated(document(), batch.getUri());
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public Batch getChild(UriPathElement uriId) throws UserException,
			ProgrammerException {
		Batch batch = (Batch) Hiber
				.session()
				.createQuery(
						"from Batch batch where batch.service = :service and batch.id = :batchId")
				.setEntity("service", service).setLong("batchId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (batch == null) {
			throw UserException.newNotFound();
		}
		return batch;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element batchesElement = doc.createElement("batches");
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
		batchesElement.appendChild(service.getXML(new XmlTree("provider",
				new XmlTree("organization")), doc));
		for (Batch batch : (List<Batch>) Hiber
				.session()
				.createQuery(
						"from Batch batch where batch.service = :service order by batch.reference")
				.setEntity("service", service).list()) {
			batchesElement.appendChild(batch.toXML(doc));
		}
		return doc;
	}
}