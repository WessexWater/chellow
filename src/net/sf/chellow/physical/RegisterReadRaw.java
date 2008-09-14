package net.sf.chellow.physical;

import net.sf.chellow.billing.DayFinishDate;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.types.MonadObject;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RegisterReadRaw extends MonadObject {
	private MpanRaw mpanRaw;

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

	public RegisterReadRaw(MpanRaw mpanRaw, float coefficient,
			String meterSerialNumber, Units units, int tpr,
			DayFinishDate previousDate, float previousValue,
			ReadType previousType, DayFinishDate presentDate,
			float presentValue, ReadType presentType) throws InternalException {
		if (mpanRaw == null) {
			throw new InternalException("mpan raw argument can't be null.");
		}
		this.mpanRaw = mpanRaw;
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

	public MpanRaw getMpanRaw() {
		return mpanRaw;
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
		element.setAttribute("mpan", mpanRaw.toString());
		element.setAttribute("coefficient", Float.toString(coefficient));
		element.setAttribute("meter-serial-number", meterSerialNumber);
		element.setAttribute("units", Units.name(units));
		element.setAttribute("tpr", Integer.toString(tpr));
		previousDate.setLabel("previous");
		element.appendChild(previousDate.toXml(doc));
		element.setAttribute("previous-value", Float.toString(previousValue));
		element.setAttribute("previous-type", ReadType.name(previousType));
		presentDate.setLabel("present");
		element.appendChild(presentDate.toXml(doc));
		element.setAttribute("present-value", Float.toString(presentValue));
		element.setAttribute("present-type", ReadType.name(presentType));
		return element;
	}
}