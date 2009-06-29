/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.billing.Dso;
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
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Llfcs implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("llfcs");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Dso dso;

	public Llfcs(Dso dso) {
		this.dso = dso;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return dso.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		throw new MethodNotAllowedException();
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element llfsElement = (Element) toXml(doc);
		source.appendChild(llfsElement);
		llfsElement.appendChild(dso.toXml(doc));
		for (Llfc llfc : (List<Llfc>) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso order by llfc.code")
				.setEntity("dso", dso).list()) {
			llfsElement.appendChild(llfc.toXml(doc, new XmlTree("voltageLevel")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		inv.sendOk(doc);
	}

	public Llfc getChild(UriPathElement uriId) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.id = :llfcId")
				.setEntity("dso", dso).setLong("llfcId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (llfc == null) {
			throw new NotFoundException();
		}
		return llfc;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element llfsElement = doc.createElement("llfcs");
		return llfsElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
