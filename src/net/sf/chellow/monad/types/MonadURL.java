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

import java.net.MalformedURLException;
import java.net.URL;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

public class MonadURL extends MonadString {
	public MonadURL() {
		setTypeName("url");
	}

	public MonadURL(String url) throws HttpException {
		this();
		update(url);
	}

	public void update(String url) throws HttpException {
		try {
			super.update(new URL(url).toString());
		} catch (MalformedURLException e) {
			throw new UserException("Invalid URL: " + e.getMessage());
		}
	}
}