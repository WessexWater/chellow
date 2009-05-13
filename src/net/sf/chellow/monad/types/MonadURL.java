/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
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

package net.sf.chellow.monad.types;

import java.net.MalformedURLException;
import java.net.URL;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

public class MonadURL extends MonadString {
	public MonadURL() {
	}

	public MonadURL(String url) throws HttpException {
		update(url);
	}

	public void update(String url) throws HttpException {
		try {
			super.update(new URL(url).toString());
		} catch (MalformedURLException e) {
			throw new UserException("Invalid URL: " + e.getMessage());
		}
	}
	
	public Attr toXml(Document doc) {
		return super.toXml(doc, "url");
	}
}
