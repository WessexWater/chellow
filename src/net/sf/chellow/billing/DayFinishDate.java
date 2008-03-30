package net.sf.chellow.billing;

import java.util.Calendar;
import java.util.Date;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;

import net.sf.chellow.monad.types.MonadDay;
import net.sf.chellow.monad.types.MonadMonth;
import net.sf.chellow.physical.HhEndDate;

public class DayFinishDate extends HhEndDate {
	public static DayFinishDate getNext(DayFinishDate date) throws ProgrammerException,
			UserException {
		return new DayFinishDate(new Date(getNext(getCalendar(), date.getDate()
				.getTime())));
	}

	public static DayFinishDate getPrevious(DayFinishDate date)
			throws ProgrammerException, UserException {
		return new DayFinishDate(new Date(getPrevious(getCalendar(), date.getDate()
				.getTime())));
	}
/*
	public static DayEndDate roundUp(Date date) throws ProgrammerException,
			UserException {
		return new DayEndDate(new Date(roundUp(getCalendar(), date.getTime())));
	}
*/
	public static long getNext(Calendar cal, long date) {
		return roundUp(cal, date + 1);
	}

	protected static long roundUp(Calendar cal, long date) {
		HhEndDate.roundUp(cal, date);
		if (cal.get(Calendar.MINUTE) == 30) {
			cal.set(Calendar.MINUTE, 0);
			cal.add(Calendar.HOUR_OF_DAY, 1);
		}
		if (cal.get(Calendar.HOUR_OF_DAY) > 0) {
			cal.set(Calendar.HOUR_OF_DAY, 0);
			cal.add(Calendar.DAY_OF_MONTH, 1);
		}
		return cal.getTimeInMillis();
	}

	public static DayFinishDate roundDown(Date date) throws ProgrammerException,
			UserException {
		return new DayFinishDate(new Date(roundDown(getCalendar(), date.getTime())));
	}

	public static long getPrevious(Calendar cal, long date) {
		return roundDown(cal, date - 1);
	}

	public static long roundDown(Calendar cal, long date) {
		roundUp(cal, date);
		cal.add(Calendar.DAY_OF_MONTH, -1);
		return cal.getTimeInMillis();
	}

	DayFinishDate() throws ProgrammerException, UserException {
		super(new Date(0));
		setTypeName();
	}

	public DayFinishDate(Date date) throws ProgrammerException, UserException {
		super(date);
		setTypeName();
	}
	
	public DayFinishDate(HhEndDate date) throws ProgrammerException, UserException {
		super(date.getDate());
		setTypeName();
	}

	public DayFinishDate(String label, String year, String month, String day)
			throws ProgrammerException, UserException {
		super(label, year, month, day);
		setTypeName();
	}

	public DayFinishDate(int year, MonadMonth month, MonadDay day)
			throws ProgrammerException, UserException {
		super(year, month, day);
		setTypeName();
	}

	public DayFinishDate(String dateStr) throws ProgrammerException, UserException {
		super(dateStr);
		setTypeName();
	}

	public DayFinishDate(String label, String dateStr) throws ProgrammerException,
			UserException {
		super(label, dateStr);
		setTypeName();
	}
	
	private void setTypeName() {
		setTypeName("day-finish-date");
	}

	public void update(Date date) throws ProgrammerException, UserException {
		super.update(date);
		Calendar cal = getCalendar();
		cal.clear();
		cal.setTime(date);
		if (cal.get(Calendar.HOUR_OF_DAY) != 0) {
			throw UserException.newInvalidParameter("For the date " + date
					+ ", the hours must be 0.");
		}
		if (cal.get(Calendar.MINUTE) == 30) {
			throw UserException.newInvalidParameter("For the date " + date
					+ ", the minutes must be 0.");
		}
	}

	public DayFinishDate getPrevious() throws ProgrammerException, UserException {
		return getPrevious(this);
	}

	public DayFinishDate getNext() throws ProgrammerException, UserException {
		return getNext(this);
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		return toXML(getDate(), getLabel(), doc, getTypeName());
	}

}
