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

import java.net.URI;
import java.net.URISyntaxException;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

public class MonadUri extends MonadString {
	public MonadUri() {
		setTypeName("URI");
	}

	public MonadUri(String uri) throws InternalException, UserException {
		this(null, uri);
	}

	public MonadUri(String label, String uri) throws InternalException, UserException {
		this();
		setLabel(label);
		update(uri);
	}

	public void update(String uri) throws UserException, InternalException {
		try {
			super.update(new URI(uri).toString());
		} catch (URISyntaxException e) {
			throw new UserException("Invalid URL: "
					+ e.getMessage());
		}
	}

	public URI toUri() throws InternalException {
		try {
			return new URI(toString());
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		}
	}

	public MonadUri resolve(MonadUri uri) throws InternalException, UserException {
		return new MonadUri(toUri().resolve(uri.toUri()).toString());
	}

	public MonadUri resolve(String uri) throws InternalException, UserException {
		return resolve(new MonadUri(uri));
	}

	public MonadUri resolve(Long uri) throws InternalException, HttpException {
		return resolve(new MonadUri(uri.toString()));
	}

	public MonadUri append(String string) throws InternalException, UserException {
		return new MonadUri(getString() + string);
	}
}