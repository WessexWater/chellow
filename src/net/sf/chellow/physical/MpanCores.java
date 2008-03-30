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

public class MpanCores implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("mpan-cores");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	private Organization organization;

	public MpanCores(Organization organization) {
		this.organization = organization;
	}

	public Organization getOrganization() {
		return organization;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return organization.getUri().resolve(getUriId());
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		return;
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();
		Element mpanCoresElement = (Element) toXML(doc);
		source.appendChild(mpanCoresElement);
		mpanCoresElement.appendChild(organization.toXML(doc));
		if (!inv.isValid()) {
			throw UserException.newInvalidParameter();
		}
		MpanCoreTerm pattern = null;
		if (inv.hasParameter("search-pattern")) {
			pattern = inv.getValidatable(MpanCoreTerm.class, "search-pattern");
		} else {
				pattern = new MpanCoreTerm("");
		}
		for (Object[] array : (List<Object[]>) Hiber
				.session()
				.createQuery(
						"select distinct mpanCore,mpanCore.dso.code.string, mpanCore.uniquePart.string, mpanCore.checkDigit.character from MpanCore mpanCore join mpanCore.supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and lower(mpanCore.dso.code.string || mpanCore.uniquePart.string || mpanCore.checkDigit.character) like lower(:term) order by mpanCore.dso.code.string, mpanCore.uniquePart.string, mpanCore.checkDigit.character")
				.setEntity("organization", organization).setString("term",
						"%" + pattern.toString() + "%").setMaxResults(50)
				.list()) {
			mpanCoresElement.appendChild(((MpanCore) array[0]).getXML(
					new XmlTree("supply").put("dso"), doc));
		}
		inv.sendOk(doc);
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public User getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		User user = (User) Hiber.session().createQuery(
				"from User user where user.id = :userId").setLong("userId",
				Long.parseLong(uriId.getString())).uniqueResult();
		if (user == null) {
			throw UserException.newNotFound();
		}
		return user;
	}

	public User findUser(String userName) throws ProgrammerException,
			UserException {
		User user = (User) Hiber.session().createQuery(
				"from User user where user.name = :userName").setString(
				"userName", userName).uniqueResult();
		if (user == null) {
			throw UserException.newNotFound();
		}
		return user;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public UriPathElement setUriId(UriPathElement uriId)
			throws ProgrammerException {
		// TODO Auto-generated method stub
		return null;
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = doc.createElement("mpan-cores");
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}