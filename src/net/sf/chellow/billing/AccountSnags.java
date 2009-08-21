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
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.Snag;

import org.hibernate.ScrollMode;
import org.hibernate.ScrollableResults;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class AccountSnags extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("snags");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Account account;

	public AccountSnags(Account account) {
		this.account = account;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return account.getUri().resolve(getUriId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element snagsElement = toXml(doc);
		source.appendChild(snagsElement);
		snagsElement.appendChild(account.toXml(doc, new XmlTree("contract",
				new XmlTree("party"))));

		for (AccountSnag snag : (List<AccountSnag>) Hiber
				.session()
				.createQuery(
						"from AccountSnag snag where snag.account = :account order by snag.account.reference, snag.description, snag.startDate.date")
				.setEntity("account", account).list()) {
			snagsElement.appendChild(snag.toXml(doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("ignore")) {
			MonadDate ignoreDate = inv.getMonadDate("ignore-date");

			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from AccountSnag snag where snag.contract = :contract and snag.finishDate < :ignoreDate")
					.setEntity("contract", account).setTimestamp("ignoreDate",
							ignoreDate.getDate()).scroll(
							ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				AccountSnag snag = (AccountSnag) snags.get(0);
				snag.setIsIgnored(true);
				Hiber.session().flush();
				Hiber.session().clear();
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		return Snag.getSnag(urlId.getString());
	}

	public MonadUri getMonadUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("account-snags");
	}
}
