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

package net.sf.chellow.monad;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class VFParameter {
	private String name;

	private String value;

	public VFParameter(String name, String value) {
		if (name == null) {
			throw new IllegalArgumentException("The 'name' parameter must not"
					+ " be null.");
		}
		this.name = name;
		if (value == null) {
			throw new IllegalArgumentException("The 'value' parameter must "
					+ " not be null.");
		}
		this.value = value;
	}

	public String getName() {
		return name;
	}

	public String getValue() {
		return value;
	}
	public Element toXML(Document doc) {
		Element elem = doc.createElement("parameter");

		elem.setAttribute("name", getName());
		elem.setAttribute("value", getValue());
		return elem;
	}
}