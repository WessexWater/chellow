/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.billing;

import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDouble;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.physical.RegisterReadRaw;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class InvoiceRaw extends MonadObject {
	private InvoiceType type;
	
	private DayStartDate issueDate;

	private DayStartDate startDate;

	private DayFinishDate finishDate;

	private double net;

	private double vat;

	private String accountText;

	private String invoiceText;

	private String mpanText;

	private Set<MpanRaw> mpans = new HashSet<MpanRaw>();

	private Set<RegisterReadRaw> reads = new HashSet<RegisterReadRaw>();

	public InvoiceRaw(InvoiceType type, String accountText, String mpanText,
			String invoiceText, DayStartDate issueDate, DayStartDate startDate,
			DayFinishDate finishDate, double net, double vat,
			Set<RegisterReadRaw> registerReads) throws UserException,
			ProgrammerException {
		this.type = type;
		if (issueDate == null) {
			throw new ProgrammerException("The issue date can't be null.");
		}
		this.issueDate = issueDate;
		if (startDate == null) {
			throw new ProgrammerException("The start date can't be null.");
		}
		this.startDate = startDate;
		if (finishDate == null) {
			throw new ProgrammerException("The finish date can't be null.");
		}
		this.finishDate = finishDate;
		this.net = net;
		this.vat = vat;
		if (invoiceText == null) {
			throw UserException
					.newInvalidParameter("The invoiceText parameter is required.");
		}
		this.invoiceText = invoiceText;
		if (accountText == null) {
			throw UserException
					.newInvalidParameter("The accountText parameter is required.");
		}
		this.accountText = accountText;
		if (mpanText == null) {
			throw UserException
					.newInvalidParameter("The mpanText parameter is required.");
		}
		for (String mpanStr : mpanText.split(",")) {
			try {
				mpans.add(new MpanRaw(mpanStr));
			} catch (UserException e) {
				throw UserException
						.newInvalidParameter("While parsing the MPAN string '"
								+ mpanText
								+ "' I encountered difficulties with '"
								+ mpanStr + "'. " + e.getVFMessage().toString());
			}
		}
		this.mpanText = mpanText;
		if (registerReads != null) {
			this.reads = registerReads;
		}
	}

	public InvoiceType getType() {
		return type;
	}

	public Set<MpanRaw> getMpans() {
		return mpans;
	}

	public DayStartDate getIssueDate() {
		return issueDate;
	}
	
	public DayStartDate getStartDate() {
		return startDate;
	}

	public DayFinishDate getFinishDate() {
		return finishDate;
	}

	public double getNet() {
		return net;
	}

	public double getVat() {
		return vat;
	}

	public String getInvoiceText() {
		return invoiceText;
	}

	public String getAccountText() {
		return accountText;
	}

	public String getMpanText() {
		return mpanText;
	}

	public Set<RegisterReadRaw> getRegisterReads() {
		return reads;
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		Element element = doc.createElement("invoice-raw");
		startDate.setLabel("start");
		element.appendChild(startDate.toXML(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXML(doc));
		element.setAttributeNode(MonadDouble.toXml(doc, "net", net));
		element.setAttributeNode(MonadDouble.toXml(doc, "vat", vat));
		element.setAttributeNode(MonadString.toXml(doc, "invoice-text",
				invoiceText));
		element.setAttributeNode(MonadString.toXml(doc, "account-text",
				accountText));
		element.setAttributeNode(MonadString.toXml(doc, "mpan-text", mpanText));
		return element;
	}
}