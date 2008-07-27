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

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadDouble;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Bill extends PersistentEntity implements Urlable {
	public static Bill getBill(Long id) throws HttpException,
			InternalException {
		Bill bill = (Bill) Hiber.session().get(Bill.class, id);
		if (bill == null) {
			throw new UserException("There isn't a bill with that id.");
		}
		return bill;
	}

	private Account account;

	private Contract contract;

	private DayStartDate startDate; // Excluding rejected invoices

	// private boolean isStartFuzzy;

	private DayFinishDate finishDate; // Excluding rejected invoices

	// private boolean isFinishFuzzy;

	private double net; // Excluding rejected invoices

	private double vat; // Excluding rejected invoices

	private Set<Invoice> invoices;

	public Bill() {
	}

	@SuppressWarnings("unchecked")
	public Bill(Contract contract, Account account) throws
			InternalException {
		setAccount(account);
		setContract(contract);
	}

	void setInvoices(Set<Invoice> invoices) {
		this.invoices = invoices;
	}

	Set<Invoice> getInvoices() {
		return invoices;
	}
/*
	public Invoice insertInvoice(Batch batch, InvoiceRaw invoiceRaw)
			throws UserException, ProgrammerException {
		if (batch.getService().equals(getService())) {
			throw new ProgrammerException(
					"The batch must be of the same service as the bill.");
		}
		Invoice invoice = new Invoice(batch, this, invoiceRaw);
		attach(invoice);
		return invoice;
	}
*/
	public void attach(Invoice invoice) throws InternalException,
			HttpException {
		invoice.setBill(this);
		if (invoices == null) {
			invoices = new HashSet<Invoice>();
		}
		invoices.add(invoice);
		setSummary();
	}

	@SuppressWarnings("unchecked")
	public void detach(Invoice invoice) throws HttpException {
		HhEndDate billStart = getStartDate();
		HhEndDate billFinish = getFinishDate();
		Contract contract = getContract();
		Account account = getAccount();

		invoices.remove(invoice);
		invoice.setBill(null);
		Hiber.flush();
		if (invoices.isEmpty()) {
			for (BillSnag snag : (List<BillSnag>) Hiber.session().createQuery(
					"from BillSnag snag where snag.bill = :bill").setEntity(
					"bill", this).list()) {
				Hiber.session().delete(snag);
				Hiber.flush();
			}
			Hiber.session().delete(this);
			Hiber.flush();
		} else if (getInvoices().size() > 1) {
			List<Invoice> invoices = new ArrayList<Invoice>(getInvoices());
			invoices.remove(0);
			for (Invoice invoiceToRemove : invoices) {
				getInvoices().remove(invoiceToRemove);
			}
			for (Invoice invoiceToAttach : invoices) {
				getAccount().attach(invoiceToAttach);
			}
		} else {
			setSummary();
		}
		account.checkMissing(contract, billStart, billFinish);
	}

	private void setSummary() throws InternalException, HttpException {
		if (getStartDate() != null) {
			getAccount().addSnag(contract, AccountSnag.MISSING_BILL,
					getStartDate(), getFinishDate(), true);
		}
		HhEndDate oldStartDate = getStartDate();
		DayStartDate startDate = null;
		// boolean isStartFuzzy = false;
		HhEndDate oldFinishDate = getFinishDate();
		DayFinishDate finishDate = null;
		// boolean isFinishFuzzy = false;
		double net = 0;
		double vat = 0;
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
			net += invoice.getNet();
			vat += invoice.getVat();
		}
		setStartDate(startDate);
		// setIsStartFuzzy(isStartFuzzy);
		setFinishDate(finishDate);
		// setIsFinishFuzzy(isFinishFuzzy);
		setNet(net);
		setVat(vat);
		check();
		if (getStartDate() != null) {
			getAccount().checkMissing(contract, oldStartDate, oldFinishDate);
		}
	}

	public void check() throws HttpException, InternalException {
		if (getElement().getCost() != nonRejectedCost()) {
			addSnag(false);
		}
	}

	public Account getAccount() {
		return account;
	}

	public void setAccount(Account account) {
		this.account = account;
	}

	public Contract getContract() {
		return contract;
	}

	public void setContract(Contract contract) {
		this.contract = contract;
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
	public double getNet() {
		return net;
	}

	void setNet(double net) {
		this.net = net;
	}

	public double getVat() {
		return vat;
	}

	void setVat(double vat) {
		this.vat = vat;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "bill");
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXml(doc));
		element.setAttributeNode(MonadDouble.toXml(doc, "net", net));
		element.setAttributeNode(MonadDouble.toXml(doc, "vat", vat));
		return element;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billElement = (Element) toXml(doc, new XmlTree("account",
						new XmlTree("provider", new XmlTree("organization"))));
		source.appendChild(billElement);
		for (Invoice invoice : (List<Invoice>) Hiber
				.session()
				.createQuery(
						"from Invoice invoice where invoice.bill = :bill order by invoice.startDate.date")
				.setEntity("bill", this).list()) {
			billElement.appendChild(invoice.toXml(doc, new XmlTree("batch",
							new XmlTree("service"))));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return account.billsInstance().getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		throw new NotFoundException();
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// deleteBill(this);
		// inv.sendOk();
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	/*
	 * BillElement getElement(String name, String chargeScript) throws
	 * UserException, ProgrammerException { return service.billElement(name,
	 * chargeScript, account, startDate, finishDate); }
	 */

	BillElement getElement(String chargeScript) throws InternalException,
			HttpException {
		return contract.billElement("total", chargeScript, account, startDate,
				finishDate);
	}

	BillElement getElement() throws HttpException, InternalException {
		return contract.billElement("total", account, startDate, finishDate);
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
			nonRejectedCost += invoice.getNet() + invoice.getVat();
		}
		return nonRejectedCost;
	}

	void update() {

	}

	private void addSnag(boolean isResolved) throws InternalException,
			HttpException {
		BillSnag snag = (BillSnag) Hiber.session().createQuery(
				"from BillSnag snag where snag.bill = :bill").setEntity("bill",
				this).uniqueResult();

		if (isResolved) {
			if (snag != null) {
				snag.resolve(false);
			}
		} else {
			if (snag == null) {
				BillSnag.insertBillSnag(new BillSnag(BillSnag.INCORRECT_BILL,
						contract, this));
			} else {
				snag.deResolve();
			}
		}
	}
}