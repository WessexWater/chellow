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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Meter extends PersistentEntity {
	static public Meter getMeter(String meterSerialNumber) throws HttpException {
		Meter meter = (Meter) Hiber.session().createQuery("from Meter meter where meter.serialNumber = :meterSerialNumber").setString("meterSerialNumber", meterSerialNumber).uniqueResult();
		if (meter == null) {
			throw new NotFoundException("The meter cannot be found.");
		}
		return meter;
	}
	
	private Supply supply;

	private String serialNumber;

	Meter() {
	}

	public Meter(Supply supply, String serialNumber) {
		setSupply(supply);
		setSerialNumber(serialNumber);
	}

	public Supply getSupply() {
		return supply;
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public String getSerialNumber() {
		return serialNumber;
	}

	void setSerialNumber(String serialNumber) {
		this.serialNumber = serialNumber;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "meter");
		element.setAttribute("serial-number", serialNumber);
		return element;
	}
}
