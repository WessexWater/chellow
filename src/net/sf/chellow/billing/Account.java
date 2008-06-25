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
import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.SnagDateBounded;
import net.sf.chellow.physical.SupplyGeneration;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Account extends PersistentEntity implements Urlable {
	public static Account getAccount(Long id) throws HttpException,
			InternalException {
		Account account = (Account) Hiber.session().get(Account.class, id);
		if (account == null) {
			throw new UserException("There isn't an account with that id.");
		}
		return account;
	}

	/*
	 * public static void deleteAccount(Account account) throws
	 * ProgrammerException { try { Hiber.session().delete(account);
	 * Hiber.flush(); } catch (HibernateException e) { throw new
	 * ProgrammerException(e); } }
	 */
	@SuppressWarnings("unchecked")
	public static void checkAllMissingFromLatest(Organization organization)
			throws InternalException, HttpException {
		List<Object[]> results = (List<Object[]>) Hiber
				.session()
				.createQuery(
						"select distinct mpan.supplierAccount, mpan.supplierService from Mpan mpan where mpan.supplierAccount.organization = :organization")
				.setEntity("organization", organization).list();
		for (Object[] result : results) {
			((Account) result[0]).checkMissingFromLatest((Service) result[1]);
		}
	}
	
	private Organization organization;

	private Provider provider;

	private String reference;

	public Account() {
	}

	public Account(Organization organization, Provider provider, String reference) {
		setProvider(provider);
		setOrganization(organization);
		update(reference);
	}

	public Organization getOrganization() {
		return organization;
	}

	public void setOrganization(Organization organization) {
		this.organization = organization;
	}

	public String getReference() {
		return reference;
	}

	public void setReference(String reference) {
		this.reference = reference;
	}

	public Provider getProvider() {
		return provider;
	}

	protected void setProvider(Provider provider) {
		this.provider = provider;
	}

	public void update(String reference) {
		setReference(reference);
	}

	public Element toXml(Document doc) throws HttpException {
		setTypeName("account");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("reference", reference);
		if (Supplier.findSupplier(provider.getId()) != null) {
			element.setAttribute("label", "supplier");
		} else {
			element.setAttribute("label", provider.getClass().getName());
		}
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			try {
				provider.deleteAccount(this);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			Supplier supplier = Supplier.findSupplier(provider.getId());
			if (supplier != null) {
				inv.sendSeeOther(organization.accountsInstance().getUri());
			}
		} else {
			String reference = inv.getString("reference");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(reference);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element accountElement = (Element) toXml(doc, new XmlTree("organization")
						.put("provider"));
		source.appendChild(accountElement);
		for (Mpan mpan : (List<Mpan>) Hiber.session().createQuery(
				"from Mpan mpan where mpan.supplierAccount = :account")
				.setEntity("account", this).list()) {
			accountElement.appendChild(mpan.toXml(doc, new XmlTree(
									"supplyGeneration", new XmlTree("supply")).put(
									"mpanTop",
									new XmlTree("profileClass").put("meterTimeswitch").put(
											"llf")).put("mpanCore")));
		}
		for (Bill bill : (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account order by bill.startDate.date")
				.setEntity("account", this).list()) {
			accountElement.appendChild(bill.toXml(doc));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws HttpException {
		return organization.accountsInstance().getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		if (Bills.URI_ID.equals(uriId)) {
			return billsInstance();
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// deleteAccount(this);
		// inv.sendOk();
	}

	public void checkMissingFromLatest(Service service)
			throws InternalException, HttpException {
		checkMissingFromLatest(service, null);
	}

	@SuppressWarnings("unchecked")
	public void checkMissingFromLatest(Service service, HhEndDate to)
			throws InternalException, HttpException {
		List<Bill> bills = (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account and bill.service.id = :serviceId order by bill.finishDate.date desc")
				.setEntity("account", this).setLong("serviceId",
						service.getId()).list();
		Bill latestBill = null;
		if (bills != null && !bills.isEmpty()) {
			latestBill = bills.get(0);
		}
		HhEndDate from = latestBill == null ? null : latestBill.getFinishDate();
		AccountSnag accountSnag = (AccountSnag) Hiber
				.session()
				.createQuery(
						"from AccountSnag snag where snag.account = :account order by snag.finishDate.date")
				.setEntity("account", this).setMaxResults(1).uniqueResult();
		if (accountSnag != null
				&& (from == null || accountSnag.getFinishDate().getDate()
						.after(from.getDate()))) {
			from = accountSnag.getFinishDate();
		}
		checkMissing(service, from, to);
	}

	@SuppressWarnings("unchecked")
	void checkMissing(Service service, HhEndDate from, HhEndDate to)
			throws HttpException {
		List<SupplyGeneration> supplyGenerations = Hiber
		.session()
		.createQuery(
				"select mpan.supplyGeneration from Mpan mpan where mpan.supplierAccount = :account order by mpan.supplyGeneration.startDate.date")
		.setEntity("account", this).list();
		
		if (supplyGenerations.isEmpty()) {
			return;
		}
		if (from == null) {
			from = supplyGenerations.get(0).getStartDate();
		}
		if (to == null) {
			int frequency = 1;
			int profileClass = Integer.parseInt(supplyGenerations.get(0)
					.getMpans().iterator().next().getMpanTop()
					.getProfileClass().getCode().toString());
			if (profileClass < 5 && profileClass > 1) {
				frequency = 3;
			}
			Calendar cal = GregorianCalendar.getInstance(TimeZone
					.getTimeZone("GMT"), Locale.UK);
			cal.set(Calendar.MILLISECOND, 0);
			cal.set(Calendar.SECOND, 0);
			cal.set(Calendar.MINUTE, 0);
			cal.set(Calendar.HOUR_OF_DAY, 0);
			cal.set(Calendar.DAY_OF_MONTH, 1);
			cal.add(Calendar.MONTH, -frequency);
			to = new HhEndDate(cal.getTime());
			HhEndDate lastGenerationFinishDate = supplyGenerations.get(
					supplyGenerations.size() - 1).getFinishDate();
			if (lastGenerationFinishDate != null
					&& lastGenerationFinishDate.getDate().before(to.getDate())) {
				to = lastGenerationFinishDate;
			}
		}
		if (from.getDate().after(to.getDate())) {
			return;
		}
		List<Bill> bills = (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account and bill.service.id = :serviceId and bill.startDate.date <= :to and bill.finishDate.date >= :from order by bill.finishDate.date")
				.setEntity("account", this).setLong("serviceId",
						service.getId()).setTimestamp("to", to.getDate())
				.setTimestamp("from", from.getDate()).list();
		HhEndDate gapStart = from;
		for (int i = 0; i < bills.size(); i++) {
			Bill bill = bills.get(i);
			if (bill.getStartDate().getDate().after(gapStart.getDate())) {
				addSnag(service, AccountSnag.MISSING_BILL, gapStart, bill
						.getStartDate().getPrevious(), false);
			}
			addSnag(service, AccountSnag.MISSING_BILL, bill.getStartDate(),
					bill.getFinishDate(), true);
			gapStart = bill.getFinishDate().getNext();
		}
		if (!gapStart.getDate().after(to.getDate())) {
			addSnag(service, AccountSnag.MISSING_BILL, gapStart, to, false);
		}
	}

	void addSnag(Service service, String description, HhEndDate startDate,
			HhEndDate finishDate, boolean isResolved)
			throws InternalException, HttpException {
		SnagDateBounded.addAccountSnag(service, this, description, startDate,
				finishDate, isResolved);
	}

	Bills billsInstance() {
		return new Bills(this);
	}

	/*
	 * @SuppressWarnings("unchecked") Invoice insertInvoice(Batch batch,
	 * InvoiceRaw invoiceRaw) throws UserException, ProgrammerException { Bill
	 * bill = combineBills(invoiceRaw.getStartDate(), invoiceRaw
	 * .getFinishDate()); Service service = batch.getService(); if (bill ==
	 * null) { checkMissingFromLatest(service, invoiceRaw.getStartDate()
	 * .getPrevious()); bill = new Bill(service, this);
	 * Hiber.session().save(bill); Hiber.flush(); } Invoice invoice = new
	 * Invoice(batch, invoiceRaw); Hiber.session().save(invoice); Hiber.flush();
	 * bill.attach(invoice); checkMissing(service, bill.getStartDate(),
	 * bill.getFinishDate()); return invoice; }
	 */
	@SuppressWarnings("unchecked")
	private List<Mpan> getMpans(HhEndDate from, HhEndDate to)
			throws HttpException, InternalException {
		String roleCode = getProvider().getRole().getCode();
		if (roleCode.equals("X")) {
			if (to == null) {
				return Hiber
						.session()
						.createQuery(
								"select distinct mpan from Mpan mpan where mpan.supplierAccount = :account and (mpan.supplyGeneration.finishDate is null or mpan.supplyGeneration.finishDate >= :from)")
						.setEntity("account", this).setTimestamp("from",
								from.getDate()).list();
			} else {
				return Hiber
						.session()
						.createQuery(
								"select distinct mpan from Mpan mpan where mpan.supplierAccount = :account and (mpan.supplyGeneration.finishDate is null or mpan.supplyGeneration.finishDate >= :from) and mpan.supplyGeneration.startDate <= :to")
						.setEntity("account", this).setTimestamp("from",
								from.getDate())
						.setTimestamp("to", to.getDate()).list();
			}
		} else if (roleCode.equals("C")) {
			return Hiber
					.session()
					.createQuery(
							"select distinct mpan from Mpan mpan where mpan.dceAccount = :account and (mpan.supplyGeneration.finishDate is null or mpan.supplyGeneration.finishDate.date >= :from) and mpan.supplyGeneration.startDate.date <= :to")
					.setEntity("account", this).setTimestamp("from",
							from.getDate()).setTimestamp("to", to.getDate())
					.list();
		} else {
			throw new UserException("Not of type Supplier!");
		}
	}

	void attach(Invoice invoice) throws HttpException, InternalException {
		Bill bill = combineBills(invoice.getStartDate(), invoice
				.getFinishDate());
		List<Mpan> accountMpans = getMpans(invoice.getStartDate(), invoice
				.getFinishDate());
		List<Mpan> invoiceMpans = new ArrayList<Mpan>();
		for (InvoiceMpan invoiceMpan : invoice.getInvoiceMpans()) {
			invoiceMpans.add(invoiceMpan.getMpan());
		}
		if (!accountMpans.equals(new ArrayList<Mpan>(invoiceMpans))) {
			throw new UserException("Problem with account '"
					+ reference + "' invoice '" + invoice.getReference()
					+ "' from the half-hour ending " + invoice.getStartDate()
					+ " to the half-hour ending " + invoice.getFinishDate()
					+ ". This bill has MPANs " + invoiceMpans
					+ " but the account in Chellow has MPANs '" + accountMpans
					+ "'.");
		}
		Service service = invoice.getBatch().getContract();
		if (bill == null) {
			bill = new Bill(service, this);
			Hiber.session().save(bill);
		}
		bill.attach(invoice);
		checkMissing(service, bill.getStartDate(), bill.getFinishDate());
	}

	@SuppressWarnings("unchecked")
	private Bill combineBills(HhEndDate start, HhEndDate finish)
			throws HttpException, InternalException {
		List<Bill> bills = (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account and bill.startDate.date <= :finishDate and bill.finishDate.date >= :startDate")
				.setEntity("account", this).setTimestamp("startDate",
						start.getDate()).setTimestamp("finishDate",
						finish.getDate()).list();
		if (bills.isEmpty()) {
			return null;
		} else {
			Bill firstBill = bills.get(0);
			for (int i = 1; i < bills.size(); i++) {
				Bill bill = bills.get(i);
				for (Invoice invoice : bill.getInvoices()) {
					firstBill.attach(invoice);
					bill.detach(invoice);
				}
				delete(bill);
			}
			Hiber.flush();
			return firstBill;
		}
	}

	void delete(Bill bill) throws InternalException, HttpException {
		Service service = bill.getService();
		Bill foundBill = (Bill) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account and bill.id = :billId")
				.setEntity("account", this).setLong("billId", bill.getId())
				.uniqueResult();
		if (foundBill == null) {
			throw new InternalException(
					"This bill doesn't belong to this account.");
		} else {
			Hiber.session().delete(bill);
		}
		checkMissing(service, foundBill.getStartDate(), foundBill
				.getFinishDate());
	}
}