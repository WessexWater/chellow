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

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Bill extends PersistentEntity {
	public static Bill getBill(Long id) throws HttpException {
		Bill bill = (Bill) Hiber.session().get(Bill.class, id);
		if (bill == null) {
			throw new UserException("There isn't a bill with that id.");
		}
		return bill;
	}

	private Mpan mpan;

	private DayStartDate startDate; // Excluding rejected invoices

	// private boolean isStartFuzzy;

	private DayFinishDate finishDate; // Excluding rejected invoices

	// private boolean isFinishFuzzy;

	private BigDecimal net; // Excluding rejected invoices

	private BigDecimal vat; // Excluding rejected invoices

	private Set<Invoice> invoices;

	public Bill() {
	}

	public Bill(Mpan mpan) throws InternalException {
		setMpan(mpan);
	}

	void setInvoices(Set<Invoice> invoices) {
		this.invoices = invoices;
	}

	public Set<Invoice> getInvoices() {
		return invoices;
	}

	public void attach(Invoice invoice) throws HttpException {
		invoice.setBill(this);
		if (invoices == null) {
			invoices = new HashSet<Invoice>();
		}
		invoices.add(invoice);
		setSummary();
	}

	@SuppressWarnings("unchecked")
	public void detach(Invoice invoice) throws HttpException {
		mpan.addSnag(MpanSnag.MISSING_BILL, getStartDate(), getFinishDate());
		invoices.remove(invoice);
		invoice.setBill(null);
		Hiber.flush();
		for (BillSnag snag : (List<BillSnag>) Hiber.session().createQuery(
		"from BillSnag snag where snag.bill = :bill").setEntity(
		"bill", this).list()) {
			Hiber.session().delete(snag);
			Hiber.flush();
		}
		if (invoices.isEmpty()) {
			Hiber.session().delete(this);
			Hiber.flush();
		} else {
			List<Invoice> tempInvoices = new ArrayList<Invoice>();
			for (Invoice tempInvoice : invoices) {
				tempInvoices.add(tempInvoice);
			}
			for (Invoice invoiceToRemove : tempInvoices) {
				invoices.remove(invoiceToRemove);
			}
			for (Invoice invoiceToAttach : tempInvoices) {
				getMpan().attach(invoiceToAttach);
			}
		}

		//account.checkMissing(billStart, billFinish);
	}

	private void setSummary() throws HttpException {
		if (getStartDate() != null) {
			mpan.deleteSnag(MpanSnag.MISSING_BILL, getStartDate(),
					getFinishDate());
		}
		//HhEndDate oldStartDate = getStartDate();
		DayStartDate startDate = null;
		// boolean isStartFuzzy = false;
		//HhEndDate oldFinishDate = getFinishDate();
		DayFinishDate finishDate = null;
		// boolean isFinishFuzzy = false;
		BigDecimal net = new BigDecimal(0);
		BigDecimal vat = new BigDecimal(0);
		for (Invoice invoice : invoices) {
			if (startDate == null
					|| invoice.getStartDate().getDate().before(
							startDate.getDate())) {
				startDate = invoice.getStartDate();
				// if (invoice.getIsStartFuzzy()) {
				// isStartFuzzy = true;
				// }
			}
			if (finishDate == null
					|| invoice.getFinishDate().getDate().before(
							finishDate.getDate())) {
				finishDate = invoice.getFinishDate();
				// if (invoice.getIsFinishFuzzy()) {
				// isFinishFuzzy = true;
				// }
			}
			net = net.add(invoice.getNet());
			vat = vat.add(invoice.getVat());
		}
		setStartDate(startDate);
		// setIsStartFuzzy(isStartFuzzy);
		setFinishDate(finishDate);
		// setIsFinishFuzzy(isFinishFuzzy);
		setNet(net);
		setVat(vat);
		check();
		//if (getStartDate() != null) {
		//	getAccount().checkMissing(oldStartDate, oldFinishDate);
		// }
	}

	public void check() throws HttpException {
		if (getVirtualBill().getCost() != nonRejectedCost()) {
			addSnag();
		}
	}

	public Mpan getMpan() {
		return mpan;
	}

	public void setMpan(Mpan mpan) {
		this.mpan = mpan;
	}

	public DayStartDate getStartDate() {
		return startDate;
	}

	protected void setStartDate(DayStartDate startDate) {
		this.startDate = startDate;
	}

	/*
	 * public boolean getIsStartFuzzy() { return isStartFuzzy; }
	 * 
	 * protected void setIsStartFuzzy(boolean isStartFuzzy) { this.isStartFuzzy =
	 * isStartFuzzy; }
	 */
	public DayFinishDate getFinishDate() {
		return finishDate;
	}

	protected void setFinishDate(DayFinishDate finishDate) {
		this.finishDate = finishDate;
	}

	/*
	 * public boolean getIsFinishFuzzy() { return isFinishFuzzy; }
	 * 
	 * protected void setIsFinishFuzzy(boolean isFinishFuzzy) {
	 * this.isFinishFuzzy = isFinishFuzzy; }
	 */
	public BigDecimal getNet() {
		return net;
	}

	void setNet(BigDecimal net) {
		this.net = net;
	}

	public BigDecimal getVat() {
		return vat;
	}

	void setVat(BigDecimal vat) {
		this.vat = vat;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "bill");
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXml(doc));
		element.setAttribute("net", net.toString());
		element.setAttribute("vat", vat.toString());
		return element;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billElement = (Element) toXml(doc, new XmlTree("account",
				new XmlTree("contract", new XmlTree("party"))));
		source.appendChild(billElement);
		for (Invoice invoice : (List<Invoice>) Hiber
				.session()
				.createQuery(
						"from Invoice invoice where invoice.bill = :bill order by invoice.startDate.date")
				.setEntity("bill", this).list()) {
			billElement.appendChild(invoice.toXml(doc, new XmlTree("batch",
					new XmlTree("contract"))));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws HttpException {
		return new Bills(mpan).getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		 if (BillSnags.URI_ID.equals(uriId)) {
				return new BillSnags(this);
		 } else {
		throw new NotFoundException();
		 }
	}

	VirtualBill getVirtualBill() throws HttpException {
		return mpan.getContract().virtualBill("total", mpan, startDate,
				finishDate);
	}

	/*
	 * double calculatedCost() throws UserException, ProgrammerException {
	 * Service service = (Service) Hiber .session() .createQuery( "select
	 * distinct invoice.batch.service from Invoice invoice where invoice.bill =
	 * :bill") .setEntity("bill", this).uniqueResult(); BillElement billElement =
	 * return billElement.getCost(); }
	 */
	@SuppressWarnings("unchecked")
	double nonRejectedCost() {
		double nonRejectedCost = 0;
		for (Invoice invoice : (List<Invoice>) Hiber
				.session()
				.createQuery(
						"from Invoice invoice where invoice.bill = :bill and invoice.status <> :rejected")
				.setEntity("bill", this).setInteger("rejected",
						Invoice.REJECTED).list()) {
			nonRejectedCost += invoice.getNet().doubleValue() + invoice.getVat().doubleValue();
		}
		return nonRejectedCost;
	}

	void update() {

	}

	private BillSnag addSnag() throws HttpException {
		BillSnag snag = (BillSnag) Hiber.session().createQuery(
				"from BillSnag snag where snag.bill = :bill").setEntity("bill",
				this).uniqueResult();

		if (snag == null) {
			BillSnag
					.insertBillSnag(new BillSnag(BillSnag.INCORRECT_BILL, this));
		}
		return snag;
	}
}
