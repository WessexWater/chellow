package net.sf.chellow.physical;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class TprLine extends PersistentEntity {
	private Tpr tpr;

	private int monthFrom;

	private int monthTo;

	private int dayOfWeekFrom;

	private int dayOfWeekTo;

	private int hourFrom;

	private int minuteFrom;

	private int hourTo;

	private int minuteTo;

	private boolean isGmt;

	TprLine() {
	}

	public TprLine(Tpr tpr, int monthFrom, int monthTo, int dayOfWeekFrom,
			int dayOfWeekTo, int hourFrom, int minuteFrom, int hourTo,
			int minuteTo, boolean isGmt) throws UserException,
			ProgrammerException {
		if (monthFrom < 1 || monthFrom > 12) {
			throw UserException
					.newInvalidParameter("'Month from' must be between 1 and 12 inclusive.");
		}
		if (monthTo < 1 || monthTo > 12) {
			throw UserException
					.newInvalidParameter("'Month to' must be between 1 and 12 inclusive.");
		}
		if (dayOfWeekFrom < 1 || dayOfWeekFrom > 7) {
			throw UserException
					.newInvalidParameter("The 'day of week from' must be between 1 (Sunday) and 7 (Saturday).");
		}
		if (dayOfWeekTo < 1 || dayOfWeekTo > 7) {
			throw UserException
					.newInvalidParameter("The 'day of week to' must be between 1 (Sunday) and 7 (Saturday).");
		}
		if (hourFrom < 0 || hourFrom > 23) {
			throw UserException
					.newInvalidParameter("The 'hour from' must be between 0 and 23 inclusive.");
		}
		if (minuteFrom != 0 && minuteFrom != 30) {
			throw UserException
					.newInvalidParameter("The 'minute from' must be either 0 or 30.");
		}
		if (hourTo < 0 || hourTo > 23) {
			throw UserException
					.newInvalidParameter("The 'hour to' must be between 0 and 23 inclusive.");
		}
		if (minuteTo != 0 && minuteTo != 30) {
			throw UserException
					.newInvalidParameter("The 'minute to' must be either 0 or 30.");
		}
		setTpr(tpr);
		setMonthFrom(monthFrom);
		setMonthTo(monthTo);
		setDayOfWeekFrom(dayOfWeekFrom);
		setDayOfWeekTo(dayOfWeekTo);
		setHourFrom(hourFrom);
		setMinuteFrom(minuteFrom);
		setHourTo(hourTo);
		setMinuteTo(minuteTo);
		setIsGmt(isGmt);
	}

	Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}

	int getMonthFrom() {
		return monthFrom;
	}

	void setMonthFrom(int monthFrom) {
		this.monthFrom = monthFrom;
	}

	int getMonthTo() {
		return monthTo;
	}

	void setMonthTo(int monthTo) {
		this.monthTo = monthTo;
	}

	int getDayOfWeekFrom() {
		return dayOfWeekFrom;
	}

	void setDayOfWeekFrom(int dayOfWeekFrom) {
		this.dayOfWeekFrom = dayOfWeekFrom;
	}

	int getDayOfWeekTo() {
		return dayOfWeekTo;
	}

	void setDayOfWeekTo(int dayOfWeekTo) {
		this.dayOfWeekTo = dayOfWeekTo;
	}

	int getHourFrom() {
		return hourFrom;
	}

	void setHourFrom(int hourFrom) {
		this.hourFrom = hourFrom;
	}

	int getMinuteFrom() {
		return minuteFrom;
	}

	void setMinuteFrom(int minuteFrom) {
		this.minuteFrom = minuteFrom;
	}

	int getHourTo() {
		return hourTo;
	}

	void setHourTo(int hourTo) {
		this.hourTo = hourTo;
	}

	int getMinuteTo() {
		return minuteTo;
	}

	void setMinuteTo(int minuteTo) {
		this.minuteTo = minuteTo;
	}

	boolean getIsGmt() {
		return isGmt;
	}

	void setIsGmt(boolean isGmt) {
		this.isGmt = isGmt;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(getXML(new XmlTree("lines"), doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		Element element = doc.createElement("tpr-line");

		element.setAttribute("month-from", Integer.toString(monthFrom));
		element.setAttribute("month-to", Integer.toString(monthTo));
		element.setAttribute("day-of-week-from", Integer
				.toString(dayOfWeekFrom));
		element.setAttribute("day-of-week-to", Integer.toString(dayOfWeekTo));
		element.setAttribute("hour-from", Integer.toString(hourFrom));
		element.setAttribute("minute-from", Integer.toString(minuteFrom));
		element.setAttribute("hour-to", Integer.toString(hourTo));
		element.setAttribute("minute-to", Integer.toString(minuteTo));
		element.setAttribute("is-gmt", Boolean.toString(isGmt));
		return element;
	}
}
