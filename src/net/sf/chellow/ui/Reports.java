/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2013 Wessex Water Services Limited
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
package net.sf.chellow.ui;

import java.net.URI;
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Reports extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("reports");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Reports() {
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportsElement = toXml(doc);

		source.appendChild(reportsElement);
		for (Report report : (List<Report>) Hiber.session().createQuery(
				"from Report report order by mod(report.id, 2) desc, report.name").list()) {
			reportsElement.appendChild(report.toXml(doc));
		}
		return doc;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.getUrlableRoot().getEditUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		boolean isCore = inv.getBoolean("is-core");
		String name = inv.getString("name");
		try {
			Report report = Report.insertReport(null, isCore, name, "", null);
			Hiber.commit();
			inv.sendSeeOther(report.getEditUri());
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return Report.getReport(new Long(uriId.toString()));
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("reports");
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}