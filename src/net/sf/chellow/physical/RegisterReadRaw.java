package net.sf.chellow.physical;

import net.sf.chellow.billing.DayFinishDate;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadFloat;
import net.sf.chellow.monad.types.MonadObject;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RegisterReadRaw extends MonadObject {
	private MpanRaw mpanRaw;

	private float coefficient;

	private String meterSerialNumber;

	private Units units;

	private int tpr;
	
	private boolean isImport;

	private DayFinishDate previousDate;

	private float previousValue;

	private ReadType previousType;

	private DayFinishDate presentDate;

	private float presentValue;

	private ReadType presentType;

	public RegisterReadRaw(MpanRaw mpanRaw, float coefficient,
			String meterSerialNumber, Units units, int tpr, boolean isImport,
			DayFinishDate previousDate, float previousValue,
			ReadType previousType, DayFinishDate presentDate,
			float presentValue, ReadType presentType)
			throws ProgrammerException {
		if (mpanRaw == null) {
			throw new ProgrammerException("mpan raw argument can't be null.");
		}
		this.mpanRaw = mpanRaw;
		this.coefficient = coefficient;
		this.meterSerialNumber = meterSerialNumber;
		this.units = units;
		this.tpr = tpr;
		this.isImport = isImport;
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

	public boolean getIsImport() {
		return isImport;
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


	public Element toXML(Document doc) throws ProgrammerException,
			UserException {		
		Element element = doc.createElement("register-read-raw");
		element.setAttribute("mpan", mpanRaw.toString());
		element.setAttributeNode(MonadFloat.toXml(doc, "coefficient",
				coefficient));
		element.setAttribute("meter-serial-number", meterSerialNumber);
		element.setAttribute("units", Units.name(units));
		element.setAttribute("tpr", Integer.toString(tpr));
		previousDate.setLabel("previous");
		element.appendChild(previousDate.toXML(doc));
		element.setAttributeNode(MonadFloat.toXml(doc, "previous-value", previousValue));
		element.setAttribute("previous-type", ReadType.name(previousType));
		presentDate.setLabel("current");
		element.appendChild(presentDate.toXML(doc));
		element.setAttributeNode(MonadFloat.toXml(doc, "current-value", presentValue));
		element.setAttribute("current-type", ReadType.name(presentType));
		return element;
	}
}