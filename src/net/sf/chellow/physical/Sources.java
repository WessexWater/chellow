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

import java.net.URI;
import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Sources implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("sources");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	/*
	static public Source getSource(SourceCode code) throws HttpException,
			InternalException {
		Source source = (Source) Hiber.session().createQuery(
				"from Source source where source.code.string = :sourceCode")
				.setString("sourceCode", code.toString()).uniqueResult();
		if (source == null) {
			throw new NotFoundException();
		}
		return source;
	}
	*/

	public Sources() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUrlPath() throws InternalException, HttpException {
		return Chellow.getUrlableRoot().getEditUri().resolve(getUriId());
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = (Element) doc.getFirstChild();

		for (Source source : (List<Source>) Hiber.session().createQuery(
		"from Source source order by source.code").list()) {
			sourceElement.appendChild(source.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Source getChild(UriPathElement urlId) throws HttpException,
			InternalException {
		Source source = (Source) Hiber.session().createQuery(
				"from Source source where source.id = :sourceId").setLong(
				"sourceId", Long.parseLong(urlId.toString())).uniqueResult();
		if (source == null) {
			throw new NotFoundException();
		}
		return source;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getEditUri() throws InternalException, HttpException {
		return Chellow.getUrlableRoot().getEditUri().resolve(getEditUri());
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
