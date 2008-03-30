/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MonadDate extends MonadObject {
	static private SimpleDateFormat sdIsoDate() {
		SimpleDateFormat sdFormat = new SimpleDateFormat("yyyy-MM-dd");
		sdFormat.setCalendar(getCalendar());
		return sdFormat;
	}

	static private SimpleDateFormat sdIsoDateTime() {
		SimpleDateFormat sdFormat = new SimpleDateFormat(
				"yyyy-MM-dd'T'HH:mm'Z'");
		sdFormat.setCalendar(getCalendar());
		return sdFormat;
	}

	static public Calendar getCalendar() {
		Calendar calendar = new GregorianCalendar(TimeZone.getTimeZone("GMT"),
				Locale.UK);
		calendar.setLenient(false);
		return calendar;
	}

	static public Date intsToDate(int year, int month, int day) {
		Calendar cal = getCalendar();

		cal.clear();
		cal.set(year, month - 1, day);
		return cal.getTime();
	}

	/*
	 * public static Element toXML(MonadDate date, Document doc) throws
	 * ProgrammerException, UserException { Element element =
	 * doc.createElement(date.getTypeName());
	 * 
	 * element.setAttribute("year", date.getYear());
	 * element.setAttribute("month", date.getMonth());
	 * element.setAttribute("day", date.getDay()); element.setAttribute("hour",
	 * date.getHour()); element.setAttribute("minute", date.getMinute()); if
	 * (date.getLabel() != null) { element.setAttribute("label",
	 * date.getLabel()); } return element; }
	 */
	public static Element toXML(Date date, String label, Document doc)
			throws ProgrammerException, UserException {
		return toXML(date, label, doc, "date");
	}

	public static Element toXML(Date date, String label, Document doc,
			String typeName) throws ProgrammerException, UserException {
		Element element = doc.createElement(typeName);
		Calendar cal = getCalendar();
		SimpleDateFormat sdYear = new SimpleDateFormat("yyyy", Locale.UK);
		sdYear.setCalendar(cal);
		SimpleDateFormat sdMonth = new SimpleDateFormat("MM", Locale.UK);
		sdMonth.setCalendar(cal);
		SimpleDateFormat sdDay = new SimpleDateFormat("dd", Locale.UK);
		sdDay.setCalendar(cal);
		SimpleDateFormat sdHour = new SimpleDateFormat("HH", Locale.UK);
		sdHour.setCalendar(cal);
		SimpleDateFormat sdMinute = new SimpleDateFormat("mm", Locale.UK);
		sdMinute.setCalendar(cal);
		cal.setTime(date);
		element.setAttribute("year", sdYear.format(date));
		element.setAttribute("month", sdMonth.format(date));
		element.setAttribute("day", sdDay.format(date));
		element.setAttribute("hour", sdHour.format(date));
		element.setAttribute("minute", sdMinute.format(date));
		if (label != null) {
			element.setAttribute("label", label);
		}
		return element;
	}

	private Date date;

	/*
	 * private MonadInteger monadYear;
	 * 
	 * private MonadMonth monadMonth;
	 * 
	 * private MonadDay monadDay;
	 */
	// protected Calendar cal = getCalendar();
	public MonadDate() throws ProgrammerException, UserException {
		init(null);
		update(new Date());
	}

	public MonadDate(Date date) throws ProgrammerException, UserException {
		init(null);
		update(date);
	}

	public MonadDate(String label, String dateStr) throws UserException,
			ProgrammerException {
		init(label);
		update(dateStr);
	}

	public MonadDate(String dateStr) throws UserException, ProgrammerException {
		init(null);
		update(dateStr);
	}

	public MonadDate(String label, Date date) throws ProgrammerException,
			UserException {
		init(label);
		update(date);
	}

	public MonadDate(String label, String year, String month, String day)
			throws ProgrammerException, UserException {
		init(label);
		update(year, month, day);
	}

	public MonadDate(int year, MonadMonth month, MonadDay day)
			throws ProgrammerException, UserException {
		init(null);
		update(year, month, day);
	}

	private void init(String label) {
		setTypeName("date");
		setLabel(label);
	}

	protected void update(String year, String month, String day)
			throws ProgrammerException, UserException {
		update(new MonadInteger("year", year).getInteger(), new MonadMonth(
				month), new MonadDay(day));
	}

	public void initLast(int year, MonadMonth month, MonadDay day)
			throws ProgrammerException, UserException {
		update(year, month, day);
	}

	public void update(String dateStr) throws UserException,
			ProgrammerException {
		Date date = null;
		SimpleDateFormat sdFormat = dateStr.trim().length() > 10 ? sdIsoDateTime()
				: sdIsoDate();

		try {
			date = sdFormat.parse(dateStr);
		} catch (ParseException e) {
			throw UserException.newInvalidParameter("The date '" + dateStr
					+ "' must be of the form yyyy-MM-dd or yyyy-MM-ddThh:mmZ.");
		}
		setDate(date);
	}

	public Date getDate() {
		return date;
	}

	public void setDate(Date date) {
		this.date = date;
	}

	public void update(int year, MonadMonth month, MonadDay day)
			throws ProgrammerException, UserException {
		Calendar cal = getCalendar();
		cal.clear();
		try {
			cal.set(year, month.getInteger().intValue() - 1, day.getInteger()
					.intValue());
			update(cal.getTime());
		} catch (IllegalArgumentException e) {
			throw UserException.newInvalidParameter("Invalid date.");
		}
	}

	public void update(Date date) throws ProgrammerException, UserException {
		if (date == null) {
			throw new ProgrammerException("The date may not be null");
		}
		setDate(date);
	}

	/*
	 * private MonadInstantiationException getMonadInstantiationException() { if
	 * (ex == null) { ex = new MonadInstantiationException(getTypeName(),
	 * getLabel()); } return ex; }
	 */
	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		return toXML(date, getLabel(), doc);
	}

	/*
	 * public String getYear() { return sdYear.format(date); }
	 * 
	 * public String getMonth() { return sdMonth.format(date); }
	 * 
	 * public String getDay() { return sdDay.format(date); }
	 * 
	 * public String getHour() { return sdHour.format(date); }
	 * 
	 * public String getMinute() { return sdMinute.format(date); }
	 */
	public static Element getMonthsXml(Document doc) {
		Element monthsElement = doc.createElement("months");

		for (int i = 1; i < 13; i++) {
			Element month = doc.createElement("month");
			StringBuffer number = new StringBuffer(Integer.toString(i));

			if (i < 10) {
				number.insert(0, "0");
			}
			month.setAttribute("number", number.toString());
			monthsElement.appendChild(month);
		}
		return monthsElement;
	}

	public static Element getDaysXml(Document doc) {
		Element daysElement = doc.createElement("days");

		for (int i = 1; i < 32; i++) {
			Element dayElement = doc.createElement("day");
			StringBuffer number = new StringBuffer(Integer.toString(i));

			if (i < 10) {
				number.insert(0, "0");
			}
			dayElement.setAttribute("number", number.toString());
			daysElement.appendChild(dayElement);
		}
		return daysElement;
	}

	public String toString() {
		return sdIsoDateTime().format(date);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof MonadDate) {
			Date dateToCompare = ((MonadDate) obj).getDate();
			isEqual = getDate().equals(dateToCompare);
		}
		return isEqual;
	}
}