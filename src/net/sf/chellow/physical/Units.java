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
package net.sf.chellow.physical;

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadObject;

public class Units extends MonadObject {
	public static final Units KWH;

	public static final Units KVARH;

	public static final Units KW;

	public static final Units KVA;

	static {
		try {
			KWH = new Units(0);
			KVARH = new Units(1);
			KW = new Units(2);
			KVA = new Units(3);
		} catch (InternalException e) {
			throw new RuntimeException(e.getMessage());
		} catch (UserException e) {
			throw new RuntimeException(e.getMessage());
		}
	}

	public static Units getUnits(int intValue) throws InternalException, UserException {
		switch (intValue) {
		case 0:
			return KWH;
		case 1:
			return KVARH;
		case 2:
			return KW;
		case 3:
			return KVA;
		default:
			throw new UserException("There isn't a Units with this int value.");
		}
	}

	public static Units getUnits(String name) throws InternalException, UserException {
		if (name.equals("kWh")) {
			return KWH;
		} else if (name.equals("kVArh")) {
			return KVARH;
		} else if (name.equals("kW")) {
			return KW;
		} else if (name.equals("kVA")) {
			return KVA;
		} else {
			throw new UserException("There isn't a Units with the name " + name);
		}
	}

	public static String name(Units units) throws InternalException, UserException {
		switch (units.getInt()) {
		case 0:
			return "kWh";
		case 1:
			return "kVArh";
		case 2:
			return "kW";
		case 3:
			return "kVA";
		default:
			throw new UserException("There isn't a Units with this int value.");
		}
	}

	private int intValue;

	Units() {
	}

	private Units(int intValue) throws InternalException, UserException {
		if (intValue < 0) {
			throw new UserException("The int value can't be negative.");
		}
		if (intValue > 3) {
			throw new UserException("The int value can't be greater than 3.");
		}
		setInt(intValue);
	}

	public int getInt() {
		return intValue;
	}

	void setInt(int intValue) {
		this.intValue = intValue;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Units) {
			Units toCompare = (Units) obj;
			if (toCompare.getInt() == getInt()) {
				isEqual = true;
			}
		}
		return isEqual;
	}

	public String toString() {
		try {
			return name(this);
		} catch (InternalException e) {
			throw new RuntimeException(e);
		} catch (UserException e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		return super.toXml(doc, "Unit");
	}
}
