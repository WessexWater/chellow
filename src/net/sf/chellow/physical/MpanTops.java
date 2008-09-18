/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.billing.Dso;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

@SuppressWarnings("serial")
public class MpanTops implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("mpan-tops");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Dso dso;

	public MpanTops(Dso dso) {
		this.dso = dso;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return dso.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element mpanTopsElement = (Element) toXml(doc);
		source.appendChild(mpanTopsElement);
		mpanTopsElement.appendChild(dso.toXml(doc));
		for (MpanTop mpanTop : (List<MpanTop>) Hiber
				.session()
				.createQuery(
						"from MpanTop mpanTop where mpanTop.llfc.dso = :dso order by mpanTop.llfc.code, mpanTop.pc.code")
				.setEntity("dso", dso).list()) {
			mpanTopsElement.appendChild(mpanTop.toXml(doc, new XmlTree("llfc",
					new XmlTree("dso")).put("pc").put("mtc").put("ssc")));
		}
		inv.sendOk(doc);
	}

	public MpanTop getChild(UriPathElement uriId) throws HttpException {
		MpanTop mpanTop = (MpanTop) Hiber
				.session()
				.createQuery(
						"from MpanTop mpanTop where mpanTop.llfc.dso = :dso and mpanTop.id = :mpanTopId")
				.setEntity("dso", dso).setLong("mpanTopId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (mpanTop == null) {
			throw new NotFoundException();
		}
		return mpanTop;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		throw new MethodNotAllowedException();
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element mpanTopsElement = doc.createElement("mpan-tops");
		return mpanTopsElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}