package net.sf.chellow.physical;

import java.util.Calendar;
import java.util.Date;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;

import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadDay;
import net.sf.chellow.monad.types.MonadMonth;

public class HhEndDate extends MonadDate {
	public static HhEndDate getNext(HhEndDate date) throws ProgrammerException,
			UserException {
		return new HhEndDate(new Date(getNext(getCalendar(), date.getDate()
				.getTime())));
	}

	public static HhEndDate getPrevious(HhEndDate date)
			throws ProgrammerException, UserException {
		return new HhEndDate(new Date(getPrevious(getCalendar(), date.getDate()
				.getTime())));
	}

	public static HhEndDate roundUp(Date date) throws ProgrammerException,
			UserException {
		return new HhEndDate(new Date(roundUp(getCalendar(), date.getTime())));
	}

	public static long getNext(Calendar cal, long date) {
		return roundUp(cal, date + 1);
	}

	protected static long roundUp(Calendar cal, long date) {
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

	public static HhEndDate roundDown(Date date) throws ProgrammerException,
			UserException {
		return new HhEndDate(new Date(roundDown(getCalendar(), date.getTime())));
	}

	public static long getPrevious(Calendar cal, long date) {
		return roundDown(cal, date - 1);
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

	HhEndDate() throws ProgrammerException, UserException {
		super(new Date(0));
		setTypeName();
	}

	public HhEndDate(Date date) throws ProgrammerException, UserException {
		super(date);
		setTypeName();
	}

	public HhEndDate(String label, String year, String month, String day)
			throws ProgrammerException, UserException {
		super(label, year, month, day);
		setTypeName();
	}

	public HhEndDate(int year, MonadMonth month, MonadDay day)
			throws ProgrammerException, UserException {
		super(year, month, day);
		setTypeName();
	}

	public HhEndDate(String dateStr) throws ProgrammerException, UserException {
		super(dateStr);
		setTypeName();
	}

	public HhEndDate(String label, String dateStr) throws ProgrammerException,
			UserException {
		super(label, dateStr);
		setTypeName();
	}
	
	private void setTypeName() {
		setTypeName("hh-end-date");
	}

	public void update(Date date) throws ProgrammerException, UserException {
		if (date == null) {
			throw new ProgrammerException("Date can't be null I'm afraid.");
		}
		Calendar cal = getCalendar();
		cal.clear();
		cal.setTime(date);
		int minute = cal.get(Calendar.MINUTE);
		int second = cal.get(Calendar.SECOND);
		int milliSecond = cal.get(Calendar.MILLISECOND);
		if (minute != 0 && minute != 30) {
			throw UserException.newInvalidParameter("For the date " + date
					+ ", the minutes must be 0 or 30.");
		}
		if (second != 0) {
			throw UserException.newInvalidParameter("For the date " + date
					+ ", the seconds must be 0.");
		}
		if (milliSecond != 0) {
			throw UserException.newInvalidParameter("For the date " + date
					+ ", the milliseconds must be 0.");
		}
		super.update(cal.getTime());
	}

	public HhEndDate getPrevious() throws ProgrammerException, UserException {
		return getPrevious(this);
	}

	public HhEndDate getNext() throws ProgrammerException, UserException {
		return getNext(this);
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		return toXML(getDate(), getLabel(), doc, getTypeName());
	}

}
