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

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.MonadMessage;
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

	public MonadInteger(int intValue) throws InternalException, UserException {
		update(intValue);
	}

	public MonadInteger(String label, String integer) throws InternalException, UserException {
		super();
		setLabel(label);
		update(integer);
	}

	public MonadInteger(String integer) throws InternalException, UserException {
		this(null, integer);
	}

	public Integer getInteger() {
		return integer;
	}

	public void update(String integer) throws InternalException, UserException {
		try {
			update(new Integer(integer));
		} catch (NumberFormatException e) {
			throw new UserException(
					"The integer '" + getLabel() + "' is malformed. "
							+ e.getMessage() + ".");
		}
	}

	public void update(Integer integer) throws InternalException, UserException {
		if ((min != null) && (integer.intValue() < min.intValue())) {
			throw new UserException(MonadMessage.NUMBER_TOO_SMALL);
		}
		if ((max != null) && (integer.intValue() > max.intValue())) {
			throw new UserException(
					MonadMessage.NUMBER_TOO_BIG);
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

	public Attr toXml(Document doc) {
		return toXml(doc, getLabel() == null ? "integer" : getLabel(),
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
