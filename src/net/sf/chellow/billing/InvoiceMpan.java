/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class InvoiceMpan extends PersistentEntity {
	static public InvoiceMpan getInvoiceMpan(Long id) throws HttpException {
		InvoiceMpan invoiceMpan = (InvoiceMpan) Hiber.session().get(
				InvoiceMpan.class, id);
		if (invoiceMpan == null) {
			throw new UserException("There is no invoice-mpan with that id.");
		}
		return invoiceMpan;
	}

	private Invoice invoice;

	private Mpan mpan;

	InvoiceMpan() {
	}

	InvoiceMpan(Invoice invoice, Mpan mpan) {
		setInvoice(invoice);
		setMpan(mpan);
	}

	public Invoice getInvoice() {
		return invoice;
	}

	public void setInvoice(Invoice invoice) {
		this.invoice = invoice;
	}

	public Mpan getMpan() {
		return mpan;
	}

	protected void setMpan(Mpan mpan) {
		this.mpan = mpan;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "invoice-mpan");
		return element;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof InvoiceMpan) {
			isEqual = ((InvoiceMpan) obj).getId().equals(getId());
		}
		return isEqual;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		/*
		 * getSite().detachSiteSupply(this); Hiber.commit();
		 * inv.sendOk(MonadUtilsUI.newSourceDocument());
		 */
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}