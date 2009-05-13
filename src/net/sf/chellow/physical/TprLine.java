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
package net.sf.chellow.physical;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
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
			int minuteTo, boolean isGmt) throws HttpException,
			InternalException {
		if (monthFrom < 1 || monthFrom > 12) {
			throw new UserException(
					"'Month from' must be between 1 and 12 inclusive.");
		}
		if (monthTo < 1 || monthTo > 12) {
			throw new UserException(
					"'Month to' must be between 1 and 12 inclusive.");
		}
		if (dayOfWeekFrom < 1 || dayOfWeekFrom > 7) {
			throw new UserException(
					"The 'day of week from' must be between 1 (Sunday) and 7 (Saturday).");
		}
		if (dayOfWeekTo < 1 || dayOfWeekTo > 7) {
			throw new UserException(
					"The 'day of week to' must be between 1 (Sunday) and 7 (Saturday).");
		}
		if (hourFrom < 0 || hourFrom > 23) {
			throw new UserException(
					"The 'hour from' must be between 0 and 23 inclusive.");
		}
		if (minuteFrom != 0 && minuteFrom != 30) {
			throw new UserException("The 'minute from' must be either 0 or 30.");
		}
		if (hourTo < 0 || hourTo > 23) {
			throw new UserException(
					"The 'hour to' must be between 0 and 23 inclusive.");
		}
		if (minuteTo != 0 && minuteTo != 30) {
			throw new UserException("The 'minute to' must be either 0 or 30.");
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

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("lines")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws InternalException,
			HttpException {
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
