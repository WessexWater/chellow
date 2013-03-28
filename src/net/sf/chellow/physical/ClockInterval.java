/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;

public class ClockInterval extends PersistentEntity {
	static public ClockInterval getClockInterval(long id) throws HttpException {
		ClockInterval interval = (ClockInterval) Hiber.session().get(
				ClockInterval.class, id);
		if (interval == null) {
			throw new NotFoundException();
		}
		return interval;
	}


	private Tpr tpr;
	private int dayOfWeek;
	private int startDay;
	private int startMonth;
	private int endDay;
	private int endMonth;
	private int startHour;
	private int startMinute;
	private int endHour;
	private int endMinute;

	public ClockInterval() {
	}

	public ClockInterval(Tpr tpr, int dayOfWeek, int startDay, int startMonth,
			int endDay, int endMonth, int startHour, int startMinute,
			int endHour, int endMinute) {
		setTpr(tpr);
		setDayOfWeek(dayOfWeek);
		setStartDay(startDay);
		setStartMonth(startMonth);
		setEndDay(endDay);
		setEndMonth(endMonth);
		setStartHour(startHour);
		setStartMinute(startMinute);
		setEndHour(endHour);
		setEndMinute(endMinute);
	}

	public Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}

	public int getDayOfWeek() {
		return dayOfWeek;
	}

	void setDayOfWeek(int dayOfWeek) {
		this.dayOfWeek = dayOfWeek;
	}

	public int getStartDay() {
		return startDay;
	}

	void setStartDay(int startDay) {
		this.startDay = startDay;
	}

	public int getStartMonth() {
		return startMonth;
	}

	void setStartMonth(int startMonth) {
		this.startMonth = startMonth;
	}

	public int getEndDay() {
		return endDay;
	}

	void setEndDay(int endDay) {
		this.endDay = endDay;
	}

	public int getEndMonth() {
		return endMonth;
	}

	void setEndMonth(int endMonth) {
		this.endMonth = endMonth;
	}

	public int getStartHour() {
		return startHour;
	}

	void setStartHour(int startHour) {
		this.startHour = startHour;
	}

	public int getStartMinute() {
		return startMinute;
	}

	void setStartMinute(int startMinute) {
		this.startMinute = startMinute;
	}

	public int getEndHour() {
		return endHour;
	}

	void setEndHour(int endHour) {
		this.endHour = endHour;
	}

	public int getEndMinute() {
		return endMinute;
	}

	void setEndMinute(int endMinute) {
		this.endMinute = endMinute;
	}
}
