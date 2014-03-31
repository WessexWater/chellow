/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2014 Wessex Water Services Limited
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

import java.math.BigDecimal;
import java.net.URI;
import java.util.Date;

import net.sf.chellow.hhimport.HhDatumRaw;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhDatum extends PersistentEntity {
	public static final char ACTUAL = 'A';

	public static final char ESTIMATE = 'E';

	public static final char PADDING = 'C';


	private Channel channel;

	private HhStartDate startDate;

	private BigDecimal value;

	private char status;

	private Date lastModified;

	public HhDatum() {
	}

	public HhDatum(Channel channel, HhDatumRaw datumRaw) throws HttpException {
		setChannel(channel);
		HhStartDate startDate = datumRaw.getStartDate();
		if (startDate == null) {
			throw new InternalException(
					"The value 'startDate' must not be null.");
		}
		setStartDate(startDate);
		update(datumRaw.getValue(), datumRaw.getStatus());
	}

	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public BigDecimal getValue() {
		return value;
	}

	void setValue(BigDecimal value) {
		this.value = value;
	}

	public char getStatus() {
		return status;
	}

	void setStatus(char status) {
		this.status = status;
	}

	public Date getLastModified() {
		return lastModified;
	}

	void setLastModified(Date lastModified) {
		this.lastModified = lastModified;
	}

	public void update(BigDecimal value, char status) throws HttpException {
		if (status != ESTIMATE && status != ACTUAL && status != PADDING) {
			throw new UserException("The status character must be E, A or C.");
		}
		if (!value.equals(this.value) || this.status != status) {
			setLastModified(new Date());
		}
		setValue(value);
		setStatus(status);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "hh-datum");

		element.appendChild(startDate.toXml(doc));
		element.setAttribute("value", value.toString());
		element.setAttribute("status", Character.toString(status));
		return element;
	}

	public String toString() {
		return "Start date " + startDate + ", Value " + value + ", Status "
				+ status;
	}

	public MonadUri getEditUri() throws HttpException {
		return channel.getHhDataInstance().getEditUri().resolve(getUriId());
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		throw new NotFoundException();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document(null));
	}

	private Document document(String message) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("channel", new XmlTree("era",
				new XmlTree("supply")))));
		if (message != null) {
			source.appendChild(new MonadMessage(message).toXml(doc));
		}
		return doc;
	}


	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

}
