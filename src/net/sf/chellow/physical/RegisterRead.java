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
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class RegisterRead extends PersistentEntity {
	private Mpan mpan;

	private Invoice invoice;

	private BigDecimal coefficient;

	private Units units;

	private Tpr tpr;

	private DayFinishDate previousDate;

	private BigDecimal previousValue;

	private ReadType previousType;

	private DayFinishDate presentDate;

	private BigDecimal presentValue;

	private ReadType presentType;

	RegisterRead() {
	}

	public RegisterRead(Invoice invoice, RegisterReadRaw rawRead)
			throws HttpException {
		if (invoice == null) {
			throw new InternalException("The invoice must not be null.");
		}
		setInvoice(invoice);
		setTpr(Tpr.getTpr(rawRead.getTpr()));
		setCoefficient(rawRead.getCoefficient());
		setUnits(rawRead.getUnits());
		setPreviousDate(rawRead.getPreviousDate());
		setPreviousValue(rawRead.getPreviousValue());
		setPreviousType(rawRead.getPreviousType());
		setPresentDate(rawRead.getPresentDate());
		setpresentValue(rawRead.getPresentValue());
		setpresentType(rawRead.getPresentType());

		MpanCore mpanCore = rawRead.getMpanCore();
		Supply supply = mpanCore.getSupply();
		SupplyGeneration supplyGeneration = supply.getGeneration(rawRead
				.getPresentDate());
		Mpan importMpan = supplyGeneration.getImportMpan();
		Mpan exportMpan = supplyGeneration.getExportMpan();
		if (importMpan != null
				&& importMpan.getCore().equals(mpanCore)) {
			setMpan(importMpan);
		} else if (exportMpan != null
				&& exportMpan.getCore().equals(mpanCore)) {
			setMpan(exportMpan);
		} else {
			throw new UserException("For the supply " + getId()
					+ " neither the import MPAN core " + importMpan
					+ " or the export MPAN core " + exportMpan
					+ " match the register read MPAN core " + mpanCore
					+ ".");
		}
		precedingRead();
	}

	public Mpan getMpan() {
		return mpan;
	}

	void setMpan(Mpan mpan) {
		this.mpan = mpan;
	}

	public Invoice getInvoice() {
		return invoice;
	}

	void setInvoice(Invoice invoice) {
		this.invoice = invoice;
	}

	BigDecimal getCoefficient() {
		return coefficient;
	}

	void setCoefficient(BigDecimal coefficient) {
		this.coefficient = coefficient;
	}

	Units getUnits() {
		return units;
	}

	void setUnits(Units units) {
		this.units = units;
	}

	public Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}

	DayFinishDate getPreviousDate() {
		return previousDate;
	}

	void setPreviousDate(DayFinishDate previousDate) {
		this.previousDate = previousDate;
	}

	BigDecimal getPreviousValue() {
		return previousValue;
	}

	void setPreviousValue(BigDecimal previousValue) {
		this.previousValue = previousValue;
	}

	public ReadType getPreviousType() {
		return previousType;
	}

	void setPreviousType(ReadType previousType) {
		this.previousType = previousType;
	}

	public DayFinishDate getPresentDate() {
		return presentDate;
	}

	void setPresentDate(DayFinishDate presentDate) {
		this.presentDate = presentDate;
	}

	public BigDecimal getpresentValue() {
		return presentValue;
	}

	void setpresentValue(BigDecimal presentValue) {
		this.presentValue = presentValue;
	}

	public ReadType getpresentType() {
		return presentType;
	}

	void setpresentType(ReadType presentType) {
		this.presentType = presentType;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			Document doc = document();
			Element source = doc.getDocumentElement();
			source.appendChild(new MonadMessage(
					"This register read has been successfully deleted.")
					.toXml(doc));
			inv.sendOk(doc);
		}
	}

	public void delete() {
		Hiber.session().delete(this);
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("invoice", new XmlTree(
				"batch", new XmlTree("contract", new XmlTree("provider")
						.put("organization")))).put(
				"mpan",
				new XmlTree("supplyGeneration", new XmlTree("supply"))
						.put("mpanRaw")).put("tpr")));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "register-read");
		element.setAttribute("coefficient", coefficient.toString());
		element.setAttribute("units", units.toString());
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

	public void attach() {
	}

	private RegisterRead precedingRead() throws HttpException {
		if (previousType.getCode() == ReadType.TYPE_INITIAL) {
			return null;
		}
		RegisterRead read = (RegisterRead) Hiber
				.session()
				.createQuery(
						"from RegisterRead read where read.mpan.mpanCore = :mpanCore and read.presentDate.date = :readDate")
				.setEntity("mpanCore", getMpan().getCore()).setDate(
						"readDate", getPreviousDate().getDate()).uniqueResult();
		if (read == null) {
			throw new UserException(
					"There isn't a preceding read for this read.");
		}
		return read;
	}
}
