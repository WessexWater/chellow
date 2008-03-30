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

package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Supplies implements Urlable, XmlDescriber {
	private static final int PAGE_SIZE = 25;

	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("supplies");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);		}
	}

	private Organization organization;

	Supplies(Organization organization) {
		setOrganization(organization);
	}

	public Organization getOrganization() {
		return organization;
	}

	protected void setOrganization(Organization organization) {
		this.organization = organization;
	}

	public MonadUri getUrlPath() throws ProgrammerException, UserException {
		return organization.getUri().resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element suppliesElement = (Element) toXML(doc);
		source.appendChild(suppliesElement);
		suppliesElement.appendChild(organization.toXML(doc));
		int page = 0;
		if (inv.hasParameter("page")) {
			page = inv.getInteger("page");
		}
		for (Supply supply : findSupplies(page)) {
			suppliesElement.appendChild(supply.getXML(new XmlTree("source"),
					doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	@SuppressWarnings("unchecked")
	public List<Supply> findSupplies() {
		return (List<Supply>) Hiber.session().createQuery(
				"from Supply supply where supply.organization = :organization")
				.setEntity("organization", organization).list();
	}

	@SuppressWarnings("unchecked")
	public List<Supply> findSupplies(int page) {
		return (List<Supply>) Hiber
				.session()
				.createQuery(
						"select supply from Supply supply join supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization")
				.setEntity("organization", organization).setFirstResult(
						page * PAGE_SIZE).setMaxResults(PAGE_SIZE).list();
	}

	public Supply getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		return organization.getSupply(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return organization.getUri().resolve(getUriId());
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = doc.createElement("supplies");
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}