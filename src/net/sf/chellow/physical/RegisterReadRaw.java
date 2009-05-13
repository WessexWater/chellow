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

import net.sf.chellow.billing.DayFinishDate;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.types.MonadObject;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RegisterReadRaw extends MonadObject {
	private MpanCore mpanCore;

	private String meterSerialNumber;

	private int tpr;

	private float coefficient;

	private Units units;

	private DayFinishDate previousDate;

	private float previousValue;

	private ReadType previousType;

	private DayFinishDate presentDate;

	private float presentValue;

	private ReadType presentType;

	public RegisterReadRaw(MpanCore mpanCore, float coefficient,
			String meterSerialNumber, Units units, int tpr,
			DayFinishDate previousDate, float previousValue,
			ReadType previousType, DayFinishDate presentDate,
			float presentValue, ReadType presentType) throws InternalException {
		if (mpanCore == null) {
			throw new InternalException("mpan raw argument can't be null.");
		}
		this.mpanCore = mpanCore;
		this.coefficient = coefficient;
		this.meterSerialNumber = meterSerialNumber;
		this.units = units;
		this.tpr = tpr;
		this.previousDate = previousDate;
		this.previousValue = previousValue;
		this.previousType = previousType;
		this.presentDate = presentDate;
		this.presentValue = presentValue;
		this.presentType = presentType;
	}

	public MpanCore getMpanCore() {
		return mpanCore;
	}

	public float getCoefficient() {
		return coefficient;
	}

	public String getMeterSerialNumber() {
		return meterSerialNumber;
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

	public float getPreviousValue() {
		return previousValue;
	}

	public ReadType getPreviousType() {
		return previousType;
	}

	public DayFinishDate getPresentDate() {
		return presentDate;
	}

	public float getPresentValue() {
		return presentValue;
	}

	public ReadType getPresentType() {
		return presentType;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("register-read-raw");
		element.setAttribute("mpan-core", mpanCore.toString());
		element.setAttribute("coefficient", Float.toString(coefficient));
		element.setAttribute("meter-serial-number", meterSerialNumber);
		element.setAttribute("units", Units.name(units));
		element.setAttribute("tpr", Integer.toString(tpr));
		previousDate.setLabel("previous");
		element.appendChild(previousDate.toXml(doc));
		element.setAttribute("previous-value", Float.toString(previousValue));
		previousType.setLabel("previous");
		element.appendChild(previousType.toXml(doc));
		presentDate.setLabel("present");
		element.appendChild(presentDate.toXml(doc));
		element.setAttribute("present-value", Float.toString(presentValue));
		presentType.setLabel("present");
		element.appendChild(presentType.toXml(doc));
		return element;
	}
}
