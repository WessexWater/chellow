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

import java.util.Date;
import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadDouble;
import net.sf.chellow.monad.types.MonadInteger;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.RegisterRead;
import net.sf.chellow.physical.RegisterReadRaw;
import net.sf.chellow.physical.RegisterReads;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Invoice extends PersistentEntity implements Urlable {
	public static final int PENDING = 0;

	public static final int PAID = 1;

	public static final int REJECTED = 2;

	public static Invoice getInvoice(Long id) throws UserException,
			ProgrammerException {
		Invoice invoice = (Invoice) Hiber.session().get(Invoice.class, id);
		if (invoice == null) {
			throw UserException.newOk("There isn't an invoice with that id.");
		}
		return invoice;
	}

	private Batch batch;

	private Bill bill;

	private DayStartDate issueDate;

	private DayStartDate startDate;

	private DayFinishDate finishDate;

	private double net;

	private double vat;

	private String invoiceText;

	private String accountText;

	private String mpanText;

	private int status;

	private InvoiceType type;

	private Set<RegisterRead> reads;

	public Invoice() {
		setTypeName("invoice");
	}

	@SuppressWarnings("unchecked")
	public Invoice(Batch batch, Bill bill, InvoiceRaw invoiceRaw)
			throws UserException, ProgrammerException {
		this();
		setBatch(batch);
		setBill(bill);
		internalUpdate(invoiceRaw.getIssueDate(), invoiceRaw.getStartDate(),
				invoiceRaw.getFinishDate(), invoiceRaw.getNet(), invoiceRaw
						.getVat(), PENDING);
		setInvoiceText(invoiceRaw.getInvoiceText());
		setAccountText(invoiceRaw.getAccountText());
		setMpanText(invoiceRaw.getMpanText());
	}

	public Batch getBatch() {
		return batch;
	}

	public void setBatch(Batch batch) {
		this.batch = batch;
	}

	public Bill getBill() {
		return bill;
	}

	public void setBill(Bill bill) {
		this.bill = bill;
	}

	public DayStartDate getIssueDate() {
		return issueDate;
	}

	protected void setIssueDate(DayStartDate issueDate) {
		this.issueDate = issueDate;
	}

	public DayStartDate getStartDate() {
		return startDate;
	}

	protected void setStartDate(DayStartDate startDate) {
		this.startDate = startDate;
	}

	public DayFinishDate getFinishDate() {
		return finishDate;
	}

	protected void setFinishDate(DayFinishDate finishDate) {
		this.finishDate = finishDate;
	}

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

	public String getInvoiceText() {
		return invoiceText;
	}

	public void setInvoiceText(String invoiceText) {
		this.invoiceText = invoiceText;
	}

	public String getAccountText() {
		return accountText;
	}

	public void setAccountText(String accountText) {
		this.accountText = accountText;
	}

	public String getMpanText() {
		return mpanText;
	}

	public void setMpanText(String mpanText) {
		this.mpanText = mpanText;
	}

	public int getStatus() {
		return status;
	}

	public void setStatus(int status) {
		this.status = status;
	}

	public InvoiceType getType() {
		return type;
	}

	public void setType(InvoiceType type) {
		this.type = type;
	}

	void setReads(Set<RegisterRead> reads) {
		this.reads = reads;
	}

	public Set<RegisterRead> getReads() {
		return reads;
	}

	private void internalUpdate(DayStartDate issueDate, DayStartDate startDate,
			DayFinishDate finishDate, double net, double vat, int status)
			throws UserException, ProgrammerException {
		setIssueDate(issueDate);
		if (startDate.getDate().after(finishDate.getDate())) {
			throw UserException
					.newInvalidParameter("The bill start date can't be after the finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		setNet(net);
		setVat(vat);
		if (status != PENDING && status != PAID && status != REJECTED) {
			throw UserException
					.newInvalidParameter("The status must be 'pending', 'paid' or 'rejected'.");
		}
		setStatus(status);
	}

	public void update(Account account, DayStartDate issueDate,
			DayStartDate startDate, DayFinishDate finishDate, double net,
			double vat, int status) throws UserException, ProgrammerException {
		Account oldAccount = getBill().getAccount();

		internalUpdate(issueDate, startDate, finishDate, net, vat, status);
		oldAccount.detach(this);
		account.attach(this);
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);
		issueDate.setLabel("issue");
		element.appendChild(issueDate.toXML(doc));
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
		element.setAttributeNode(MonadInteger.toXml(doc, "status", status));
		return element;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendSeeOther(batch.invoicesInstance().getUri());
		} else {
			String accountReference = inv.getString("account-reference");
			Date issueDate = inv.getDate("issue-date");
			Date startDate = inv.getDate("start-date");
			Date finishDate = inv.getDate("finish-date");
			Double net = inv.getDouble("net");
			Double vat = inv.getDouble("vat");
			Integer status = inv.getInteger("status");
			if (!inv.isValid()) {
				throw UserException.newInvalidParameter(document());
			}
			update(batch.getService().getProvider()
					.getAccount(accountReference), new DayStartDate(issueDate),
					new DayStartDate(startDate).getNext(), new DayFinishDate(
							finishDate), net, vat, status);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element invoiceElement = (Element) getXML(new XmlTree("batch",
				new XmlTree("service", new XmlTree("provider", new XmlTree(
						"organization")))).put("bill", new XmlTree("account")),
				doc);
		source.appendChild(invoiceElement);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		for (RegisterRead read : reads) {
			invoiceElement.appendChild(read.getXML(new XmlTree("mpan",
					new XmlTree("mpanCore").put("supplyGeneration",
							new XmlTree("supply"))), doc));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return batch.invoicesInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (RegisterReads.URI_ID.equals(uriId)) {
			return registerReadsInstance();
		} else {
			throw UserException.newNotFound();
		}
	}

	public RegisterReads registerReadsInstance() {
		return new RegisterReads(this);
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
	}

	public RegisterRead insertRead(Mpan mpan, RegisterReadRaw rawRead)
			throws UserException, ProgrammerException {
		RegisterRead read = new RegisterRead(mpan, rawRead, this);
		if (reads == null) {
			reads = new HashSet<RegisterRead>();
		}
		reads.add(read);
		Hiber.flush();
		return read;
	}

	@SuppressWarnings("unchecked")
	public void delete() throws ProgrammerException, UserException {
		bill.removeInvoice(this);
		reads.clear();
		Hiber.flush();
		Hiber.session().delete(this);
	}
}