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

import net.sf.chellow.data08.MpanCoreTerm;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Supplies implements Urlable, XmlDescriber {
	// private static final int PAGE_SIZE = 25;

	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("supplies");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
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

	public MonadUri getUrlPath() throws InternalException, HttpException {
		return organization.getUri().resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(organization.toXml(doc));
		if (inv.hasParameter("search-pattern")) {
			MpanCoreTerm pattern = inv.getValidatable(MpanCoreTerm.class,
					"search-pattern");
			for (Object[] array : (List<Object[]>) Hiber
					.session()
					.createQuery(
							"select distinct mpanCore,mpanCore.dso.code.string, mpanCore.uniquePart.string, mpanCore.checkDigit.character from MpanCore mpanCore join mpanCore.supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and lower(mpanCore.dso.code.string || mpanCore.uniquePart.string || mpanCore.checkDigit.character) like lower(:term) order by mpanCore.dso.code.string, mpanCore.uniquePart.string, mpanCore.checkDigit.character")
					.setEntity("organization", organization).setString("term",
							"%" + pattern.toString() + "%").setMaxResults(50)
					.list()) {
				source.appendChild(((MpanCore) array[0]).toXml(doc, new XmlTree(
								"supply").put("dso")));
			}
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			MethodNotAllowedException {
		throw new MethodNotAllowedException();
	}

	/*
	 * @SuppressWarnings("unchecked") public List<Supply> findSupplies() {
	 * return (List<Supply>) Hiber.session().createQuery( "from Supply supply
	 * where supply.organization = :organization") .setEntity("organization",
	 * organization).list(); }
	 * 
	 * @SuppressWarnings("unchecked") public List<Supply> findSupplies(int
	 * page) { return (List<Supply>) Hiber .session() .createQuery( "select
	 * supply from Supply supply join supply.generations generation join
	 * generation.siteSupplyGenerations siteSupplyGeneration where
	 * siteSupplyGeneration.site.organization = :organization")
	 * .setEntity("organization", organization).setFirstResult( page *
	 * PAGE_SIZE).setMaxResults(PAGE_SIZE).list(); }
	 */
	public Supply getChild(UriPathElement uriId) throws InternalException, NotFoundException {
		return organization.getSupply(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getUri() throws HttpException {
		return organization.getUri().resolve(getUriId());
	}

	public Node toXml(Document doc) throws InternalException {
		Element element = doc.createElement("supplies");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}
}