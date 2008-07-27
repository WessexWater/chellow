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

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MonadCharacter extends MonadObject {
	public static final String TYPE_NAME = "Character";

	public static Attr toXml(Document doc, String name, Character value) {
		Attr attr = doc.createAttribute(name);
		attr.setValue(Character.toString(value));
		return attr;
	}

	private Character character;

	private boolean digitOnly;

	public MonadCharacter() {
	}

	public MonadCharacter(String label, Character character) {
		setLabel(label);
		setCharacter(character);
	}

	protected void setDigitOnly(boolean digitOnly) {
		this.digitOnly = digitOnly;
	}

	public String toString() {
		return character.toString();
	}

	public Character getCharacter() {
		return character;
	}

	public void update(Character character) throws HttpException,
			InternalException {

		if (digitOnly && !Character.isDigit(character.charValue())) {
			throw new UserException
					("This character must be a digit.");
		}
		setCharacter(character);
	}

	protected void setCharacter(Character character) {
		this.character = character;
	}

	public Attr toXml(Document doc) {
		Attr attr = doc.createAttribute((getLabel() == null) ? "character"
				: getLabel());

		attr.setValue(toString());
		return attr;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (super.equals(obj)) {
			isEqual = ((MonadCharacter) obj).getCharacter().equals(character);
		}
		return isEqual;
	}

	public int hashCode() {
		return character.hashCode();
	}
}