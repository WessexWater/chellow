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

import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Tpr extends PersistentEntity {
	static public Tpr findTpr(String code) {
		return (Tpr) Hiber.session().createQuery(
				"from Tpr tpr where tpr.code = :code").setString("code", code)
				.uniqueResult();
	}

	static public Tpr getTpr(String code) throws HttpException {
		Tpr tpr = findTpr(code);
		if (tpr == null) {
			throw new UserException("Can't find a TPR with code '" + code
					+ "'.");
		}
		return tpr;
	}

	static public Tpr getTpr(long id) throws NotFoundException,
			InternalException {
		Tpr tpr = (Tpr) Hiber.session().get(Tpr.class, id);
		if (tpr == null) {
			throw new NotFoundException();
		}
		return tpr;
	}

	private String code;
	private boolean isTeleswitch;
	private boolean isGmt;

	private Set<ClockInterval> clockIntervals;

	private Set<MeasurementRequirement> measurementRequirements;

	public Tpr() {
	}

	public Tpr(String code, boolean isTeleswitch, boolean isGmt) {
		setClockIntervals(new HashSet<ClockInterval>());
		setCode(code);
		setIsTeleswitch(isTeleswitch);
		setIsGmt(isGmt);
	}

	public Set<ClockInterval> getClockIntervals() {
		return clockIntervals;
	}

	void setClockIntervals(Set<ClockInterval> clockIntervals) {
		this.clockIntervals = clockIntervals;
	}

	public Set<MeasurementRequirement> getMeasurementRequirements() {
		return measurementRequirements;
	}

	void setMeasurementRequirements(
			Set<MeasurementRequirement> measurementRequirements) {
		this.measurementRequirements = measurementRequirements;
	}

	String getCode() {
		return code;
	}

	void setCode(String code) {
		this.code = code;
	}

	public boolean getIsTeleswitch() {
		return isTeleswitch;
	}

	void setIsTeleswitch(boolean isTeleswitch) {
		this.isTeleswitch = isTeleswitch;
	}

	public boolean getIsGmt() {
		return isGmt;
	}

	void setIsGmt(boolean isGmt) {
		this.isGmt = isGmt;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (ClockIntervals.URI_ID.equals(uriId)) {
			return new ClockIntervals(this);
		} else {
			throw new NotFoundException();
		}
	}

	public MonadUri getUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("measurementRequirements",
				new XmlTree("ssc")).put("clockIntervals")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public ClockInterval insertClockInterval(int dayOfWeek, int startDay,
			int startMonth, int endDay, int endMonth, int startHour,
			int startMinute, int endHour, int endMinute) {
		ClockInterval interval = new ClockInterval(this, dayOfWeek, startDay,
				startMonth, endDay, endMonth, startHour, startMinute, endHour,
				endMinute);
		Hiber.session().save(interval);
		Hiber.session().flush();
		return interval;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "tpr");

		element.setAttribute("code", code);
		element.setAttribute("is-teleswitch", String.valueOf(isTeleswitch));
		element.setAttribute("is-gmt", String.valueOf(isGmt));
		return element;
	}

	public String toString() {
		return "Code: " + code + " Is Teleswitch?: " + isTeleswitch
				+ " Is GMT?: " + isGmt;
	}
}
