/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.Snag;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class BillSnag extends Snag {
	public static final String INCORRECT_BILL = "Incorrect";
	//public static final String CALCULATION_ERROR = "Calculation error";

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

	private Service service;

	private Bill bill;

	public BillSnag() {
		setTypeName("bill-snag");
	}

	public BillSnag(String description, Service service, Bill bill)
			throws InternalException, HttpException {
		super(description);
		this.service = service;
		this.bill = bill;
	}

	public Service getService() {
		return service;
	}

	public void setService(Service service) {
		this.service = service;
	}

	public Bill getBill() {
		return bill;
	}

	void setBill(Bill bill) {
		this.bill = bill;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = (Element) super.toXml(doc);
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

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("service", new XmlTree(
						"provider", new XmlTree("organization"))).put("bill",
						new XmlTree("account"))));
		return doc;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getUri() throws InternalException, HttpException {
		return getService().getSnagsAccountInstance().getUri().resolve(
				getUriId()).append("/");
	}
}
