/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.data08.HhDatumRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class HhDatum extends PersistentEntity implements Urlable {
	private Channel channel;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatum() {
	}

	public HhDatum(Channel channel, HhDatumRaw datumRaw) throws HttpException,
			InternalException {
		setChannel(channel);
		setEndDate(datumRaw.getEndDate());
		setValue(datumRaw.getValue());
		setStatus(datumRaw.getStatus());
	}

	/*
	 * public HhDatum(Channel channel, HhEndDate endDate, float value, Character
	 * status) throws UserException, ProgrammerException { this.channel =
	 * channel; this.endDate = endDate; update(value, status); }
	 */
	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}

	public HhEndDate getEndDate() {
		return endDate;
	}

	void setEndDate(HhEndDate endDate) {
		this.endDate = endDate;
	}

	public float getValue() {
		return value;
	}

	void setValue(float value) {
		this.value = value;
	}

	public Character getStatus() {
		return status;
	}

	void setStatus(Character status) {
		this.status = status;
	}

	public void update(float value, Character status) throws HttpException,
			InternalException {
		this.value = value;
		this.status = new HhDatumStatus(status).getCharacter();
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = super.toXml(doc, "hh-datum");

		element.appendChild(endDate.toXml(doc));
		element.setAttribute("value", Float.toString(value));
		if (status != null) {
			element.setAttribute("status", Character.toString(status));
		}
		return element;
	}

	public String toString() {
		return "End date " + endDate + ", Value " + value + ", Status "
				+ status;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return channel.getHhDataInstance().getUri().resolve(getUriId());
	}

	public Urlable getChild(UriPathElement urlId) throws InternalException,
			HttpException {
		throw new NotFoundException();
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}
}
