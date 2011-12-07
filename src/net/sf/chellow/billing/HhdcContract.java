/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2011 Wessex Water Services Limited
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

import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.net.URI;
import java.util.Date;
import java.util.List;
import java.util.Properties;

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
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhdcContract extends Contract {
	static public final String GENERAL_IMPORT_NAME = "hhdc-contract";

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
			String properties = GeneralImport.addField(csvElement,
					"Properties", values, 6);
			String state = GeneralImport.addField(csvElement, "State", values,
					7);

			String rateScriptIdStr = GeneralImport.addField(csvElement,
					"Rate Script Id", values, 8);
			Long rateScriptId = rateScriptIdStr.length() > 0 ? new Long(
					rateScriptIdStr) : null;

			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 9);
			insertHhdcContract(id, participant, name, startDate, finishDate,
					chargeScript, properties, state, rateScriptId, rateScript);
		} else if (action.equals("delete")) {
			String name = GeneralImport.addField(csvElement, "Name", values, 0);
			HhdcContract contract = HhdcContract.getHhdcContract(name);
			contract.delete();
		} else if (action.equals("delete")) {
			String name = GeneralImport.addField(csvElement, "Name", values, 0);
			HhdcContract contract = HhdcContract.getHhdcContract(name);
			contract.delete();
		}
	}

	static public HhdcContract insertHhdcContract(Long id,
			Participant participant, String name, HhStartDate startDate,
			HhStartDate finishDate, String chargeScript,
			String importerProperties, String state, Long rateScriptId,
			String rateScript) throws HttpException {
		HhdcContract existing = findHhdcContract(name);
		if (existing != null) {
			throw new UserException(
					"There's already a HHDC contract with the name " + name);
		}
		HhdcContract contract = new HhdcContract(id, participant, name,
				startDate, finishDate, chargeScript, importerProperties, state);
		Hiber.session().save(contract);
		Hiber.flush();
		contract.insertFirstRateScript(rateScriptId, startDate, finishDate,
				rateScript);
		return contract;
	}

	public static HhdcContract getHhdcContract(Long id) throws HttpException {
		HhdcContract contract = findHhdcContract(id);
		if (contract == null) {
			throw new UserException("There isn't a HHDC contract with that id.");
		}
		return contract;
	}

	public static HhdcContract findHhdcContract(Long id) throws HttpException {
		return (HhdcContract) Hiber.session().get(HhdcContract.class, id);
	}

	public static HhdcContract getHhdcContract(String name)
			throws HttpException {
		HhdcContract contract = findHhdcContract(name);
		if (contract == null) {
			throw new NotFoundException("There isn't an HHDC contract called '"
					+ name + "'");
		}
		return contract;
	}

	public static HhdcContract findHhdcContract(String name)
			throws HttpException {
		return (HhdcContract) Hiber
				.session()
				.createQuery(
						"from HhdcContract contract where contract.name = :name")
				.setString("name", name).uniqueResult();
	}

	private Provider hhdc;

	private String properties;

	private String state;

	public HhdcContract() {
	}

	public HhdcContract(Long id, Participant participant, String name,
			HhStartDate startDate, HhStartDate finishDate, String chargeScript,
			String properties, String state) throws HttpException {
		super(id, Boolean.FALSE, name, startDate, finishDate, chargeScript);
		setState(state);
		intrinsicUpdate(participant, name, chargeScript, properties);
	}

	void setParty(Provider hhdc) {
		this.hhdc = hhdc;
	}

	public Provider getParty() {
		return hhdc;
	}

	public String getProperties() {
		return properties;
	}

	void setProperties(String properties) {
		this.properties = properties;
	}

	public String getState() {
		return state;
	}

	void setState(String state) {
		this.state = state;
	}

	private void intrinsicUpdate(Participant participant, String name,
			String chargeScript, String properties) throws HttpException {
		super.internalUpdate(name, chargeScript);
		setParty(Provider.getProvider(participant,
				MarketRole.getMarketRole(MarketRole.HHDC)));
		if (properties == null) {
			throw new InternalException("Properties can't be null.");
		}
		setProperties(properties);
	}

	public void update(Participant participant, String name,
			String chargeScript, String importerProperties)
			throws HttpException {
		intrinsicUpdate(participant, name, chargeScript, importerProperties);
		onUpdate(null, null);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof HhdcContract) {
			HhdcContract contract = (HhdcContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.HHDC_CONTRACTS_INSTANCE.getEditUri().resolve(getUriId())
				.append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("update-state")) {
			String state = inv.getString("state");
			state = state.replace("\r", "").replace("\t", "    ");
			setState(state);
			Hiber.commit();
			Document doc = document();
			Element source = doc.getDocumentElement();
			source.setAttribute("state", state);
			inv.sendOk(doc);
		} else if (inv.hasParameter("ignore-snags")) {
			Date ignoreDate = inv.getDate("ignore");
			Hiber.session()
					.createSQLQuery(
							"update snag set is_ignored = true from channel_snag, channel, supply_generation where snag.id = channel_snag.snag_id and channel_snag.channel_id = channel.id and channel.supply_generation_id = supply_generation.id and supply_generation.hhdc_contract_id = :contractId and supply_generation.finish_date < :ignoreDate")
					.setLong("contractId", getId())
					.setTimestamp("ignoreDate", ignoreDate).executeUpdate();
			Hiber.commit();
			inv.sendOk(document());
		} else if (inv.hasParameter("delete")) {
			try {
				delete();
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendSeeOther(Chellow.HHDC_CONTRACTS_INSTANCE.getEditUri());
		} else {
			Long participantId = inv.getLong("participant-id");
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			String properties = inv.getString("properties");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");
			properties = properties.replace("\r", "").replace("\t", "    ");
			try {
				update(Participant.getParticipant(participantId), name,
						chargeScript, properties);
			} catch (UserException e) {
				Document doc = document();
				Element source = doc.getDocumentElement();
				source.setAttribute("charge-script", chargeScript);
				source.setAttribute("properties", properties);
				e.setDocument(doc);
				throw e;
			}
			Hiber.commit();
			Document doc = document();
			Element source = doc.getDocumentElement();
			source.setAttribute("charge-script", chargeScript);
			source.setAttribute("properties", properties);
			inv.sendOk(doc);
		}
	}

	@SuppressWarnings("unchecked")
	protected Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("party", new XmlTree(
				"participant"))));
		for (Party party : (List<Party>) Hiber
				.session()
				.createQuery(
						"from Party party where party.role.code = :roleCode order by party.participant.code")
				.setCharacter("roleCode", MarketRole.HHDC).list()) {
			source.appendChild(party.toXml(doc, new XmlTree("participant")));
		}
		source.appendChild(new MonadDate().toXml(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else if (Batches.URI_ID.equals(uriId)) {
			return new Batches(this);
		} else {
			return null;
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "hhdc-contract");

		element.setAttribute("properties", properties);
		element.setAttribute("state", state);
		return element;
	}

	public void setStateProperty(String name, String value)
			throws HttpException {
		Properties properties = new Properties();
		try {
			properties.load(new StringReader(getState()));
			properties.setProperty(name, value);
			StringWriter sw = new StringWriter();
			properties.store(sw, null);
			setState(sw.toString());
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public String getStateProperty(String name) throws HttpException {
		Properties properties = new Properties();
		try {
			properties.load(new StringReader(getState()));
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return properties.getProperty(name);
	}

	public String getProperty(String name) throws HttpException {
		Properties properties = new Properties();
		try {
			properties.load(new StringReader(getProperties()));
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return properties.getProperty(name);
	}

	@Override
	public String missingBillSnagDescription() {
		return "Missing HHDC bill.";
	}

	@SuppressWarnings("unchecked")
	@Override
	void onUpdate(HhStartDate startDate, HhStartDate finishDate)
			throws HttpException {
		Query query = null;
		if (getFinishDate() == null) {
			query = Hiber
					.session()
					.createQuery(
							"from Mpan mpan where mpan.supplyGeneration.hhdcContract = :contract and mpan.supplyGeneration.startDate.date < :startDate order by mpan.supplyGeneration.startDate.date desc");
		} else {
			query = Hiber
					.session()
					.createQuery(
							"from Mpan mpan where mpan.supplyGeneration.hhdcContract = :contract and (mpan.supplyGeneration.startDate.date < :startDate or (mpan.supplyGeneration.finishDate is null or mpan.supplyGeneration.finishDate.date > :finishDate)) order by mpan.supplyGeneration.startDate.date desc")
					.setTimestamp("finishDate", getFinishDate().getDate());
		}
		List<Mpan> mpansOutside = query.setEntity("contract", this)
				.setTimestamp("startDate", getStartDate().getDate()).list();
		if (!mpansOutside.isEmpty()) {
			throw new UserException(
					document(),
					mpansOutside.size() > 1 ? "The supply generations with MPAN cores "
							+ mpansOutside.get(0).getCore()
							+ " and "
							+ mpansOutside.get(mpansOutside.size() - 1)
									.getCore() + " use this contract"
							: "A supply generation with MPAN core "
									+ mpansOutside.get(0).getCore()
									+ " uses this contract and lies outside "
									+ startDate
									+ " to "
									+ (finishDate == null ? "ongoing"
											: finishDate + "."));
		}
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}