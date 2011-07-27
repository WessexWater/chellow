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

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import net.sf.chellow.billing.Dno;
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
	static public List<Mpan> getMpans(String mpanStr, HhStartDate from,
			HhStartDate to) throws HttpException {
		MpanRaw raw = new MpanRaw(mpanStr);
		MpanCore core = MpanCore.getMpanCore(raw.getCore());
		List<SupplyGeneration> supplyGenerations = core.getSupply()
				.getGenerations(from, to);
		Dno dno = core.getDno();
		return (List<Mpan>) Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.core = :core and mpan.supplyGeneration in (:supplyGenerations) and mpan.supplyGeneration.pc = :pc and mpan.mtc = :mtc and mpan.llfc = :llfc")
				.setEntity("core", core).setEntity("pc",
						Pc.getPc(raw.getPcCode())).setEntity("mtc",
						Mtc.getMtc(dno, raw.getMtcCode())).setEntity("llfc",
						dno.getLlfc(raw.getLlfcCode())).setParameterList(
						"supplyGenerations", supplyGenerations).list();
	}

	static public String getCore(String mpan) throws HttpException {
		return new MpanRaw(mpan).getCore();
	}

	static public Pc pc(String mpan) throws HttpException {
		return Pc.getPc(new MpanRaw(mpan).getPcCode());
	}
	
	static public Dno dno(String mpan) throws HttpException {
		String core = getCore(mpan);
		String dnoCode = core.substring(0, 2);
		return Dno.getDno(dnoCode);
	}
	
	static public Mtc mtc(String mpan) throws HttpException {
		Dno dno = dno(mpan);
		return Mtc.getMtc(dno, new MpanRaw(mpan).getMtcCode());
	}


	static public boolean haveEqualCores(List<String> mpans1,
			List<String> mpans2) throws HttpException {
		Collections.sort(mpans1);
		List<String> cores1 = new ArrayList<String>();
		for (String mpan : mpans1) {
			cores1.add(new MpanRaw(mpan).getCore());
		}

		Collections.sort(mpans2);
		List<String> cores2 = new ArrayList<String>();
		for (String mpan : mpans2) {
			cores2.add(new MpanRaw(mpan).getCore());
		}
		return cores1.equals(cores2);
	}

	static public boolean isEqual(List<String> mpans1, List<String> mpans2)
			throws HttpException {
		List<MpanRaw> mpansRaw1 = new ArrayList<MpanRaw>();
		Collections.sort(mpans1);
		for (String mpan : mpans1) {
			mpansRaw1.add(new MpanRaw(mpan));
		}
		List<MpanRaw> mpansRaw2 = new ArrayList<MpanRaw>();
		Collections.sort(mpans2);
		for (String mpan : mpans2) {
			mpansRaw2.add(new MpanRaw(mpan));
		}
		return mpansRaw1.equals(mpansRaw2);
	}

	private SupplyGeneration supplyGeneration;

	private Llfc llfc;

	private MpanCore core;

	private SupplierContract supplierContract;

	private String supplierAccount;

	private int agreedSupplyCapacity;

	Mpan() {
	}

	Mpan(SupplyGeneration supplyGeneration, String llfcCode, String core,
			SupplierContract supplierContract, String supplierAccount,
			int agreedSupplyCapacity) throws HttpException {
		this.supplyGeneration = supplyGeneration;
		update(llfcCode, core, supplierContract, supplierAccount,
				agreedSupplyCapacity);
	}

	public SupplyGeneration getSupplyGeneration() {
		return supplyGeneration;
	}

	protected void setSupplyGeneration(SupplyGeneration supplyGeneration) {
		this.supplyGeneration = supplyGeneration;
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

	public void update(String llfcCode, String core, SupplierContract supplierContract,
			String supplierAccount, Integer agreedSupplyCapacity)
			throws HttpException {
		if (agreedSupplyCapacity == null) {
			throw new InternalException("agreedSupplyCapacity can't be null");
		}
		MpanCore mpanCore = MpanCore.findMpanCore(core);
		if (mpanCore == null) {
			mpanCore = supplyGeneration.getSupply().addMpanCore(core);
		}
		Dno dno = mpanCore.getDno();
		Llfc llfc = dno.getLlfc(llfcCode);

		if (!mpanCore.getSupply().equals(supplyGeneration.getSupply())) {
			throw new UserException(
					"This MPAN core is already attached to another supply.");
		}
		if (!llfc.getDno().equals(dno)) {
			throw new UserException(
					"The MPAN top line DNO doesn't match the MPAN core DNO.");
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

		setCore(mpanCore);
		if (supplierContract == null) {
			throw new UserException("An MPAN must have a supplier contract.");
		}
		setSupplierContract(supplierContract);
		if (supplierAccount == null) {
			throw new UserException("An MPAN must have a supplier account.");
		}
		setSupplierAccount(supplierAccount);
		setAgreedSupplyCapacity(agreedSupplyCapacity);
	}

	public String toString() {
		return supplyGeneration.getPc() + " "
				+ supplyGeneration.getMtc() + " " + llfc + " " + core;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "mpan");
		element.setAttribute("agreed-supply-capacity", Integer
				.toString(agreedSupplyCapacity));
		element.setAttribute("mpan", supplyGeneration.getPc().toXml(doc)
				.getTextContent()
				+ " "
				+ supplyGeneration.getMtc().toXml(doc).getTextContent()
				+ " "
				+ llfc.toXml(doc).getTextContent() + " " + core.toString());
		element.setAttribute("supplier-account", supplierAccount);
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

		public String getCore() {
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
					+ getLlfcCode().hashCode() + getCore().hashCode();
		}
	}
}
