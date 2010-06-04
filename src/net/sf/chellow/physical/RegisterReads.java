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

package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.billing.Bill;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RegisterReads extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("reads");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Bill bill;

	public RegisterReads(Bill bill) {
		this.bill = bill;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return bill.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		/*
		 * String reference = inv.getString("reference"); if (!inv.isValid()) {
		 * throw UserException.newInvalidParameter(document()); } Account
		 * account = provider.insertAccount(reference); Hiber.commit();
		 * inv.sendCreated(document(), account.getUri());
		 */
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public RegisterRead getChild(UriPathElement uriId) throws HttpException {
		RegisterRead read = (RegisterRead) Hiber
				.session()
				.createQuery(
						"from RegisterRead read where read.bill = :bill and read.id = :readId")
				.setEntity("bill", bill).setLong("readId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (read == null) {
			throw new NotFoundException();
		}
		return read;
	}

	public Element toXml(Document doc) throws HttpException {
		Element accountsElement = doc.createElement("register-reads");
		return accountsElement;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element readsElement = toXml(doc);
		source.appendChild(readsElement);
		readsElement.appendChild(bill.toXml(doc, new XmlTree("batch",
				new XmlTree("contract", new XmlTree("party")))));
		for (RegisterRead read : (List<RegisterRead>) Hiber
				.session()
				.createQuery(
						"from RegisterRead read where read.bill = :bill order by read.presentDate.date, read.id")
				.setEntity("bill", bill).list()) {
			readsElement.appendChild(read.toXml(doc, new XmlTree("tpr")));
		}
		return doc;
	}
}