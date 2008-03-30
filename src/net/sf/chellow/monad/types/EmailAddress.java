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

package net.sf.chellow.monad.types;

import javax.mail.internet.AddressException;
import javax.mail.internet.InternetAddress;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.VFParameter;
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
			throws ProgrammerException, UserException {
		this(null, emailAddress);
	}

	public EmailAddress(String label, String emailAddress)
			throws ProgrammerException, UserException {
		if (emailAddress == null) {
			throw new ProgrammerException(
					"Email address argument must not be null.");
		}
		super.setAddress(emailAddress);
		try {
			validate();
		} catch (AddressException e) {
			throw UserException.newInvalidParameter(
					new VFMessage("The email address '" + label
							+ "' is not correctly formed. " + e.getMessage() + ".",
							new VFParameter[] {
									new VFParameter("code",
											"email_address_malformed"),
									new VFParameter("reason", e.getMessage()) }));
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

	public Node toXML(Document doc) {
		Attr attr = doc.createAttribute("email-address");

		attr.setNodeValue(getAddress());
		return attr;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException {
		return toXML(doc);
	}

	public String getLabel() {
		return label;
	}
}
