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

package net.sf.chellow.physical;

import net.sf.chellow.billing.DceService;
import net.sf.chellow.billing.Service;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SiteSnag extends SnagDateBounded {
	public static void insertSiteSnag(SiteSnag snag) {
		Hiber.session().save(snag);
	}

	public static SiteSnag getSiteSnag(Long id) throws HttpException {
		SiteSnag snag = (SiteSnag) Hiber.session().get(SiteSnag.class, id);
		
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}
	
	private Site site;

	private DceService dceService;

	public SiteSnag() {
	}

	public SiteSnag(String description, DceService dceService, Site site,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		super(description, startDate, finishDate);
		this.site = site;
		this.dceService = dceService;
	}

	public Site getSite() {
		return site;
	}

	void setSite(Site site) {
		this.site = site;
	}

	public DceService getService() {
		return dceService;
	}

	public void setService(DceService dceService) {
		this.dceService = dceService;
	}

	@Override
	public void setService(Service service) {
		setService((DceService) service);
	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		setTypeName("site-snag");
		Element element = (Element) super.toXml(doc);

		return element;
	}

	public SiteSnag copy() throws InternalException {
		SiteSnag cloned;
		try {
			cloned = (SiteSnag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return super.toString() + " Contract: " + getService();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("service",
				new XmlTree("provider", new XmlTree("organization")))
				.put("site")));
		return doc;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public MonadUri getUri() throws HttpException {
		return getService().getSnagsSiteInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void delete() {
		Hiber.session().delete(this);
	}
}