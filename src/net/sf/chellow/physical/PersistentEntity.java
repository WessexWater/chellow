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

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class PersistentEntity extends MonadObject implements Urlable {
	private Long id;
	
	public PersistentEntity() {
	}

	public Long getId() {
		return id;
	}

	protected void setId(Long id) {
		this.id = id;
	}
	
	public UriPathElement getUriId() throws HttpException {
			return new UriPathElement(Long.toString(id));
	}

	public Element toXml(Document doc, String elementName) throws HttpException {
		Element element = (Element) super.toXml(doc, elementName);

		element.setAttribute("id", id.toString());
		return element;
	}
	
	public boolean equals(Object obj) {
		boolean isEqual = false;
		
		if (obj instanceof PersistentEntity) {
			isEqual = ((PersistentEntity) obj).getId().equals(getId());
		}
		return isEqual;
	}
	
	public int hashCode() {
		return id == null ? super.hashCode() : id.intValue();
	}
}