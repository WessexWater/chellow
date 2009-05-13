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

package net.sf.chellow.monad;


import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Node;


public class ParameterName implements XmlDescriber {
	private String name;
	
	public ParameterName(String name) {
			this.name = name;
	}
	
	public Node toXml(Document doc) {
		Attr attr = doc.createAttribute("name");
		
		attr.setValue(name);
		return attr;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException {
		return toXml(doc);
	}
	
	public String toString() {
		return name;
	}
}
