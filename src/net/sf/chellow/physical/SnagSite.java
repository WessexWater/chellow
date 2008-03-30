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

package net.sf.chellow.physical;

import net.sf.chellow.billing.DceService;
import net.sf.chellow.billing.Service;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;


public class SnagSite extends SnagDateBounded {
	public static void insertSnagSite(SnagSite snag) {
		Hiber.session().save(snag);
	}

	public static void deleteSnagSite(SnagSite snag) {
		Hiber.session().delete(snag);
	}

	private Site site;
	
	private DceService dceService;

	public SnagSite() {
		setTypeName("snag-site");
	}

	public SnagSite(String description, DceService dceService,
			Site site, HhEndDate startDate, HhEndDate finishDate)
			throws ProgrammerException, UserException {
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

	
	public Element toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);

		return element;
	}
	
	public SnagSite copy() throws ProgrammerException {
		SnagSite cloned;
		try {
			cloned = (SnagSite) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new ProgrammerException(e);
		}
		cloned.setId(null);
		return cloned;
	}
	public String toString() {
		return super.toString() + " Contract: " + getService();
	}

	public void httpGet(Invocation inv) throws DesignerException, ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}
	
	private Document document() throws ProgrammerException, UserException, DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(getXML(new XmlTree("service", new XmlTree(
				"provider", new XmlTree("organization"))).put("site"), doc));
		return doc;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException, DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub
		
	}
	public MonadUri getUri() throws ProgrammerException, UserException {
		return getService().getSnagsSiteInstance().getUri().resolve(getUriId()).append("/");
	}
}
