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

package net.sf.chellow.physical;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.billing.Bill;
import net.sf.chellow.billing.Dso;
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.billing.InvoiceRaw;
import net.sf.chellow.billing.MpanSnag;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Mpan extends PersistentEntity {
	static public Mpan getMpan(Long id) throws HttpException {
		Mpan mpan = (Mpan) Hiber.session().get(Mpan.class, id);
		if (mpan == null) {
			throw new UserException("There is no mpan with that id.");
		}
		return mpan;
	}

	@SuppressWarnings("unchecked")
	static public List<Mpan> getMpans(String mpanStr, HhEndDate from,
			HhEndDate to) throws HttpException {
		MpanRaw raw = new MpanRaw(mpanStr);
		MpanCore core = MpanCore.getMpanCore(raw.getMpanCore());
		List<SupplyGeneration> supplyGenerations = core.getSupply()
				.getGenerations(from, to);
		Dso dso = core.getDso();
		return (List<Mpan>) Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.core = :core and mpan.supplyGeneration in (:supplyGenerations) and mpan.top.pc = :pc and mpan.top.mtc = :mtc and mpan.top.llfc = :llfc")
				.setEntity("pc", Pc.getPc(raw.getPcCode())).setEntity("mtc",
						Mtc.getMtc(dso, raw.getMtcCode())).setEntity("llfc",
						dso.getLlfc(raw.getLlfcCode())).setParameterList(
						"supplyGenerations", supplyGenerations).list();
	}

	static public String getCore(String mpan) throws HttpException {
		return new MpanRaw(mpan).getMpanCore();
	}

	static public Pc pc(String mpan) throws HttpException {
		return Pc.getPc(new MpanRaw(mpan).getPcCode());
	}

	static public boolean isEqual(Set<String> mpans1, Set<String> mpans2)
			throws HttpException {
		Set<MpanRaw> mpansRaw1 = new HashSet<MpanRaw>();
		for (String mpan : mpans1) {
			mpansRaw1.add(new MpanRaw(mpan));
		}
		Set<MpanRaw> mpansRaw2 = new HashSet<MpanRaw>();
		for (String mpan : mpans2) {
			mpansRaw2.add(new MpanRaw(mpan));
		}
		return mpansRaw1.equals(mpansRaw2);
	}

	private SupplyGeneration supplyGeneration;
	private Mtc mtc;

	private Llfc llfc;

	private Ssc ssc;

	private MpanCore core;

	private SupplierContract supplierContract;
	
	private String supplierAccount;

	private int agreedSupplyCapacity;

	Mpan() {
	}

	Mpan(SupplyGeneration supplyGeneration, String mpanStr, Ssc ssc,
			SupplierContract supplierContract, String supplierAccountReference,
			int agreedSupplyCapacity) throws HttpException {
		this.supplyGeneration = supplyGeneration;
		update(mpanStr, ssc, supplierContract, supplierAccountReference,
				agreedSupplyCapacity);
	}

	public SupplyGeneration getSupplyGeneration() {
		return supplyGeneration;
	}

	protected void setSupplyGeneration(SupplyGeneration supplyGeneration) {
		this.supplyGeneration = supplyGeneration;
	}

	public Mtc getMtc() {
		return mtc;
	}

	void setMtc(Mtc mtc) {
		this.mtc = mtc;
	}

	public Llfc getLlfc() {
		return llfc;
	}

	void setLlfc(Llfc llfc) {
		this.llfc = llfc;
	}

	public MpanCore getCore() {
		return core;
	}

	void setCore(MpanCore core) {
		this.core = core;
	}

	public Ssc getSsc() {
		return ssc;
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public SupplierContract getSupplierContract() {
		return supplierContract;
	}

	void setSupplierContract(SupplierContract supplierContract) {
		this.supplierContract = supplierContract;
	}

	public String getSupplierAccount() {
		return supplierAccount;
	}

	void setSupplierAccount(String supplierAccount) {
		this.supplierAccount = supplierAccount;
	}

	
	public int getAgreedSupplyCapacity() {
		return agreedSupplyCapacity;
	}

	protected void setAgreedSupplyCapacity(int agreedSupplyCapacity) {
		this.agreedSupplyCapacity = agreedSupplyCapacity;
	}

	public void update(String mpan, Ssc ssc, SupplierContract supplierContract,
			String supplierAccount, Integer agreedSupplyCapacity)
			throws HttpException {
		if (agreedSupplyCapacity == null) {
			throw new InternalException("agreedSupplyCapacity can't be null");
		}
		MpanRaw mpanRaw = new MpanRaw(mpan);
		MpanCore mpanCore = MpanCore.findMpanCore(mpanRaw.getMpanCore());
		if (mpanCore == null) {
			mpanCore = supplyGeneration.getSupply().addMpanCore(
					mpanRaw.getMpanCore());
		}
		Dso dso = mpanCore.getDso();
		Pc pc = Pc.getPc(mpanRaw.getPcCode());
		// if (!pc.equals(supplyGeneration.getPc())) {
		// throw new UserException(
		// "The Profile Class of the MPAN must match that of the supply generation.");
		// }
		setMtc(Mtc.getMtc(dso, mpanRaw.getMtcCode()));
		Llfc llfc = dso.getLlfc(mpanRaw.getLlfcCode());
		if (!mpanCore.getSupply().equals(supplyGeneration.getSupply())) {
			throw new UserException(
					"This MPAN core is already attached to another supply.");
		}
		if (!llfc.getDso().equals(mpanCore.getDso())) {
			throw new UserException(
					"The MPAN top line DSO doesn't match the MPAN core DSO.");
		}
		if (getLlfc() != null && getLlfc().getIsImport() != llfc.getIsImport()) {
			throw new UserException(
					"You can't change an import mpan into an export one, and vice versa. The existing MPAN has LLFC "
							+ getLlfc()
							+ " that has IsImport "
							+ getLlfc().getIsImport()
							+ " whereas the new MPAN has LLFC "
							+ llfc
							+ " which has IsImport " + llfc.getIsImport() + ".");
		}
		setLlfc(llfc);
		if (pc.getCode() == 0 && ssc != null) {
			throw new UserException(
					"A supply with Profile Class 00 can't have a Standard Settlement Configuration.");
		}
		if (pc.getCode() > 0 && ssc == null) {
			throw new UserException(
					"A NHH supply must have a Standard Settlement Configuration.");
		}
		setSsc(ssc);
		setCore(mpanCore);
		if (supplierAccount == null) {
			throw new UserException("An MPAN must have a supplier account.");
		}
		setSupplierAccount(supplierAccount);
		setAgreedSupplyCapacity(agreedSupplyCapacity);
	}

	public String toString() {
		return supplyGeneration.getPc().codeAsString() + " "
				+ mtc.codeAsString() + " " + llfc.codeAsString() + " " + core;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "mpan");
		element.setAttribute("agreed-supply-capacity", Integer
				.toString(agreedSupplyCapacity));
		element.setAttribute("mpan", supplyGeneration.getPc().toXml(doc)
				.getTextContent()
				+ " "
				+ mtc.toXml(doc).getTextContent()
				+ " "
				+ llfc.toXml(doc).getTextContent() + " " + core.toString());
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public void httpGet(Invocation inv) throws HttpException {
	}

	public void httpPost(Invocation inv) throws HttpException {
	}

	void delete() throws HttpException {
		if (((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from RegisterRead read where read.mpan = :mpan")
				.setEntity("mpan", this).uniqueResult()) > 0) {
			throw new UserException(
					"An MPAN can't be deleted if it still has register reads attached.");
		}
	}
	
	@SuppressWarnings("unchecked")
	public Invoice attach(Invoice invoice) {
		Bill bill = combineBills(invoice.getStartDate(), invoice
				.getFinishDate());
		if (bill == null) {
			bill = new Bill(this);
			Hiber.session().save(bill);
		}
		bill.attach(invoice);
		deleteSnag(AccountSnag.MISSING_BILL, bill.getStartDate(), bill
				.getFinishDate());
	}	
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
			Hiber.session().delete(foundBill);
		}
		addSnag(MpanSnag.MISSING_BILL, foundBill.getStartDate(), foundBill
				.getFinishDate());
		// checkMissing(foundBill.getStartDate(), foundBill.getFinishDate());
	}
	public void addSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		SnagDateBounded
				.addMpanSnag(this, description, startDate, finishDate);
	}

	
	static private class MpanRaw {
		private String pcCode;

		private String mtcCode;

		private String llfcCode;

		private String mpanCore;

		public MpanRaw(String mpan) throws HttpException {
			mpan = mpan.replace(" ", "");
			if (mpan.length() != 21) {
				throw new UserException(
						"An MPAN must contain exactly 21 digits.");
			}
			pcCode = mpan.substring(0, 2);
			mtcCode = mpan.substring(2, 5);
			llfcCode = mpan.substring(5, 8);
			mpanCore = mpan.substring(8);
		}

		public String getPcCode() {
			return pcCode;
		}

		public String getMtcCode() {
			return mtcCode;
		}

		public String getLlfcCode() {
			return llfcCode;
		}

		public String getMpanCore() {
			return mpanCore;
		}

		public String toString() {
			return pcCode + " " + mtcCode + " " + llfcCode + " " + mpanCore;
		}

		public boolean equals(Object obj) {
			return toString().equals(obj.toString());
		}

		public int hashCode() {
			return getPcCode().hashCode() + getMtcCode().hashCode()
					+ getLlfcCode().hashCode() + getMpanCore().hashCode();
		}
	}
}
