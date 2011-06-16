/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
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

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MonadDate extends MonadObject {
	static private Calendar calendar = new GregorianCalendar(
			TimeZone.getTimeZone("GMT"), Locale.UK);
	static {
		calendar.setLenient(false);
		calendar.clear();
	}

	static public SimpleDateFormat sdIsoDate() {
		SimpleDateFormat sdFormat = new SimpleDateFormat("yyyy-MM-dd");
		sdFormat.setCalendar(getCalendar());
		return sdFormat;
	}

	static public SimpleDateFormat sdIsoDateTime() {
		SimpleDateFormat sdFormat = new SimpleDateFormat(
				"yyyy-MM-dd'T'HH:mm'Z'");
		sdFormat.setCalendar(getCalendar());
		return sdFormat;
	}

	static public Calendar getCalendar() {
		return (Calendar) calendar.clone();
	}

	static public Date intsToDate(int year, int month, int day) {
		Calendar cal = getCalendar();

		cal.set(year, month - 1, day);
		return cal.getTime();
	}

	public static Element getHoursXml(Document doc) {
		Element monthsElement = doc.createElement("hours");

		for (int i = 0; i < 24; i++) {
			Element month = doc.createElement("hour");
			StringBuffer number = new StringBuffer(Integer.toString(i));

			if (i < 10) {
				number.insert(0, "0");
			}
			month.setAttribute("number", number.toString());
			monthsElement.appendChild(month);
		}
		return monthsElement;
	}
	
	public static Element toXML(Date date, String label, Document doc)
			throws InternalException {
		return toXML(date, label, doc, "date");
	}

	public static Element toXML(Date date, String label, Document doc,
			String typeName) throws InternalException {
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

	public MonadDate() throws HttpException {
		update(new Date());
	}

	public MonadDate(Date date) throws HttpException {
		update(date);
	}

	public MonadDate(String label, String dateStr) throws HttpException {
		setLabel(label);
		update(dateStr);
	}

	public MonadDate(String dateStr) throws HttpException {
		update(dateStr);
	}

	public MonadDate(String label, Date date) throws HttpException {
		setLabel(label);
		update(date);
	}

	public MonadDate(String label, String year, String month, String day)
			throws HttpException {
		setLabel(label);
		update(year, month, day);
	}

	public MonadDate(String label, String year, String month, String day,
			String hour, String minute) throws HttpException {
		setLabel(label);
		update(year, month, day, hour, minute);
	}

	public MonadDate(int year, int month, int day) throws HttpException {
		update(year, month, day);
	}

	public MonadDate(int year, int month, int day, int hour, int minute)
			throws HttpException {
		update(year, month, day, hour, minute);
	}

	protected void update(String year, String month, String day)
			throws HttpException {
		update(new MonadInteger("year", year).getInteger(), new MonadInteger(
				month).getInteger(), new MonadInteger(day).getInteger());
	}

	protected void update(String year, String month, String day, String hour,
			String minute) throws HttpException {
		update(new MonadInteger("year", year).getInteger(), new MonadInteger(
				month).getInteger(), new MonadInteger(day).getInteger(),
				new MonadInteger(hour).getInteger(),
				new MonadInteger(minute).getInteger());
	}

	public void update(String dateStr) throws HttpException {
		Date date = null;
		SimpleDateFormat sdFormat = dateStr.trim().length() > 10 ? sdIsoDateTime()
				: sdIsoDate();

		try {
			date = sdFormat.parse(dateStr);
		} catch (ParseException e) {
			throw new UserException("The date '" + dateStr
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

	public void update(int year, int month, int day) throws HttpException {
		Calendar cal = getCalendar();
		cal.clear();
		try {
			cal.set(year, month - 1, day);
			update(cal.getTime());
		} catch (IllegalArgumentException e) {
			throw new UserException("Invalid date.");
		}
	}

	public void update(int year, int month, int day, int hour, int minute)
			throws HttpException {
		Calendar cal = getCalendar();
		cal.clear();
		try {
			cal.set(year, month - 1, day, hour, minute);
			update(cal.getTime());
		} catch (IllegalArgumentException e) {
			throw new UserException("Invalid date.");
		}
	}

	public void update(Date date) throws HttpException {
		if (date == null) {
			throw new InternalException("The date may not be null");
		}
		setDate(date);
	}

	/*
	 * private MonadInstantiationException getMonadInstantiationException() { if
	 * (ex == null) { ex = new MonadInstantiationException(getTypeName(),
	 * getLabel()); } return ex; }
	 */
	public Element toXml(Document doc) throws InternalException {
		return toXML(date, getLabel(), doc);
	}

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
			isEqual = getDate().getTime() == dateToCompare.getTime();
		}
		return isEqual;
	}
}
