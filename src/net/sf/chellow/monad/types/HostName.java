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


/*
public class HostName extends VFBO {
	String hostName;

	public HostName(String hostName) throws InvalidArgumentException {
		checkNull(this.hostName = hostName, "hostName");
		for (int i = 0; i < hostName.length(); i += 1) {
			char c = hostName.charAt(i);
			if (Character.UnicodeBlock.of(c) != Character.UnicodeBlock.BASIC_LATIN) {
				throw new InvalidArgumentException("character_outside_range",
						"block", "basic_latin");
			}
			if (!(Character.isDigit(c) || Character.isLetter(c) || c == '.')) {
				throw new InvalidArgumentException("character_must_be_one_of",
						"allowed_characters", "<digit>, <letter>, '.'");
			}
		}
		if (hostName.indexOf("..") != -1) {
			throw new InvalidArgumentException("two_dots_together");
		}
	}
	
	public Node toXML(Document doc) throws ProgrammerException {
		Element element = doc.createElement("HostName");
		element.setAttribute("name", toString());
		return element;
	}

	public String toString() {
		return hostName;
	}
}*/
