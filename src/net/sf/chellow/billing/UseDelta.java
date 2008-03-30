/*
 
 Copyright 2005 Meniscus Systems Ltd
 
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

import java.util.Date;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadInteger;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.Site;
import net.sf.chellow.physical.SiteCode;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class UseDelta extends PersistentEntity implements Urlable {
	public static UseDelta getUseDelta(Long id) throws UserException,
			ProgrammerException {
		UseDelta useDelta = (UseDelta) Hiber.session().get(UseDelta.class, id);
		if (useDelta == null) {
			throw UserException.newOk("There isn't an account with that id.");
		}
		return useDelta;
	}

	public static void deleteUseDelta(UseDelta useDelta)
			throws ProgrammerException {
		try {
			Hiber.session().delete(useDelta);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	private Organization organization;

	private Site site;

	private HhEndDate startDate;

	private int kwhPerMonth;

	public UseDelta() {
		setTypeName("use-delta");
	}

	public UseDelta(Organization organization, Site site, HhEndDate startDate,
			int kwhPerMonth) {
		this();
		setOrganization(organization);
		update(site, startDate, kwhPerMonth);
	}

	public Organization getOrganization() {
		return organization;
	}

	public void setOrganization(Organization organization) {
		this.organization = organization;
	}

	public Site getSite() {
		return site;
	}

	public void setSite(Site site) {
		this.site = site;
	}

	public HhEndDate getStartDate() {
		return startDate;
	}

	protected void setStartDate(HhEndDate startDate) {
		this.startDate = startDate;
	}

	public int getKwhPerMonth() {
		return kwhPerMonth;
	}

	public void setKwhPerMonth(int kwhPerMonth) {
		this.kwhPerMonth = kwhPerMonth;
	}

	public void update(Site site, HhEndDate startDate, int kwhPerMonth) {
		setSite(site);
		setStartDate(startDate);
		setKwhPerMonth(kwhPerMonth);
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);
		startDate.setLabel("start");
		element.appendChild(startDate.toXML(doc));
		element.setAttributeNode(MonadInteger.toXml(doc, "kwh-per-month",
				kwhPerMonth));
		return element;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		String siteCode = inv.getString("site-code");
		Date date = inv.getDate("start-date");
		int kwhPerMonth = inv.getInteger("kwh-per-month");
		if (!inv.isValid()) {
			throw UserException.newInvalidParameter(document());
		}
		update(organization.getSite(new SiteCode(siteCode)), HhEndDate
				.roundUp(date), kwhPerMonth);
		Hiber.commit();
		inv.sendOk(document());
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source
				.appendChild(getXML(new XmlTree("organization").put("site"),
						doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return organization.useDeltasInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		throw UserException.newNotFound();
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		deleteUseDelta(this);
		inv.sendOk();
	}
}