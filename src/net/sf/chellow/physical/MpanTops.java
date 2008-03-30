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

@SuppressWarnings("serial")
public class MpanTops implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("mpan-tops");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
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

	public MonadUri getUri() throws ProgrammerException, UserException {
		return dso.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		throw UserException.newMethodNotAllowed();
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element mpanTopsElement = (Element) toXML(doc);
		source.appendChild(mpanTopsElement);
		mpanTopsElement.appendChild(dso.toXML(doc));
		for (MpanTop mpanTop : (List<MpanTop>) Hiber
				.session()
				.createQuery(
						"from MpanTop mpanTop where mpanTop.lineLossFactor.dso = :dso order by mpanTop.lineLossFactor.code, mpanTop.profileClass.code")
				.setEntity("dso", dso).list()) {
			mpanTopsElement.appendChild(mpanTop.getXML(new XmlTree(
					"lineLossFactor", new XmlTree("dso")).put("profileClass")
					.put("meterTimeswitch"), doc));
		}
		inv.sendOk(doc);
	}

	public MpanTop getChild(UriPathElement uriId) throws UserException,
			ProgrammerException {
		MpanTop mpanTop = (MpanTop) Hiber
				.session()
				.createQuery(
						"from MpanTop mpanTop where mpanTop.lineLossFactor.dso = :dso and mpanTop.id = :mpanTopId")
				.setEntity("dso", dso).setLong("mpanTopId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (mpanTop == null) {
			throw UserException.newNotFound();
		}
		return mpanTop;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		throw UserException.newMethodNotAllowed();
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element mpanTopsElement = doc.createElement("mpan-tops");
		return mpanTopsElement;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}