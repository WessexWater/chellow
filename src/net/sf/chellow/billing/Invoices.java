/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Invoices extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("invoices");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Batch batch;

	public Invoices(Batch batch) {
		setBatch(batch);
	}

	public Batch getBatch() {
		return batch;
	}

	void setBatch(Batch batch) {
		this.batch = batch;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return batch.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element invoicesElement = toXml(doc);
		source.appendChild(invoicesElement);
		invoicesElement.appendChild(batch.toXml(doc, new XmlTree("contract",
						new XmlTree("party"))));
		for (Invoice invoice : (List<Invoice>) Hiber
				.session()
				.createQuery(
						"from Invoice invoice where invoice.batch = :batch order by invoice.bill.account.reference")
				.setEntity("batch", batch).list()) {
			invoicesElement.appendChild(invoice.toXml(doc, new XmlTree("bill",
							new XmlTree("account"))));
		}
		return doc;
	}

	public Invoice getChild(UriPathElement uriId) throws HttpException {
		Invoice invoice = (Invoice) Hiber
				.session()
				.createQuery(
						"from Invoice invoice where invoice.batch = :batch and invoice.id = :invoiceId")
				.setEntity("batch", batch).setLong("invoiceId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (invoice == null) {
			throw new NotFoundException();
		}
		return invoice;
	}

	public Element toXml(Document doc) throws HttpException {
		Element billsElement = doc.createElement("invoices");
		return billsElement;
	}
}
