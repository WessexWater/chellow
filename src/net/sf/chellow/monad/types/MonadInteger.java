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

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.VFParameter;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MonadInteger extends MonadObject {
	private static final long serialVersionUID = 1L;

	public static Attr toXml(Document doc, String name, int value) {
		Attr attr = doc.createAttribute(name);
		attr.setValue(Integer.toString(value));
		return attr;
	}

	private Integer integer;

	private Integer min = null;

	private Integer max = null;

	public MonadInteger() {
	}

	public MonadInteger(int intValue) throws UserException, ProgrammerException {
		update(intValue);
	}

	public MonadInteger(String label, String integer) throws UserException,
			ProgrammerException {
		super();
		setLabel(label);
		update(integer);
	}

	public MonadInteger(String integer) throws UserException,
			ProgrammerException {
		this(null, integer);
	}

	public Integer getInteger() {
		return integer;
	}

	public void update(String integer) throws UserException,
			ProgrammerException {
		try {
			update(new Integer(integer));
		} catch (NumberFormatException e) {
			throw UserException.newInvalidParameter(new VFMessage(
					"The integer '" + getLabel() + "' is malformed. "
							+ e.getMessage() + ".", new VFParameter[] {
							new VFParameter("code", "malformed_integer"),
							new VFParameter("note", e.getMessage()) }));
		}
	}

	public void update(Integer integer) throws UserException,
			ProgrammerException {
		if ((min != null) && (integer.intValue() < min.intValue())) {
			throw UserException.newInvalidParameter(new VFMessage(
					VFMessage.NUMBER_TOO_SMALL, new VFParameter[] {
							new VFParameter("number", integer.toString()),
							new VFParameter("min", min.toString()) }));
		}
		if ((max != null) && (integer.intValue() > max.intValue())) {
			throw UserException.newInvalidParameter(new VFMessage(
					VFMessage.NUMBER_TOO_BIG, new VFParameter[] {
							new VFParameter("number", integer.toString()),
							new VFParameter("max", max.toString()) }));
		}
		setInteger(integer);
	}

	public void setInteger(Integer integer) {
		this.integer = integer;
	}

	public int getMimimum() {
		return min;
	}

	protected void setMinimum(int minimum) {
		this.min = minimum;
	}

	public int getMaximum() {
		return max;
	}

	protected void setMaximum(int maximum) {
		this.max = maximum;
	}

	public Attr toXML(Document doc) {
		return toXml(doc, getLabel() == null ? getTypeName() : getLabel(),
				integer);
	}

	public String toString() {
		return integer.toString();
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (super.equals(obj)) {
			isEqual = ((MonadInteger) obj).getInteger().equals(getInteger());
		}
		return isEqual;
	}
	
	public int hashCode() {
		return integer.hashCode();
	}
}