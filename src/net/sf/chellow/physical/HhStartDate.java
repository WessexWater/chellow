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
package net.sf.chellow.physical;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadObject;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhStartDate extends MonadObject {
	public static long getNext(Calendar cal, long date) {
		return roundUp(cal, date + 1);
	}

	public static long getPrevious(Calendar cal, long date) {
		return roundDown(cal, date - 1);
	}

	public static HhStartDate roundUp(Date date) throws HttpException {
		return new HhStartDate(new Date(roundUp(MonadDate.getCalendar(), date
				.getTime())));
	}

	public static boolean isEqual(HhStartDate date1, HhStartDate date2) {
		if (date1 == null) {
			if (date2 == null) {
				return true;
			} else {
				return false;
			}
		} else {
			if (date2 == null) {
				return false;
			} else {
				return date1.getDate().getTime() == date2.getDate().getTime();
			}
		}
	}

	public static boolean isAfter(HhStartDate date1, HhStartDate date2) {
		if (date1 == null) {
			if (date2 == null) {
				return false;
			} else {
				return true;
			}
		} else {
			return date1.after(date2);
		}
	}

	public static boolean isBefore(HhStartDate date1, HhStartDate date2) {
		if (date1 == null) {
			return false;
		} else {
			return date1.before(date2);
		}
	}

	public static long roundUp(Calendar cal, long date) {
		cal.clear();
		cal.setTimeInMillis(date);
		if (cal.get(Calendar.MILLISECOND) > 0) {
			cal.set(Calendar.MILLISECOND, 0);
			cal.add(Calendar.SECOND, 1);
		}
		if (cal.get(Calendar.SECOND) > 0) {
			cal.set(Calendar.SECOND, 0);
			cal.add(Calendar.MINUTE, 1);
		}
		int minute = cal.get(Calendar.MINUTE);
		if (minute > 0 && minute < 30) {
			cal.set(Calendar.MINUTE, 30);
		} else if (minute > 30) {
			cal.set(Calendar.MINUTE, 0);
			cal.add(Calendar.HOUR_OF_DAY, 1);
		}
		return cal.getTimeInMillis();
	}

	public static HhStartDate roundDown(Date date) throws HttpException {
		return new HhStartDate(new Date(roundDown(MonadDate.getCalendar(), date
				.getTime())));
	}

	public static long roundDown(Calendar cal, long date) {
		cal.clear();
		cal.setTimeInMillis(date);
		cal.set(Calendar.SECOND, 0);
		cal.set(Calendar.MILLISECOND, 0);
		int minute = cal.get(Calendar.MINUTE);
		if (minute < 30) {
			cal.set(Calendar.MINUTE, 0);
		} else if (minute < 60) {
			cal.set(Calendar.MINUTE, 30);
		}
		return cal.getTimeInMillis();
	}

	private Date date;

	public HhStartDate() {
	}

	public HhStartDate(String dateStr) throws HttpException {
		this(new MonadDate(dateStr).getDate());
	}

	public HhStartDate(Date date) throws HttpException {
		if (date == null) {
			throw new InternalException("Date can't be null I'm afraid.");
		}
		Calendar cal = MonadDate.getCalendar();
		cal.setTime(date);
		int minute = cal.get(Calendar.MINUTE);
		int second = cal.get(Calendar.SECOND);
		int milliSecond = cal.get(Calendar.MILLISECOND);
		if (minute != 0 && minute != 30) {
			throw new UserException("For the date " + date
					+ ", the minutes must be 0 or 30.");
		}
		if (second != 0) {
			throw new UserException("For the date " + date
					+ ", the seconds must be 0.");
		}
		if (milliSecond != 0) {
			throw new UserException("For the date " + date
					+ ", the milliseconds must be 0.");
		}
		setDate(date);
	}

	public Date getDate() {
		return date;
	}

	public void setDate(Date date) {
		this.date = date;
	}

	public HhStartDate getPrevious() throws HttpException {
		HhStartDate prev = new HhStartDate();
		prev.setDate(new Date(getPrevious(MonadDate.getCalendar(), date
				.getTime())));
		return prev;
	}

	public HhStartDate getNext() throws HttpException {
		HhStartDate next = new HhStartDate();
		next
				.setDate(new Date(getNext(MonadDate.getCalendar(), date
						.getTime())));
		return next;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = (Element) super.toXml(doc, "hh-start-date");
		Calendar cal = MonadDate.getCalendar();
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
		return element;
	}

	public boolean after(HhStartDate date) {
		if (date == null) {
			return false;
		} else {
			return getDate().after(date.getDate());
		}
	}

	public boolean before(HhStartDate date) {
		if (date == null) {
			return true;
		} else {
			return getDate().before(date.getDate());
		}
	}

	public boolean equals(Object obj) {
		return obj instanceof HhStartDate && isEqual((HhStartDate) obj, this);
	}

	public String toString() {
		return MonadDate.sdIsoDateTime().format(date);
	}
}
