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

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MonadBoolean extends MonadObject {
	static public final MonadBoolean TRUE = new MonadBoolean(true);
	static public final MonadBoolean FALSE = new MonadBoolean(false);
	
	public static Attr toXml(Document doc, String name, boolean value) {
		Attr attr = doc.createAttribute(name);
		attr.setNodeValue(Boolean.toString(value));
		return attr;
	}
	
	private Boolean booleanValue;

	public MonadBoolean(String label, boolean booleanValue) {
		this(null, label, new Boolean(booleanValue));
	}

	public MonadBoolean(boolean booleanValue)
			 {
		this(null, null, new Boolean(booleanValue));
	}

	public MonadBoolean(String booleanValue)  {
		this(null, null, Boolean.parseBoolean(booleanValue));
	}

	protected MonadBoolean(String typeName, String label, boolean booleanValue) {
		this(typeName, label, new Boolean(booleanValue));
	}

	protected MonadBoolean(String typeName, String label, Boolean booleanValue) {
		super(typeName, label);
		setBoolean(booleanValue);
	}

	public MonadBoolean() {
		super("Boolean", null);
	}

	public Boolean getBoolean() {
		return booleanValue;
	}

	public void setBoolean(Boolean booleanValue) {
		this.booleanValue = booleanValue;
	}

	public Attr toXml(Document doc) {
		return toXml(doc, (getLabel() == null) ? getTypeName()
				: getLabel(), booleanValue);
	}

	public void update(String booleanValue) {
		update(Boolean.parseBoolean(booleanValue));
	}

	public void update(boolean booleanValue) {
		setBoolean(new Boolean(booleanValue));
	}
	
	public String toString() {
		return booleanValue.toString();
	}
	
	public boolean equals(Object obj) {
		boolean isEqual = false;
		
		if (obj instanceof MonadBoolean) {
			isEqual = ((MonadBoolean) obj).getBoolean().equals(getBoolean());
		}
		return isEqual;
	}
}