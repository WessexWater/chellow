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

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class Accounts extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("accounts");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Contract contract;

	public Accounts(Contract contract) {
		this.contract = contract;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return contract.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		String reference = inv.getString("reference");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Account account = contract.insertAccount(reference);
		Hiber.commit();
		inv.sendCreated(document(), account.getUri());
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Account getChild(UriPathElement uriId) throws HttpException {
		Account account = (Account) Hiber
				.session()
				.createQuery(
						"from Account account where account.contract = :contract and account.id = :accountId")
				.setEntity("contract", contract).setLong("accountId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (account == null) {
			throw new NotFoundException();
		}
		return account;
	}

	public Element toXml(Document doc) throws HttpException {
		Element accountsElement = doc.createElement("accounts");
		return accountsElement;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element accountsElement = toXml(doc);
		source.appendChild(accountsElement);
		accountsElement.appendChild(contract.toXml(doc));
		for (Account account : (List<Account>) Hiber
				.session()
				.createQuery(
						"from Account account where account.contract = :contract order by account.reference")
				.setEntity("contract", contract).list()) {
			accountsElement.appendChild(account.toXml(doc));
		}
		return doc;
	}
}