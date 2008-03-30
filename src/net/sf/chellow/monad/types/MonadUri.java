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

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;

public class MonadUri extends MonadString {
	public MonadUri() {
		setTypeName("URI");
	}

	public MonadUri(String uri) throws UserException, ProgrammerException {
		this(null, uri);
	}

	public MonadUri(String label, String uri) throws UserException,
			ProgrammerException {
		this();
		setLabel(label);
		update(uri);
	}

	public void update(String uri) throws UserException, ProgrammerException {
		try {
			super.update(new URI(uri).toString());
		} catch (URISyntaxException e) {
			throw UserException.newInvalidParameter("Invalid URL: "
					+ e.getMessage());
		}
	}

	public URI toUri() throws ProgrammerException {
		try {
			return new URI(toString());
		} catch (URISyntaxException e) {
			throw new ProgrammerException(e);
		}
	}

	public MonadUri resolve(MonadUri uri) throws ProgrammerException,
			UserException {
		return new MonadUri(toUri().resolve(uri.toUri()).toString());
	}

	public MonadUri resolve(String uri) throws ProgrammerException,
			UserException {
		return resolve(new MonadUri(uri));
	}

	public MonadUri resolve(Long uri) throws ProgrammerException, UserException {
		return resolve(new MonadUri(uri.toString()));
	}

	public MonadUri append(String string) throws ProgrammerException,
			UserException {
		return new MonadUri(getString() + string);
	}
}