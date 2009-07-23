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

import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.util.Date;
import java.util.List;
import java.util.Properties;

import net.sf.chellow.hhimport.AutomaticHhDataImporter;
import net.sf.chellow.hhimport.AutomaticHhDataImporters;
import net.sf.chellow.hhimport.HhDataImportProcesses;
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
import net.sf.chellow.physical.ChannelSnag;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.ScrollMode;
import org.hibernate.ScrollableResults;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhdcContract extends Contract {
	static public final String GENERAL_IMPORT_NAME = "hhdc-contract";

	static public final String FREQUENCY_DAILY = "daily";

	static public final String FREQUENCY_MONTHLY = "monthly";

	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (values.length < 8) {
			throw new UserException("There aren't enough fields in this row");
		}
		String participantCode = GeneralImport.addField(csvElement,
				"Participant Code", values, 0);
		Provider provider = Provider.getProvider(participantCode,
				MarketRole.HHDC);
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
			String properties = GeneralImport.addField(csvElement,
					"Properties", values, 5);
			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 6);
			insertHhdcContract(provider, name, startDate, finishDate,
					chargeScript, properties, rateScript);
		}
	}

	static public HhdcContract insertHhdcContract(Provider provider,
			String name, HhEndDate startDate, HhEndDate finishDate,
			String chargeScript, String importerProperties, String rateScript)
			throws HttpException {
		HhdcContract existing = findHhdcContract(name);
		if (existing != null) {
			throw new UserException(
					"There's already a HHDC contract with the name " + name);
		}
		HhdcContract contract = new HhdcContract(provider, name, startDate,
				finishDate, chargeScript, importerProperties, rateScript);
		Hiber.session().save(contract);
		Hiber.flush();
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
		return (HhdcContract) Hiber.session().createQuery(
				"from HhdcContract contract where contract.name = :name")
				.setString("name", name).uniqueResult();
	}

	private Provider hhdc;

	private String properties;

	private String state;

	public HhdcContract() {
	}

	public HhdcContract(Provider hhdc, String name, HhEndDate startDate,
			HhEndDate finishDate, String chargeScript, String properties,
			String rateScript) throws HttpException {
		super(name, startDate, finishDate, chargeScript, rateScript);
		if (hhdc.getRole().getCode() != MarketRole.HHDC) {
			throw new UserException("The provider must have the HHDC role.");
		}
		setParty(hhdc);
		setState("");
		intrinsicUpdate(name, chargeScript, properties);
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

	private void intrinsicUpdate(String name, String chargeScript,
			String properties) throws HttpException {
		super.internalUpdate(name, chargeScript);
		if (properties == null) {
			throw new InternalException("Properties can't be null.");
		}
		setProperties(properties);
	}

	public void update(String name, String chargeScript,
			String importerProperties) throws HttpException {
		intrinsicUpdate(name, chargeScript, importerProperties);
		onUpdate();
	}

	@SuppressWarnings("unchecked")
	void onUpdate() throws HttpException {
		super.onUpdate();
		for (Mpan mpan : (List<Mpan>) Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.hhdcAccount.contract = :hhdcContract and mpan.supplyGeneration.startDate.date < :startDate or (mpan.supplyGeneration.finishDate.date is not null and (:finishDate is not null or mpan.supplyGeneration.finishDate.date > :finishDate))")
				.setEntity("hhdcContract", this).setTimestamp("startDate",
						getStartDate().getDate()).setTimestamp(
						"finishDate",
						getFinishDate() == null ? null : getFinishDate()
								.getDate()).list()) {
			throw new UserException(
					"The supply '"
							+ mpan.getSupplyGeneration().getSupply().getId()
							+ "' has an MPAN with this contract that covers a time outside this contract.");
		}
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof HhdcContract) {
			HhdcContract contract = (HhdcContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.HHDC_CONTRACTS_INSTANCE.getUri().resolve(getUriId())
				.append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("update-state")) {
			String state = inv.getString("state");
			setState(state);
			Hiber.commit();
			Document doc = document();
			Element source = doc.getDocumentElement();
			source.setAttribute("state", state);
			inv.sendOk(doc);
		} else if (inv.hasParameter("ignore-snags")) {
			Date ignoreDate = inv.getDate("ignore-date");
			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from ChannelSnag snag where snag.channel.supplyGeneration.hhdcAccount.contract.id = :contractId and snag.finishDate < :ignoreDate")
					.setLong("contractId", getId()).setTimestamp("ignoreDate",
							ignoreDate).scroll(ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				ChannelSnag snag = (ChannelSnag) snags.get(0);
				snag.setIsIgnored(true);
				Hiber.session().flush();
				Hiber.session().clear();
			}
			Hiber.commit();
			inv.sendSeeOther(getUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			String properties = inv.getString("properties");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");
			properties = properties.replace("\r", "").replace("\t", "    ");
			try {
				update(name, chargeScript, properties);
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
		source.appendChild(toXml(doc, new XmlTree("party")));
		for (Party party : (List<Party>) Hiber
				.session()
				.createQuery(
						"from Party party where party.role.code = :roleCode order by party.participant.code")
				.setCharacter("roleCode", MarketRole.HHDC).list()) {
			source.appendChild(party.toXml(doc, new XmlTree("participant")));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public HhDataImportProcesses getHhDataImportProcessesInstance() {
		return new HhDataImportProcesses(this);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (HhDataImportProcesses.URI_ID.equals(uriId)) {
			return getHhDataImportProcessesInstance();
		} else if (AutomaticHhDataImporter.URI_ID.equals(uriId)) {
			return AutomaticHhDataImporters.getImportersInstance()
					.findImporter(this);
		} else if (Accounts.URI_ID.equals(uriId)) {
			return new Accounts(this);
		} else if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else {
			return null;
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "hhdc-contract");

		element.setAttribute("has-automatic-hh-data-importer",
				AutomaticHhDataImporters.getImportersInstance().findImporter(
						this) == null ? "false" : "true");
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
}
