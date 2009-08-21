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

	static public BillSnag getBillSnag(Long id) throws HttpException {
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

	private Bill bill;

	public BillSnag() {
	}

	public BillSnag(String description, Bill bill) throws HttpException {
		super(description);
		this.bill = bill;
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
		sourceElement.appendChild(toXml(doc, new XmlTree("bill", new XmlTree(
				"account", new XmlTree("contract", new XmlTree("party"))))));
		return doc;
	}

	public MonadUri getUri() throws HttpException {
		return new BillSnags(bill)
				.getUri().resolve(getUriId()).append("/");
	}
}
