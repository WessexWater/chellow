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

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Organization;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Suppliers implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("suppliers");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Organization organization;

	public Suppliers(Organization organization) {
		this.organization = organization;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return organization.getUri().resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public void httpPost(Invocation inv) throws HttpException {
		String name = inv.getString("name");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			Supplier supplier = organization.insertSupplier(name);
			Hiber.commit();
			inv.sendCreated(document(), supplier.getUri());
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element suppliersElement = (Element) toXml(doc);

		source.appendChild(suppliersElement);
		suppliersElement.appendChild(organization.toXml(doc));
		for (Supplier supplier : (List<Supplier>) Hiber
				.session()
				.createQuery(
						"from Supplier supplier where supplier.organization = :organization")
				.setEntity("organization", organization).list()) {
			suppliersElement.appendChild(supplier.toXml(doc));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return organization.getSupplier(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element suppliersElement = doc.createElement("suppliers");
		return suppliersElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}