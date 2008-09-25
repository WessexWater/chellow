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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;


@SuppressWarnings("serial")
public class UseDeltas implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("use-deltas");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		//return organization.getUri().resolve(getUrlId()).append("/");
		return null;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
	}

	public UseDelta getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		/*
		UseDelta useDelta = (UseDelta) Hiber
				.session()
				.createQuery(
						"from UseDelta delta where delta.organization = :organization and delta.id = :deltaId")
				.setEntity("organization", organization).setLong("deltaId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (useDelta == null) {
			throw new NotFoundException();
		}
		return useDelta;
		*/
		return null;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element accountsElement = doc.createElement("accounts");
		return accountsElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		return null;
	}
}