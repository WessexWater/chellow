/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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

package net.sf.chellow.physical;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.Dso;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
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

	/*
	 * static public String canonicalize(String mpanStr) throws HttpException {
	 * return new MpanRaw(mpanStr).toString(); }
	 */
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

	private Pc pc;

	private Mtc mtc;

	private Llfc llfc;

	private Ssc ssc;

	private GspGroup gspGroup;

	private MpanCore core;

	private Account hhdcAccount;

	private Account supplierAccount;

	private Account mopAccount;

	private boolean hasImportKwh;

	private boolean hasImportKvarh;

	private boolean hasExportKwh;

	private boolean hasExportKvarh;

	private int agreedSupplyCapacity;

	Mpan() {
	}

	Mpan(SupplyGeneration supplyGeneration, String mpanStr, Ssc ssc,
			GspGroup gspGroup, Account hhdcAccount, Account supplierAccount,
			boolean hasImportKwh, boolean hasImportKvarh, boolean hasExportKwh,
			boolean hasExportKvarh, int agreedSupplyCapacity)
			throws HttpException {
		this.supplyGeneration = supplyGeneration;
		update(mpanStr, ssc, gspGroup, hhdcAccount, supplierAccount,
				hasImportKwh, hasImportKvarh, hasExportKwh, hasExportKvarh,
				agreedSupplyCapacity);
	}

	public SupplyGeneration getSupplyGeneration() {
		return supplyGeneration;
	}

	protected void setSupplyGeneration(SupplyGeneration supplyGeneration) {
		this.supplyGeneration = supplyGeneration;
	}

	public Pc getPc() {
		return pc;
	}

	void setPc(Pc pc) {
		this.pc = pc;
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

	public GspGroup getGspGroup() {
		return gspGroup;
	}

	void setGspGroup(GspGroup gspGroup) {
		this.gspGroup = gspGroup;
	}

	public Account getMopAccount() {
		return mopAccount;
	}

	void setMopAccount(Account mopAccount) {
		this.mopAccount = mopAccount;
	}

	public Account getHhdcAccount() {
		return hhdcAccount;
	}

	void setHhdcAccount(Account hhdcAccount) {
		this.hhdcAccount = hhdcAccount;
	}

	public Account getSupplierAccount() {
		return supplierAccount;
	}

	void setSupplierAccount(Account supplierAccount) {
		this.supplierAccount = supplierAccount;
	}

	public boolean getHasImportKwh() {
		return hasImportKwh;
	}

	protected void setHasImportKwh(boolean hasImportKwh) {
		this.hasImportKwh = hasImportKwh;
	}

	public boolean getHasImportKvarh() {
		return hasImportKvarh;
	}

	protected void setHasImportKvarh(boolean hasImportKvarh) {
		this.hasImportKvarh = hasImportKvarh;
	}

	public boolean getHasExportKwh() {
		return hasExportKwh;
	}

	protected void setHasExportKwh(boolean hasExportKwh) {
		this.hasExportKwh = hasExportKwh;
	}

	public boolean getHasExportKvarh() {
		return hasExportKvarh;
	}

	protected void setHasExportKvarh(boolean hasExportKvarh) {
		this.hasExportKvarh = hasExportKvarh;
	}

	public int getAgreedSupplyCapacity() {
		return agreedSupplyCapacity;
	}

	protected void setAgreedSupplyCapacity(int agreedSupplyCapacity) {
		this.agreedSupplyCapacity = agreedSupplyCapacity;
	}

	public boolean hasChannel(boolean isImport, boolean isKwh) {
		if (isImport) {
			if (isKwh) {
				return hasImportKwh;
			} else {
				return hasImportKvarh;
			}
		} else {
			if (isKwh) {
				return hasExportKwh;
			} else {
				return hasExportKvarh;
			}
		}
	}

	public void update(String mpan, Ssc ssc, GspGroup gspGroup,
			Account hhdcAccount, Account supplierAccount, boolean hasImportKwh,
			boolean hasImportKvarh, boolean hasExportKwh,
			boolean hasExportKvarh, int agreedSupplyCapacity)
			throws HttpException {
		Debug.print("starting to update mpan");
		MpanRaw mpanRaw = new MpanRaw(mpan);
		MpanCore mpanCore = MpanCore.findMpanCore(mpanRaw.getMpanCore());
		if (mpanCore == null) {
			mpanCore = supplyGeneration.getSupply().addMpanCore(
					mpanRaw.getMpanCore());
		}
		Dso dso = mpanCore.getDso();
		Pc pc = Pc.getPc(mpanRaw.getPcCode());
		Llfc llfc = dso.getLlfc(mpanRaw.getLlfcCode());
		Mtc mtc = Mtc.getMtc(dso, mpanRaw.getMtcCode());
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
		setPc(pc);
		setMtc(mtc);
		setLlfc(llfc);
		setSsc(ssc);
		setGspGroup(gspGroup);
		setCore(mpanCore);
		if (hhdcAccount == null
				&& (hasImportKwh == true || hasImportKvarh == true
						|| hasExportKwh == true || hasExportKvarh == true)) {
			throw new UserException(
					"If an MPAN doesn't have an HHDC account, then it can't collect data on any channels.");
		}
		if (hhdcAccount != null
				&& (!hasImportKwh && !hasImportKvarh && !hasExportKwh && !hasExportKvarh)) {
			throw new UserException(
					"If there's a HHDC account, surely there must be some data to collect?");
		}
		setHhdcAccount(hhdcAccount);
		if (supplierAccount == null) {
			throw new UserException("An MPAN must have a supplier account.");
		}
		setSupplierAccount(supplierAccount);
		setHasImportKwh(hasImportKwh);
		setHasImportKvarh(hasImportKvarh);
		setHasExportKwh(hasExportKwh);
		setHasExportKvarh(hasExportKvarh);
		setAgreedSupplyCapacity(agreedSupplyCapacity);
		Debug.print("calling onmpanchange 66");
		supplyGeneration.onMpanChange();
	}

	public String toString() {
		return pc.codeAsString() + " " + mtc.codeAsString() + " "
				+ llfc.codeAsString() + " " + core;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "mpan");
		element.setAttribute("has-import-kwh", Boolean.toString(hasImportKwh));
		element.setAttribute("has-import-kvarh", Boolean
				.toString(hasImportKvarh));
		element.setAttribute("has-export-kwh", Boolean.toString(hasExportKwh));
		element.setAttribute("has-export-kvarh", Boolean
				.toString(hasExportKvarh));
		element.setAttribute("agreed-supply-capacity", Integer
				.toString(agreedSupplyCapacity));
		element.setAttribute("mpan", pc.toXml(doc).getTextContent() + " "
				+ mtc.toXml(doc).getTextContent() + " "
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
		// check no invoices
		if (((Long) Hiber.session().createQuery(
				"from InvoiceMpan invoiceMpan where invoiceMpan.mpan = :mpan")
				.setEntity("mpan", this).uniqueResult()) > 0) {
			throw new UserException(
					"An MPAN can't be deleted if still has invoices attached.");
		}
	}

	/*
	 * public Account getHhdcAccount(boolean isImport, boolean isKwh) throws
	 * HttpException { Account account = null; if (isImport) { if (isKwh) { if
	 * (hasImportKwh) { account = hhdcAccount; } } else { if (hasImportKvarh) {
	 * account = hhdcAccount; } } } else { if (isKwh) { if (hasExportKwh) {
	 * account = hhdcAccount; } } else { if (hasExportKvarh) { account =
	 * hhdcAccount; } } } return account; }
	 */
	/*
	 * public MpanRaw getMpanRaw() throws HttpException { return new
	 * MpanRaw(Integer.toString(getMpanTop().getPc().getCode()),
	 * Integer.toString(getMpanTop().getMtc().getCode()), Integer
	 * .toString(getMpanTop().getLlfc().getCode()), getMpanCore().getCore()); }
	 */
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

		public String toStringNoSpaces() {
			return toString().replace(" ", "");
		}

		/*
		 * public boolean equals(Object obj) { boolean isEqual = false; if (obj
		 * instanceof MpanRaw) { MpanRaw mpan = (MpanRaw) obj; isEqual =
		 * getPc().equals(mpan.getPc()) && getMtc().equals(mpan.getMtc()) &&
		 * getLlfc().equals(mpan.getLlfc()) &&
		 * getMpanCore().equals(mpan.getMpanCore()); } return isEqual; }
		 */
		public boolean equals(Object obj) {
			return toString().equals(obj.toString());
		}

		public int hashCode() {
			return getPcCode().hashCode() + getMtcCode().hashCode()
					+ getLlfcCode().hashCode() + getMpanCore().hashCode();
		}
	}
}