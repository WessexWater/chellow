/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadCharacter;
import net.sf.chellow.monad.types.MonadFloat;
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

	public HhDatum(Channel channel, HhDatumRaw datumRaw) throws UserException, ProgrammerException {
		setChannel(channel);
		setEndDate(datumRaw.getEndDate());
		setValue(datumRaw.getValue());
		setStatus(datumRaw.getStatus());
	}
/*	
	public HhDatum(Channel channel, HhEndDate endDate, float value,
			Character status) throws UserException, ProgrammerException {
		this.channel = channel;
		this.endDate = endDate;
		update(value, status);
	}
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

	public void update(float value, Character status) throws UserException,
			ProgrammerException {
		this.value = value;
			this.status = new HhDatumStatus(status).getCharacter();
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		setTypeName("hh-datum");
		Element element = (Element) super.toXML(doc);

		element.appendChild(endDate.toXML(doc));
		element.setAttributeNode(MonadFloat.toXml(doc, "value", value));
		if (status != null) {
			element.setAttributeNode(MonadCharacter
					.toXml(doc, "status", status));
		}
		return element;
	}

	public String toString() {
		return "End date " + endDate + ", Value " + value + ", Status "
				+ status;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return channel.getHhDataInstance().getUri().resolve(getUriId());
	}

	public Urlable getChild(UriPathElement urlId) throws ProgrammerException,
			UserException {
		throw UserException.newNotFound();
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}
}
