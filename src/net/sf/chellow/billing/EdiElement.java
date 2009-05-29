package net.sf.chellow.billing;

import java.math.BigDecimal;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.ReadType;

public class EdiElement {
	private List<String> components = new ArrayList<String>();

	private String segment;

	private int index;
	
	private Map<Integer, Character> readTypeMap;

	public EdiElement(String segment, int index, String element, Map<Integer, Character> readTypeMap) {
		this.segment = segment;
		this.index = index;
		for (String component : element.split(":")) {
			components.add(component);
		}
		this.readTypeMap = readTypeMap;
	}

	public List<String> getComponents() {
		return components;
	}

	public HhEndDate getDate(int index) throws InternalException,
			HttpException {
		DateFormat dateFormat = new SimpleDateFormat("yyMMdd", Locale.UK);
		dateFormat.setCalendar(MonadDate.getCalendar());
		try {
			return new HhEndDate(dateFormat.parse(components.get(index)));
		} catch (ParseException e) {
			throw new UserException("Expected component " + index
					+ " of element " + this.index + " of segment '"
					+ segment + "' to be a date. " + e.getMessage());
		}
	}

	public Float getFloat() {
		Float result = new Float(components.get(0));
		if (components.size() > 1
				&& components.get(components.size() - 1).equals("R")) {
			result = result * -1;
		}
		return result;
	}
	
	public BigDecimal getBigDecimal() {
		BigDecimal result = new BigDecimal(components.get(0));
		if (components.size() > 1
				&& components.get(components.size() - 1).equals("R")) {
			result = result.multiply(new BigDecimal("-1"));
		}
		return result;
	}

	public ReadType getReadType(int index) throws HttpException {
		return ReadType.getReadType(readTypeMap.get(getInt(index)));
	}

	public int getInt(int index) throws HttpException {
		try {
			return Integer.parseInt(components.get(index));
		} catch (NumberFormatException e) {
			throw new UserException("Expected component " + index
					+ " of element " + this.index + " of segment '"
					+ segment + "' to be an integer. " + e.getMessage());
		}
	}

	public String getString(int index) {
		return components.get(index);
	}
}