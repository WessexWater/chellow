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

import java.util.Date;
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
import net.sf.chellow.ui.Chellow;

import org.hibernate.ScrollMode;
import org.hibernate.ScrollableResults;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SiteSnags extends EntityList {
	static private final int PAGE_SIZE = 20;

	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("site-snags");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public SiteSnags() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUriId()).append("/");
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
		for (SiteSnag snag : (List<SiteSnag>) Hiber
				.session()
				.createQuery(
						"from SiteSnag snag order by snag.startDate.date desc, snag.site.code, snag.description")
				.setMaxResults(PAGE_SIZE)
				.list()) {
			snagsElement.appendChild(snag.toXml(doc, new XmlTree("site")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("ignore")) {
			Date ignoreDate = inv.getDate("ignore-date");

			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from SiteSnag snag where snag.finishDate < :ignoreDate")
					.setTimestamp(
							"ignoreDate", ignoreDate).scroll(
							ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				SiteSnag snag = (SiteSnag) snags.get(0);
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
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("site-snags");
	}
}
