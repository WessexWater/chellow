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

import java.util.Calendar;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.SnagDateBounded;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Account extends PersistentEntity {
	public static void generalImportHhdc(String action, String[] values,
			Element csvElement) throws HttpException {
		String hhdcContractName = GeneralImport.addField(csvElement,
				"Contract", values, 0);
		HhdcContract hhdcContract = HhdcContract
				.getHhdcContract(hhdcContractName);
		String hhdcAccountReference = GeneralImport.addField(csvElement,
				"Reference", values, 1);
		if (action.equals("insert")) {
			hhdcContract.insertAccount(hhdcAccountReference);
		} else {
			Account hhdcAccount = hhdcContract.getAccount(hhdcAccountReference);
			if (action.equals("delete")) {
				hhdcContract.deleteAccount(hhdcAccount);
			} else if (action.equals("update")) {
				String newReference = GeneralImport.addField(csvElement,
						"New Reference", values, 2);
				hhdcAccount.update(newReference);
			}
		}
	}

	public static void generalImportSupplier(String action, String[] values,
			Element csvElement) throws HttpException {
		if (values.length < 2) {
			throw new UserException("There aren't enough fields in this row");
		}
		String supplierContractName = GeneralImport.addField(csvElement,
				"Contract", values, 0);
		SupplierContract supplierContract = SupplierContract
				.getSupplierContract(supplierContractName);
		String supplierAccountReference = GeneralImport.addField(csvElement,
				"Reference", values, 1);
		if (action.equals("insert")) {
			supplierContract.insertAccount(supplierAccountReference);
		} else {
			Account supplierAccount = supplierContract
					.getAccount(supplierAccountReference);
			if (action.equals("delete")) {
				supplierContract.deleteAccount(supplierAccount);
			} else if (action.equals("update")) {
				String newReference = GeneralImport.addField(csvElement,
						"New Reference", values, 2);
				supplierAccount.update(newReference);
			}
		}
	}

	public static Account getAccount(Long id) throws HttpException,
			InternalException {
		Account account = findAccount(id);
		if (account == null) {
			throw new UserException("There isn't an account with that id.");
		}
		return account;
	}

	public static Account findAccount(Long id) throws HttpException {
		return (Account) Hiber.session().get(Account.class, id);
	}

	@SuppressWarnings("unchecked")
	public static void checkAllMissingFromLatest() throws HttpException {
		for (Account account : (List<Account>) Hiber
				.session()
				.createQuery(
						"select distinct mpan.supplierAccount from Mpan mpan where mpan.supplyGeneration.finishDate.date is null")
				.list()) {
			account.checkMissingFromLatest();
		}
	}

	private Contract contract;

	private String reference;

	public Account() {
	}

	public Account(Contract contract, String reference) {
		setContract(contract);
		update(reference);
	}

	public Contract getContract() {
		return contract;
	}

	public void setContract(Contract contract) {
		this.contract = contract;
	}

	public String getReference() {
		return reference;
	}

	public void setReference(String reference) {
		this.reference = reference;
	}

	public void update(String reference) {
		setReference(reference);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "account");

		element.setAttribute("reference", reference);
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			try {
				contract.deleteAccount(this);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendSeeOther(contract.accountsInstance().getUri());
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
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element accountElement = (Element) toXml(doc, new XmlTree("contract",
				new XmlTree("party")));
		source.appendChild(accountElement);
		for (Mpan mpan : (List<Mpan>) Hiber.session().createQuery(
				"from Mpan mpan where mpan.supplierAccount = :account")
				.setEntity("account", this).list()) {
			accountElement.appendChild(mpan.toXml(doc, new XmlTree(
					"supplyGeneration", new XmlTree("supply")).put("pc").put(
					"mtc").put("llfc").put("core")));
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
		return contract.accountsInstance().getUri().resolve(getUriId()).append(
				"/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Bills.URI_ID.equals(uriId)) {
			return billsInstance();
		} else {
			throw new NotFoundException();
		}
	}

	public void checkMissingFromLatest() throws HttpException {
		checkMissingFromLatest(null);
	}

	@SuppressWarnings("unchecked")
	public void checkMissingFromLatest(HhEndDate to) throws HttpException {
		List<Bill> bills = (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.account = :account order by bill.finishDate.date desc")
				.setEntity("account", this).list();
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
		checkMissing(from, to);
	}

	@SuppressWarnings("unchecked")
	void checkMissing(HhEndDate from, HhEndDate to) throws HttpException {
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
			int profileClass = supplyGenerations.get(0).getMpans().iterator()
					.next().getPc().getCode();
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
						"from Bill bill where bill.account = :account and bill.startDate.date <= :to and bill.finishDate.date >= :from order by bill.finishDate.date")
				.setEntity("account", this).setTimestamp("to", to.getDate())
				.setTimestamp("from", from.getDate()).list();
		HhEndDate gapStart = from;
		for (int i = 0; i < bills.size(); i++) {
			Bill bill = bills.get(i);
			if (bill.getStartDate().getDate().after(gapStart.getDate())) {
				addSnag(AccountSnag.MISSING_BILL, gapStart, bill.getStartDate()
						.getPrevious());
			}
			deleteSnag(AccountSnag.MISSING_BILL, bill.getStartDate(), bill
					.getFinishDate());
			gapStart = bill.getFinishDate().getNext();
		}
		if (!gapStart.getDate().after(to.getDate())) {
			addSnag(AccountSnag.MISSING_BILL, gapStart, to);
		}
	}

	void deleteSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		SnagDateBounded.deleteAccountSnag(this, description, startDate,
				finishDate);
	}

	void addSnag(String description, HhEndDate startDate, HhEndDate finishDate)
			throws HttpException {
		SnagDateBounded
				.addAccountSnag(this, description, startDate, finishDate);
	}

	Bills billsInstance() {
		return new Bills(this);
	}

	@SuppressWarnings("unchecked")
	public List<Mpan> getMpans(HhEndDate from, HhEndDate to)
			throws HttpException {
		Party party = contract.getParty();
		MarketRole role = party.getRole();
		char roleCode = role.getCode();
		if (roleCode == MarketRole.SUPPLIER) {
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
		} else if (roleCode == MarketRole.HHDC) {
			return Hiber
					.session()
					.createQuery(
							"select distinct mpan from Mpan mpan where mpan.hhdceAccount = :account and (mpan.supplyGeneration.finishDate is null or mpan.supplyGeneration.finishDate.date >= :from) and mpan.supplyGeneration.startDate.date <= :to")
					.setEntity("account", this).setTimestamp("from",
							from.getDate()).setTimestamp("to", to.getDate())
					.list();
		} else {
			throw new InternalException("Unknown market role type.");
		}
	}

	void attach(Invoice invoice) throws HttpException {
		Bill bill = combineBills(invoice.getStartDate(), invoice
				.getFinishDate());
		/*
		 * List<Mpan> accountMpans = getMpans(invoice.getStartDate(), invoice
		 * .getFinishDate()); List<Mpan> invoiceMpans = new ArrayList<Mpan>();
		 * 
		 * for (InvoiceMpan invoiceMpan : invoice.getInvoiceMpans()) {
		 * invoiceMpans.add(invoiceMpan.getMpan()); } if
		 * (!accountMpans.equals(new ArrayList<Mpan>(invoiceMpans))) { throw new
		 * UserException("Problem with account '" + reference + "' invoice '" +
		 * invoice.getReference() + "' from the half-hour ending " +
		 * invoice.getStartDate() + " to the half-hour ending " +
		 * invoice.getFinishDate() + ". This bill has MPANs " + invoiceMpans + "
		 * but the account in Chellow has MPANs '" + accountMpans + "'."); }
		 */
		if (bill == null) {
			bill = new Bill(this);
			Hiber.session().save(bill);
		}
		bill.attach(invoice);
		checkMissing(bill.getStartDate(), bill.getFinishDate());
	}

	@SuppressWarnings("unchecked")
	private Bill combineBills(HhEndDate start, HhEndDate finish)
			throws HttpException {
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

	void delete(Bill bill) throws HttpException {
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
		checkMissing(foundBill.getStartDate(), foundBill.getFinishDate());
	}
}
