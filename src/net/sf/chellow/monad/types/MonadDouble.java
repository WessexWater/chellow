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
import net.sf.chellow.monad.MonadMessage;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MonadDouble extends MonadObject {
	public static Attr toXml(Document doc, String name, double value) {
		Attr attr = doc.createAttribute(name);
		attr.setValue(Double.toString(value));
		return attr;
	}

	private Double doubleValue;

	private Double min = null;

	private Double max = null;

	protected MonadDouble() {
	}

	public MonadDouble(String label, String doubleString) throws HttpException,
			InternalException {
		this(null, label, doubleString, null, null);
	}

	protected MonadDouble(String typeName, String doubleString, double min,
			double max) throws HttpException, InternalException {
		this(typeName, null, doubleString, new Double(min), new Double(max));
	}

	protected MonadDouble(String typeName, String name, String doubleString,
			Double min, Double max) throws HttpException, InternalException {
		super(typeName, name);
		this.min = min;
		this.max = max;

		try {
			setDouble(new Double(doubleString));
		} catch (NumberFormatException e) {
			throw new UserException
					("malformed_double " + e.getMessage());
		}
	}

	public MonadDouble(double doubleValue) {
		setDouble(new Double(doubleValue));
	}

	public MonadDouble(String doubleString) throws HttpException,
			InternalException {
		this(null, doubleString);
	}

	public Double getDouble() {
		return doubleValue;
	}

	void setDouble(Double doubleValue) {
		this.doubleValue = doubleValue;
	}

	public void update(Double doubleValue) throws HttpException,
			InternalException {

		if ((min != null) && (doubleValue.doubleValue() < min.intValue())) {
			throw new UserException(
					MonadMessage.NUMBER_TOO_SMALL);
		}
		if ((max != null) && (doubleValue.doubleValue() > max.intValue())) {
			throw new UserException(
					MonadMessage.NUMBER_TOO_BIG);
		}
		setDouble(doubleValue);
	}

	public Attr toXml(Document doc) {
		return toXml(doc, getLabel(), doubleValue);
	}

	public String toString() {
		return doubleValue.toString();
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof MonadDouble) {
			isEqual = ((MonadDouble) obj).getDouble().equals(getDouble());
		}
		return isEqual;
	}
}