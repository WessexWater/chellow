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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.Snag;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class BillSnag extends Snag {
	public static final String INCORRECT_BILL = "Incorrect";

	// public static final String CALCULATION_ERROR = "Calculation error";

	static public BillSnag getBillSnag(Long id) throws HttpException,
			InternalException {
		BillSnag snag = (BillSnag) Hiber.session().get(BillSnag.class, id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	public static void insertBillSnag(BillSnag snag) {
		Hiber.session().save(snag);
	}

	public static void deleteBillSnag(BillSnag snag) {
		Hiber.session().delete(snag);
	}

	private SupplierContract contract;

	private Bill bill;

	public BillSnag() {
	}

	public BillSnag(String description, Bill bill)
			throws HttpException {
		super(description);
		this.contract = SupplierContract.getSupplierContract(bill.getAccount().getContract().getId());
		this.bill = bill;
	}

	public SupplierContract getContract() {
		return contract;
	}

	public void setContract(Contract contract) {
		this.contract = (SupplierContract) contract;
	}

	public Bill getBill() {
		return bill;
	}

	void setBill(Bill bill) {
		this.bill = bill;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "bill-snag");
		return element;
	}

	public BillSnag copy() throws InternalException {
		BillSnag cloned;
		try {
			cloned = (BillSnag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return super.toString();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("contract",
				new XmlTree("provider").put("organization")).put(
				"bill", new XmlTree("account"))));
		return doc;
	}

	public MonadUri getUri() throws HttpException {
		return getContract().getSnagsAccountInstance().getUri().resolve(
				getUriId()).append("/");
	}
}
