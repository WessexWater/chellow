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
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
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

	private String reference;

	private String mpanText;

	private Set<MpanRaw> mpans = new HashSet<MpanRaw>();

	private Set<RegisterReadRaw> reads = new HashSet<RegisterReadRaw>();

	public InvoiceRaw(InvoiceType type, String accountText, String mpanText,
			String reference, DayStartDate issueDate, DayStartDate startDate,
			DayFinishDate finishDate, double net, double vat,
			Set<RegisterReadRaw> registerReads) throws HttpException,
			InternalException {
		this.type = type;
		if (issueDate == null) {
			throw new InternalException("The issue date can't be null.");
		}
		this.issueDate = issueDate;
		if (startDate == null) {
			throw new InternalException("The start date can't be null.");
		}
		this.startDate = startDate;
		if (finishDate == null) {
			throw new InternalException("The finish date can't be null.");
		}
		this.finishDate = finishDate;
		this.net = net;
		this.vat = vat;
		if (reference == null) {
			throw new UserException("The invoiceText parameter is required.");
		}
		this.reference = reference;
		if (accountText == null) {
			throw new UserException("The accountText parameter is required.");
		}
		this.accountText = accountText;
		if (mpanText == null) {
			throw new UserException("The mpanText parameter is required.");
		}
		for (String mpanStr : mpanText.split(",")) {
			try {
				mpans.add(new MpanRaw(mpanStr));
			} catch (HttpException e) {
				throw new UserException("While parsing the MPAN string '"
								+ mpanText
								+ "' I encountered difficulties with '"
								+ mpanStr + "'. " + e.getMessage());
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

	public String getReference() {
		return reference;
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

	public Element toXml(Document doc) throws InternalException {
		Element element = doc.createElement("invoice-raw");
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXml(doc));
		element.setAttribute("net", Double.toString(net));
		element.setAttribute("vat", Double.toString(vat));
		element.setAttribute("reference", reference);
		element.setAttribute("account-reference", accountText);
		element.setAttributeNode(MonadString.toXml(doc, "mpan-text", mpanText));
		return element;
	}
}