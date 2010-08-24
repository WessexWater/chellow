/*******************************************************************************
 * 
 *  Copyright (c) 2010 Wessex Water Services Limited
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
package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class BillTypes extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("bill-types");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public BillTypes() {
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element typesElement = doc.createElement("bill-types");

		source.appendChild(typesElement);
		for (BillType type : (List<BillType>) Hiber
				.session()
				.createQuery(
						"from BillType type order by type.code")
				.list()) {
			typesElement.appendChild(type.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public MonadUri getUri() throws HttpException {
		return new MonadUri("/").resolve(getUriId()).append("/");
	}

	public BillType getChild(UriPathElement uriId) throws HttpException {
		try {
			return BillType.getBillType(Long.parseLong(uriId.toString()));
		} catch (NumberFormatException e) {
			throw new NotFoundException();
		}
	}

	public UriPathElement getUriId() throws InternalException {
		return URI_ID;
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
		
	}
}