package net.sf.chellow.physical;

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadObject;

public class ReadType extends MonadObject {
	public static final ReadType NORMAL;

	public static final ReadType MANUAL_ESTIMATE;

	public static final ReadType COMPUTER_ESTIMATE;

	public static final ReadType REMOVED;

	public static final ReadType CUSTOMER;

	public static final ReadType COMPUTER;

	public static final ReadType EXCHANGE;

	static {
		try {
			NORMAL = new ReadType(0);
			MANUAL_ESTIMATE = new ReadType(1);
			COMPUTER_ESTIMATE = new ReadType(2);
			REMOVED = new ReadType(3);
			CUSTOMER = new ReadType(4);
			COMPUTER = new ReadType(5);
			EXCHANGE = new ReadType(6);
		} catch (HttpException e) {
			throw new RuntimeException(e.getMessage());
		}
	}

	public static ReadType getType(int intValue) throws HttpException {
		switch (intValue) {
		case 0:
			return NORMAL;
		case 1:
			return MANUAL_ESTIMATE;
		case 2:
			return COMPUTER_ESTIMATE;
		case 3:
			return REMOVED;
		case 4:
			return CUSTOMER;
		case 5:
			return COMPUTER;
		case 6:
			return EXCHANGE;
		default:
			throw new UserException(
					"There isn't a read type with this int value.");
		}
	}

	public static String name(ReadType type) throws HttpException {
		switch (type.getInt()) {
		case 0:
			return "normal";
		case 1:
			return "manual-estimate";
		case 2:
			return "computer-estimate";
		case 3:
			return "removed";
		case 4:
			return "customer";
		case 5:
			return "computer";
		case 6:
			return "exchange";
		default:
			throw new UserException("There isn't a Units with this int value.");
		}
	}

	public static ReadType getType(String name) throws HttpException {
		name = name.trim().toLowerCase();
		if (name.equals("normal")) {
			return NORMAL;
		} else if (name.equals("manual-estimate")) {
			return MANUAL_ESTIMATE;
		} else if (name.equals("computer-estimate")) {
			return COMPUTER_ESTIMATE;
		} else if (name.equals("removed")) {
			return REMOVED;
		} else if (name.equals("customer")) {
			return CUSTOMER;
		} else if (name.equals("computer")) {
			return COMPUTER;
		} else if (name.equals("exchange")) {
			return EXCHANGE;
		} else {
			throw new UserException("There isn't a read type with that name.");
		}
	}

	private int intValue;

	ReadType() {
	}

	private ReadType(int intValue) throws HttpException {
		if (intValue < 0) {
			throw new UserException("The int value can't be negative.");
		}
		if (intValue > 6) {
			throw new UserException("The int value can't be greater than 3.");
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
		if (obj instanceof ReadType) {
			ReadType toCompare = (ReadType) obj;
			if (toCompare.getInt() == getInt()) {
				isEqual = true;
			}
		}
		return isEqual;
	}

	public String toString() {
		try {
			return name(this);
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		return super.toXml(doc, "Unit");
	}
}