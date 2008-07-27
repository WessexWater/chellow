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

package net.sf.chellow.monad.types;

import javax.mail.internet.AddressException;
import javax.mail.internet.InternetAddress;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Node;

public class EmailAddress extends InternetAddress implements XmlDescriber,
		MonadValidatable {
	private static final long serialVersionUID = 1L;
	private String label = null;

	public EmailAddress() {
	}

	public EmailAddress(String emailAddress)
			throws HttpException {
		this(null, emailAddress);
	}

	public EmailAddress(String label, String emailAddress)
			throws HttpException {
		if (emailAddress == null) {
			throw new InternalException(
					"Email address argument must not be null.");
		}
		super.setAddress(emailAddress);
		try {
			validate();
		} catch (AddressException e) {
			throw new UserException(
					"The email address '" + label
							+ "' is not correctly formed. " + e.getMessage() + ".");
		}
		this.label = label;
	}

	public void setAddress(String address) {
		super.setAddress(address);
		try {
			validate();
		} catch (AddressException e) {
			throw new IllegalArgumentException("email_address_malformed");
		}
	}

	public Attr toXml(Document doc) {
		Attr attr = doc.createAttribute("email-address");

		attr.setNodeValue(getAddress());
		return attr;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException {
		return toXml(doc);
	}

	public String getLabel() {
		return label;
	}
}
