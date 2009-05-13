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
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.MonadMessage;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Node;

public class MonadFloat extends MonadObject {
	private Float floatValue;

	private Float min = null;

	private Float max = null;

	public static Attr toXml(Document doc, String name, float value) {
		Attr attr = doc.createAttribute(name);
		attr.setValue(Float.toString(value));
		return attr;
	}

	protected MonadFloat() {
	}

	public MonadFloat(String label, String floatString) throws HttpException,
			InternalException {
		this(null, label, floatString, null, null);
	}

	protected MonadFloat(String typeName, String floatString, float min,
			float max) throws HttpException, InternalException {
		this(typeName, null, floatString, new Float(min), new Float(max));
	}

	protected MonadFloat(String typeName, String name, String floatString,
			Float min, Float max) throws HttpException, InternalException {
		super(typeName, name);
		this.min = min;
		this.max = max;

		try {
			setFloat(new Float(floatString));
		} catch (NumberFormatException e) {
			throw new UserException("malformed_float" + e.getMessage());
		}
	}

	public MonadFloat(float floatValue) {
		setFloat(new Float(floatValue));
	}

	public MonadFloat(String floatString) throws HttpException,
			InternalException {
		this(null, floatString);
	}

	public Float getFloat() {
		return floatValue;
	}

	void setFloat(Float floatValue) {
		this.floatValue = floatValue;
	}

	public void update(Float floatValue) throws HttpException,
			InternalException {

		if ((min != null) && (floatValue.floatValue() < min.intValue())) {
			throw new UserException(MonadMessage.NUMBER_TOO_SMALL);
		}
		if ((max != null) && (floatValue.floatValue() > max.intValue())) {
			throw new UserException(MonadMessage.NUMBER_TOO_BIG);
		}
		setFloat(floatValue);
	}

	public Node toXml(Document doc) {
		Node node = doc.createAttribute(getLabel());

		node.setNodeValue(floatValue.toString());
		return node;
	}

	public String toString() {
		return floatValue.toString();
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof MonadFloat) {
			isEqual = ((MonadFloat) obj).getFloat().equals(getFloat());
		}
		return isEqual;
	}
}
