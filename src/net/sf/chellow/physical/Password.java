/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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



import java.io.UnsupportedEncodingException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.types.MonadString;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

import com.Ostermiller.util.Base64;

public class Password extends MonadString {
	public Password() {
		setMinimumLength(6);
		setMaximumLength(250);
	}
	
	public Password(String name) throws HttpException {
		this(null, name);
	}

	public Password(String label, String name) throws HttpException {
		this();
		setLabel(label);
		update(name);
	}
	
	public Attr toXml(Document doc) {
		setTypeName("password");
		return super.toXml(doc);
	}
	
	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Password) {
			isEqual = getString().equals(((Password) obj).getString());
		}
		return isEqual;
	}
	
	public void update(String password) throws HttpException {
		try {
			MessageDigest digest = MessageDigest.getInstance("MD5");
		digest.update(password.getBytes("US-ASCII"));
		super.update(Base64.encode(new String(digest.digest(), "ISO-8859-1")));
		} catch (NoSuchAlgorithmException e) {
			throw new InternalException(e);
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		}
	}
}