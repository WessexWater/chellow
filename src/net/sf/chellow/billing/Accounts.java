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
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

@SuppressWarnings("serial")
public class Accounts implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
			try {
				URI_ID = new UriPathElement("accounts");
			} catch (HttpException e) {
				throw new RuntimeException(e);
			}
	}

	private ProviderOrganization provider;

	public Accounts(ProviderOrganization provider) {
		this.provider = provider;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return provider.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		String reference = inv.getString("reference");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Account account = provider.insertAccount(reference);
		Hiber.commit();
		inv.sendCreated(document(), account.getUri());
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public Account getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		Account account = (Account) Hiber
				.session()
				.createQuery(
						"from Account account where account.provider = :provider and account.id = :accountId")
				.setEntity("provider", provider).setLong("accountId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (account == null) {
			throw new NotFoundException();
		}
		return account;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element accountsElement = doc.createElement("accounts");
		return accountsElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		return null;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element accountsElement = (Element) toXml(doc);
		source.appendChild(accountsElement);
		accountsElement.appendChild(provider.toXml(
				doc, new XmlTree("organization")));
		for (Account account : (List<Account>) Hiber
				.session()
				.createQuery(
						"from Account account where account.provider = :provider order by account.reference")
				.setEntity("provider", provider).list()) {
			accountsElement.appendChild(account.toXml(doc));
		}
		return doc;
	}
}