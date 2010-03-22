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

import java.util.List;

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
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.Snag;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplierContract extends Contract {
	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		String participantCode = GeneralImport.addField(csvElement,
				"Participant Code", values, 0);
		Participant participant = Participant.getParticipant(participantCode);
		String name = GeneralImport.addField(csvElement, "Name", values, 1);

		if (action.equals("insert")) {
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhEndDate startDate = new HhEndDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 3);
			HhEndDate finishDate = null;
			if (finishDateStr.length() > 0) {
				finishDate = new HhEndDate(finishDateStr);
			}
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 4);
			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 5);
			insertSupplierContract(participant, name, startDate, finishDate,
					chargeScript, rateScript);
		}
	}

	static public SupplierContract insertSupplierContract(
			Participant participant, String name, HhEndDate startDate,
			HhEndDate finishDate, String chargeScript, String rateScript)
			throws HttpException {
		SupplierContract contract = new SupplierContract(participant, name,
				startDate, finishDate, chargeScript, rateScript);
		Hiber.session().save(contract);
		Hiber.flush();
		return contract;
	}

	public static SupplierContract getSupplierContract(Long id)
			throws HttpException {
		SupplierContract service = findSupplierContract(id);
		if (service == null) {
			throw new UserException(
					"There isn't a supplier service with that id.");
		}
		return service;
	}

	public static SupplierContract findSupplierContract(Long id) {
		return (SupplierContract) Hiber.session().get(SupplierContract.class,
				id);
	}

	static public SupplierContract getSupplierContract(String name)
			throws HttpException {
		SupplierContract contract = (SupplierContract) Hiber
				.session()
				.createQuery(
						"from SupplierContract contract where contract.name = :name")
				.setString("name", name).uniqueResult();
		if (contract == null) {
			throw new NotFoundException("There's no supplier contract named '"
					+ name + "'.");
		}
		return contract;
	}

	Provider supplier;

	public SupplierContract() {
	}

	public SupplierContract(Participant participant, String name,
			HhEndDate startDate, HhEndDate finishDate, String chargeScript,
			String rateScript) throws HttpException {
		super(name, startDate, finishDate, chargeScript, rateScript);
		internalUpdate(participant, name, chargeScript);
	}

	void setParty(Provider supplier) {
		this.supplier = supplier;
	}

	public Provider getParty() {
		return supplier;
	}

	public void internalUpdate(Participant participant, String name,
			String chargeScript) throws HttpException {
		setParty(Provider.getProvider(participant, MarketRole
				.getMarketRole(MarketRole.SUPPLIER)));
		super.internalUpdate(name, chargeScript);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof SupplierContract) {
			SupplierContract contract = (SupplierContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.SUPPLIER_CONTRACTS_INSTANCE.getUri().resolve(getUriId())
				.append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("test")) {
			String chargeScript = inv.getString("charge-script");
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");
			Long billId = inv.getLong("bill-id");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			try {
				Bill bill = Bill.getBill(billId);
				Document doc = document();
				Element source = doc.getDocumentElement();
				update(getName(), chargeScript);
				source.appendChild(bill.virtualBillXml(doc));
				inv.sendOk(doc);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
		} else if (inv.hasParameter("delete")) {
			try {
				delete();
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendSeeOther(Chellow.SUPPLIER_CONTRACTS_INSTANCE.getUri());
		} else {
			String chargeScript = inv.getString("charge-script");
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");

			String name = inv.getString("name");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			try {
				update(name, chargeScript);
				Hiber.commit();
				inv.sendOk(document());
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
		}
	}

	@SuppressWarnings("unchecked")
	void onUpdate(HhEndDate startDate, HhEndDate finishDate)
			throws HttpException {
		List<Mpan> mpansOutside = Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.supplierContract = :contract and mpan.supplyGeneration.startDate.date < :startDate and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate > :finishDate) order by mpan.supplyGeneration.startDate.date desc")
				.setEntity("contract", this).setTimestamp("startDate",
						getStartDate().getDate()).setTimestamp(
						"finishDate",
						getFinishDate() == null ? null : getFinishDate()
								.getDate()).list();
		if (!mpansOutside.isEmpty()) {
			throw new UserException(document(),
					mpansOutside.size() > 1 ? "The MPANs with cores "
							+ mpansOutside.get(0).getCore()
							+ " and "
							+ mpansOutside.get(mpansOutside.size() - 1)
									.getCore() + " use this contract"
							: "An MPAN with core "
									+ mpansOutside.get(0).getCore()
									+ " uses this contract and lies outside "
									+ startDate
									+ " to "
									+ (finishDate == null ? "ongoing"
											: finishDate + "."));
		}
		super.onUpdate(startDate, finishDate);
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild((Element) toXml(doc, new XmlTree("party",
				new XmlTree("participant"))));
		for (Provider provider : (List<Provider>) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.role.code = :roleCode order by provider.name")
				.setCharacter("roleCode", MarketRole.SUPPLIER).list()) {
			source.appendChild(provider.toXml(doc, new XmlTree("participant")));
		}
		source.appendChild(new MonadDate().toXml(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public int compareTo(SupplierContract arg0) {
		return 0;
	}

	public Snag getSnag(UriPathElement uriId) throws HttpException {
		Snag snag = (Snag) Hiber
				.session()
				.createQuery(
						"from Snag snag where snag.contract = :contract and snag.id = :snagId")
				.setEntity("contract", this).setLong("snagId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Batches.URI_ID.equals(uriId)) {
			return new Batches(this);
		} else if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supplier-contract");
		return element;
	}

	public String missingBillSnagDescription() {
		return "Missing supplier bill.";
	}
}
