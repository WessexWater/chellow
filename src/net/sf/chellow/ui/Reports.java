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
package net.sf.chellow.ui;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;
import javax.servlet.http.HttpServletResponse;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
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
				"from Report report order by report.name").list()) {
			reportsElement.appendChild(report.toXml(doc));
		}
		return doc;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(URI_ID).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		if (inv.hasParameter("view")) {
			inv.getResponse().setStatus(HttpServletResponse.SC_OK);
			inv.getResponse().setContentType("text/plain");
			inv.getResponse().setHeader("Content-Disposition",
					"filename=reports.xml;");
			PrintWriter pw = null;
			try {
				pw = inv.getResponse().getWriter();
			} catch (IOException e) {
				throw new InternalException(e);
			}
			pw.println("<?xml version=\"1.0\"?>");
			pw.println("<csv>");
			pw.println("  <line>");
			pw.println("    <value>action</value>");
			pw.println("    <value>type</value>");
			pw.println("  </line>");
			pw.flush();
			for (Report report : (List<Report>) Hiber
					.session()
					.createQuery(
							"from Report report where report.name like '0 %' order by report.id")
					.list()) {
				pw.println("  <line>");
				pw.println("    <value>insert</value>");
				pw.println("    <value>report</value>");
				pw.println("    <value>" + report.getId() + "</value>");
				pw.println("    <value>" + report.getName() + "</value>");
				pw.println("    <value><![CDATA["
						+ report.getScript().replace("<![CDATA[",
								"&lt;![CDATA[").replace("]]>", "]]&gt;")
						+ "]]></value>");
				pw.print("    <value><![CDATA[");
				if (report.getTemplate() != null) {
					pw.print(report.getTemplate().replace("<![CDATA[",
							"&lt;![CDATA[").replace("]]>", "]]&gt;"));
				}
				pw.println("]]></value>");
				pw.println("  </line>");
			}
			pw.println("</csv>");
			pw.close();
		} else {
			inv.sendOk(document());
		}
	}

	public void httpPost(Invocation inv) throws HttpException {
		String name = inv.getString("name");
		try {
			Report report = Report.insertReport(null, name, "", null);
			Hiber.commit();
			inv.sendSeeOther(report.getUri());
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return Report.getReport(Long.parseLong(uriId.toString()));
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("reports");
	}
}