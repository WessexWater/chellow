package net.sf.chellow.physical;

import net.sf.chellow.monad.ProgrammerException;
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
		} catch (UserException e) {
			throw new RuntimeException(e.getMessage());
		} catch (ProgrammerException e) {
			throw new RuntimeException(e.getMessage());
		}
	}

	public static Units getUnits(int intValue) throws UserException,
			ProgrammerException {
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
			throw UserException
					.newInvalidParameter("There isn't a Units with this int value.");
		}
	}

	public static Units getUnits(String name) throws UserException,
			ProgrammerException {
		if (name.equals("kWh")) {
			return KWH;
		} else if (name.equals("kVArh")) {
			return KVARH;
		} else if (name.equals("kW")) {
			return KW;
		} else if (name.equals("kVA")) {
			return KVA;
		} else {
			throw UserException
					.newInvalidParameter("There isn't a Units with this name.");
		}
	}

	public static String name(Units units) throws UserException,
			ProgrammerException {
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
			throw UserException
					.newInvalidParameter("There isn't a Units with this int value.");
		}
	}

	private int intValue;

	Units() {
		setTypeName("Unit");
	}

	private Units(int intValue) throws UserException, ProgrammerException {
		if (intValue < 0) {
			throw UserException
					.newInvalidParameter("The int value can't be negative.");
		}
		if (intValue > 3) {
			throw UserException
					.newInvalidParameter("The int value can't be greater than 3.");
		}
		setInt(intValue);
	}

	int getInt() {
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
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}
}