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
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Dcses implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("dcses");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Dcses() {
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
	}
	
	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element suppliersElement = (Element) toXml(doc);
		
		source.appendChild(suppliersElement);
		for (Mop mop : (List<Mop>) Hiber.session().createQuery("from Dcs dcs").list()) {
			suppliersElement.appendChild(mop.toXml(doc));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return Mop.getMop(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element suppliersElement = doc.createElement("dcss");
		return suppliersElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}