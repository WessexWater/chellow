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
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.Snag;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplierContract extends Contract {
	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String idStr = GeneralImport.addField(csvElement, "Id", values, 0);
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			String participantCode = GeneralImport.addField(csvElement,
					"Participant Code", values, 1);
			Participant participant = Participant
					.getParticipant(participantCode);
			String name = GeneralImport.addField(csvElement, "Name", values, 2);

			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 3);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 4);
			HhStartDate finishDate = null;
			if (finishDateStr.length() > 0) {
				finishDate = new HhStartDate(finishDateStr);
			}
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 5);

			String rateScriptIdStr = GeneralImport.addField(csvElement,
					"Rate Script Id", values, 6);
			Long rateScriptId = rateScriptIdStr.length() > 0 ? new Long(
					rateScriptIdStr) : null;

			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 7);

			insertSupplierContract(id, participant, name, startDate,
					finishDate, chargeScript, rateScriptId, rateScript);
		}
	}

	static public SupplierContract insertSupplierContract(Long id,
			Participant participant, String name, HhStartDate startDate,
			HhStartDate finishDate, String chargeScript, Long rateScriptId,
			String rateScript) throws HttpException {
		SupplierContract contract = new SupplierContract(id, participant, name,
				startDate, finishDate, chargeScript);
		Hiber.session().save(contract);
		Hiber.flush();
		contract.insertFirstRateScript(rateScriptId, startDate, finishDate,
				rateScript);
		return contract;
	}

	public static SupplierContract getSupplierContract(Long id)
			throws HttpException {
		SupplierContract contract = findSupplierContract(id);
		if (contract == null) {
			throw new UserException(
					"There isn't a supplier contract with that id.");
		}
		return contract;
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

	public SupplierContract(Long id, Participant participant, String name,
			HhStartDate startDate, HhStartDate finishDate, String chargeScript)
			throws HttpException {
		super(id, Boolean.FALSE, name, startDate, finishDate, chargeScript);
		internalUpdate(participant, name, chargeScript);
	}

	void setParty(Provider supplier) {
		this.supplier = supplier;
	}

	public Provider getParty() {
		return supplier;
	}

	public void update(Participant participant, String name, String chargeScript)
			throws HttpException {
		internalUpdate(participant, name, chargeScript);
		onUpdate(null, null);
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
		if (inv.hasParameter("delete")) {
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
			String name = inv.getString("name");
			Long participantId = inv.getLong("participant-id");

			if (!inv.isValid()) {
				throw new UserException(document());
			}
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");

			try {
				update(Participant.getParticipant(participantId), name,
						chargeScript);
				Hiber.commit();
				inv.sendOk(document());
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
		}
	}

	@SuppressWarnings("unchecked")
	void onUpdate(HhStartDate startDate, HhStartDate finishDate)
			throws HttpException {
		// Debug.print("Checking on update from " + startDate + " to " +
		// finishDate);
		Query query = null;
		if (getFinishDate() == null) {
			query = Hiber
					.session()
					.createQuery(
							"from Mpan mpan where mpan.supplierContract = :contract and mpan.supplyGeneration.startDate.date < :startDate order by mpan.supplyGeneration.startDate.date desc");
		} else {
			query = Hiber
					.session()
					.createQuery(
							"from Mpan mpan where mpan.supplierContract = :contract and (mpan.supplyGeneration.startDate.date < :startDate or (mpan.supplyGeneration.finishDate is null or mpan.supplyGeneration.finishDate.date > :finishDate)) order by mpan.supplyGeneration.startDate.date desc")
					.setTimestamp("finishDate", getFinishDate().getDate());
		}
		List<Mpan> mpansOutside = query.setEntity("contract", this)
				.setTimestamp("startDate", getStartDate().getDate()).list();
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
									+ (getFinishDate() == null ? "ongoing"
											: getFinishDate() + "."));
		}
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
