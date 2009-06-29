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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Bills extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("bills");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Account account;

	public Bills(Account account) {
		setAccount(account);
	}

	public Account getAccount() {
		return account;
	}

	void setAccount(Account account) {
		this.account = account;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return account.getUri().resolve(getUrlId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billsElement = toXml(doc);
		source.appendChild(billsElement);
		billsElement.appendChild(account.toXml(doc, new XmlTree("contract", new XmlTree("party"))));
		for (Bill bill : (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account order by bill.startDate.date")
				.setEntity("account", account).list()) {
			billsElement.appendChild(bill.toXml(doc, new XmlTree("account")));
		}
		return doc;
	}

	public Bill getChild(UriPathElement uriId) throws HttpException {
		Bill bill = (Bill) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account and bill.id = :billId")
				.setEntity("account", account).setLong("billId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (bill == null) {
			throw new NotFoundException();
		}
		return bill;
	}

	public Element toXml(Document doc) throws HttpException {
		Element billsElement = doc.createElement("bills");
		return billsElement;
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
		
	}
}
