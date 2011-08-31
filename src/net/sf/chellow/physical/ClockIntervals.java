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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class ClockIntervals implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("clock-intervals");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Tpr tpr;

	public ClockIntervals(Tpr tpr) {
		this.tpr = tpr;
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element intervalsElement = doc.createElement("clock-intervals");
		source.appendChild(intervalsElement);
		intervalsElement.appendChild(tpr.toXml(doc));
		for (ClockInterval interval : (List<ClockInterval>) Hiber
				.session()
				.createQuery(
						"from ClockInterval interval where interval.tpr = :tpr order by interval.id")
				.setEntity("tpr", tpr).list()) {
			intervalsElement.appendChild(interval.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public MonadUri getEditUri() throws InternalException, HttpException {
		return new MonadUri("/").resolve(getUriId()).append("/");
	}

	public ClockInterval getChild(UriPathElement uriId) throws HttpException {
		return ClockInterval.getClockInterval(Long.parseLong(uriId.toString()));
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public UriPathElement getUriId() throws InternalException {
		return URI_ID;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
