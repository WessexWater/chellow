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

import java.math.BigDecimal;

import net.sf.chellow.billing.DayFinishDate;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.types.MonadObject;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RegisterReadRaw extends MonadObject {
	private Meter meter;

	private int tpr;

	private BigDecimal coefficient;

	private Units units;

	private DayFinishDate previousDate;

	private BigDecimal previousValue;

	private ReadType previousType;

	private DayFinishDate presentDate;

	private BigDecimal presentValue;

	private ReadType presentType;

	public RegisterReadRaw(Meter meter, BigDecimal coefficient,
			Units units, int tpr,
			DayFinishDate previousDate, BigDecimal previousValue,
			ReadType previousType, DayFinishDate presentDate,
			BigDecimal presentValue, ReadType presentType) throws InternalException {
		this.coefficient = coefficient;
		this.meter = meter;
		this.units = units;
		this.tpr = tpr;
		this.previousDate = previousDate;
		this.previousValue = previousValue;
		this.previousType = previousType;
		this.presentDate = presentDate;
		this.presentValue = presentValue;
		this.presentType = presentType;
	}

	public BigDecimal getCoefficient() {
		return coefficient;
	}

	public Meter getMeter() {
		return meter;
	}

	public Units getUnits() {
		return units;
	}

	public int getTpr() {
		return tpr;
	}

	public DayFinishDate getPreviousDate() {
		return previousDate;
	}

	public BigDecimal getPreviousValue() {
		return previousValue;
	}

	public ReadType getPreviousType() {
		return previousType;
	}

	public DayFinishDate getPresentDate() {
		return presentDate;
	}

	public BigDecimal getPresentValue() {
		return presentValue;
	}

	public ReadType getPresentType() {
		return presentType;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("register-read-raw");
		element.setAttribute("coefficient", coefficient.toString());
		element.setAttribute("units", Units.name(units));
		element.setAttribute("tpr", Integer.toString(tpr));
		previousDate.setLabel("previous");
		element.appendChild(previousDate.toXml(doc));
		element.setAttribute("previous-value", previousValue.toString());
		previousType.setLabel("previous");
		element.appendChild(previousType.toXml(doc));
		presentDate.setLabel("present");
		element.appendChild(presentDate.toXml(doc));
		element.setAttribute("present-value", presentValue.toString());
		presentType.setLabel("present");
		element.appendChild(presentType.toXml(doc));
		return element;
	}
}
