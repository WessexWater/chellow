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

package net.sf.chellow.billing;

import java.util.Calendar;
import java.util.Date;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class DayStartDate extends HhEndDate {
	public static DayStartDate getNext(DayStartDate date) throws HttpException {
		return new DayStartDate(new Date(getNext(getCalendar(), date.getDate()
				.getTime())));
	}

	public static DayStartDate getPrevious(DayStartDate date)
			throws HttpException {
		return new DayStartDate(new Date(getPrevious(getCalendar(), date
				.getDate().getTime())));
	}

	/*
	 * public static DayEndDate roundUp(Date date) throws ProgrammerException,
	 * UserException { return new DayEndDate(new Date(roundUp(getCalendar(),
	 * date.getTime()))); }
	 */
	public static long getNext(Calendar cal, long date) {
		return roundUp(cal, date + 1);
	}

	public static DayStartDate roundUp(Date date) throws HttpException {
		return new DayStartDate(
				new Date(roundUp(getCalendar(), date.getTime())));
	}

	protected static long roundUp(Calendar cal, long date) {
		HhEndDate.roundUp(cal, date);
		if (cal.get(Calendar.MINUTE) == 0) {
			cal.add(Calendar.MINUTE, 30);
		}
		if (cal.get(Calendar.HOUR_OF_DAY) != 0) {
			cal.set(Calendar.HOUR_OF_DAY, 0);
			cal.add(Calendar.DAY_OF_MONTH, 1);
		}
		return cal.getTimeInMillis();
	}

	public static DayStartDate roundDown(Date date) throws HttpException {
		return new DayStartDate(new Date(roundDown(getCalendar(), date
				.getTime())));
	}

	public static long getPrevious(Calendar cal, long date) {
		return roundDown(cal, date - 1);
	}

	public static long roundDown(Calendar cal, long date) {
		HhEndDate.roundDown(cal, date);
		if (cal.get(Calendar.MINUTE) == 0) {
			cal.set(Calendar.MINUTE, 30);
			cal.add(Calendar.HOUR_OF_DAY, -1);
		}
		if (cal.get(Calendar.HOUR_OF_DAY) != 0) {
			cal.set(Calendar.HOUR_OF_DAY, 0);
			cal.add(Calendar.DAY_OF_MONTH, -1);
		}
		return cal.getTimeInMillis();
	}

	DayStartDate() throws HttpException {
		super(DayStartDate.roundUp(new Date()).getDate());
	}

	public DayStartDate(Date date) throws HttpException {
		super(date);
	}

	public DayStartDate(String label, String year, String month, String day)
			throws HttpException {
		super(label, year, month, day);
		setTypeName();
	}

	public DayStartDate(int year, int month, int day)
			throws HttpException {
		super(year, month, day);
	}

	public DayStartDate(String dateStr) throws HttpException {
		super(dateStr);
	}

	public DayStartDate(String label, String dateStr) throws HttpException {
		super(label, dateStr);
	}

	private void setTypeName() {
		setTypeName();
	}

	public void update(Date date) throws HttpException {
		super.update(date);
		Calendar cal = getCalendar();
		cal.clear();
		cal.setTime(date);
		if (cal.get(Calendar.HOUR_OF_DAY) != 0) {
			throw new UserException("For the date " + date
					+ ", the hours must be 0.");
		}
		if (cal.get(Calendar.MINUTE) == 0) {
			throw new UserException("For the date " + date
					+ ", the minutes must be 30.");
		}
		super.update(cal.getTime());
	}

	public DayStartDate getPrevious() throws HttpException {
		return getPrevious(this);
	}

	public DayStartDate getNext() throws HttpException {
		return getNext(this);
	}

	public Element toXml(Document doc) throws InternalException {
		return toXML(getDate(), getLabel(), doc, "day-start-date");
	}
}
