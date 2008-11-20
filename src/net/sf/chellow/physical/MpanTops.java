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
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class MpanTops extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("mpan-tops");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public MpanTops() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element mpanTopsElement = toXml(doc);
		source.appendChild(mpanTopsElement);
		if (inv.hasParameter("dso-id") && inv.hasParameter("gsp-group-id")) {
			Long dsoId = inv.getLong("dso-id");
			Dso dso = Dso.getDso(dsoId);
			Long gspGroupId = inv.getLong("gsp-group-id");
			GspGroup gspGroup = GspGroup.getGspGroup(gspGroupId);
			for (MpanTop mpanTop : (List<MpanTop>) Hiber
					.session()
					.createQuery(
							"from MpanTop mpanTop where mpanTop.llfc.dso = :dso and mpanTop.gspGroup = :gspGroup order by mpanTop.llfc.code, mpanTop.pc.code")
					.setEntity("dso", dso).setEntity("gspGroup", gspGroup).list()) {
				mpanTopsElement.appendChild(mpanTop.toXml(doc, new XmlTree(
						"llfc", new XmlTree("dso")).put("pc").put("mtc").put(
						"ssc").put("gspGroup")));
			}
		} else {
			for (GspGroup group : (List<GspGroup>) Hiber.session().createQuery(
					"from GspGroup group order by group.code").list()) {
				Element groupElement = group.toXml(doc);
				source.appendChild(groupElement);
				for (Dso dso : (List<Dso>) Hiber
						.session()
						.createQuery(
								"select distinct top.llfc.dso from MpanTop top where top.gspGroup = :gspGroup order by top.llfc.dso.code")
						.setEntity("gspGroup", group).list()) {
					groupElement.appendChild(dso.toXml(doc));
				}
			}
		}
		inv.sendOk(doc);
	}

	public MpanTop getChild(UriPathElement uriId) throws HttpException {
		return MpanTop.getMpanTop(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		throw new MethodNotAllowedException();
	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		Element mpanTopsElement = doc.createElement("mpan-tops");
		return mpanTopsElement;
	}
}