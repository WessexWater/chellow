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

package net.sf.chellow.monad.types;

import java.net.URI;
import java.net.URISyntaxException;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

public class UriPathElement extends MonadUri {
	public UriPathElement() {
		setTypeName("UriPathElement");
	}
	
	public UriPathElement(String uri) throws InternalException, UserException {
		this();
		update(uri);
	}
	
	public UriPathElement(Long uri) throws HttpException, InternalException {
		this(uri.toString());
	}
	
	public void update(String uriString) throws InternalException, UserException {
		super.update(uriString);
		URI uri;
		try {
			uri = toUri();
		} catch (InternalException e) {
			throw new UserException(e.getMessage());
		}
		if (uri.isAbsolute()) {
			throw new UserException(
					"The URI path element must be a relative URI.");
		}
		if (uri.getPath().split("/").length > 1) {
			throw new UserException(
					"The URI path element can only consist of a single element.");
		}
	}
	
	public URI toUri() throws InternalException {
		try {
			return new URI(toString());
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		}
	}
	
	public UriPathElement resolve(UriPathElement uri) throws InternalException, HttpException {
			return new UriPathElement(toUri().resolve(uri.toUri()).toString());
	}
}