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

package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.hhimport.HhDataImportProcesses;
import net.sf.chellow.hhimport.stark.StarkAutomaticHhDataImporter;
import net.sf.chellow.hhimport.stark.StarkAutomaticHhDataImporters;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.ChannelSnags;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.SiteSnags;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class HhdcContract extends Contract {
	static public final String GENERAL_IMPORT_NAME = "hhdc-contract";
	static public final String FREQUENCY_DAILY = "daily";
	static public final String FREQUENCY_MONTHLY = "monthly";

	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (values.length < 8) {
			throw new UserException("There aren't enough fields in this row");
		}
		String participantCode = values[0];
		GeneralImport.addField(csvElement, "Participant Code", participantCode);
		Provider provider = Provider.getProvider(participantCode,
				MarketRole.HHDC);
		String name = values[1];
		GeneralImport.addField(csvElement, "Name", name);

		if (action.equals("insert")) {
			String startDateStr = values[2];
			GeneralImport.addField(csvElement, "Start Date", startDateStr);
			HhEndDate startDate = new HhEndDate(startDateStr);
			String finishDateStr = values[3];
			GeneralImport.addField(csvElement, "Finish Date", finishDateStr);
			HhEndDate finishDate = null;
			if (finishDateStr.length() > 0) {
				finishDate = new HhEndDate(finishDateStr);
			}
			String frequency = values[4];
			GeneralImport.addField(csvElement, "Frequency", frequency);
			String lagStr = values[5];
			GeneralImport.addField(csvElement, "Lag", lagStr);
			int lag = Integer.parseInt(lagStr);
			String chargeScript = values[6];
			GeneralImport.addField(csvElement, "Charge Script", chargeScript);
			String importerProperties = values[7];
			GeneralImport.addField(csvElement, "Importer Properties",
					importerProperties);
			insertHhdcContract(provider, name, startDate, finishDate,
					chargeScript, frequency, lag, importerProperties);
		}
	}

	static public HhdcContract insertHhdcContract(Provider provider,
			String name, HhEndDate startDate, HhEndDate finishDate,
			String chargeScript, String frequency, int lag,
			String importerProperties) throws HttpException {
		HhdcContract contract = new HhdcContract(provider, name, startDate,
				finishDate, chargeScript, frequency, lag, importerProperties);
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
		HhdcContract contract = (HhdcContract) Hiber.session().createQuery(
				"from HhdcContract contract where contract.name = :name")
				.setString("name", name).uniqueResult();
		if (contract == null) {
			throw new NotFoundException("There isn't an HHDC contract called '"
					+ name + "'");
		}
		return contract;
	}

	private Provider hhdc;

	private String frequency;

	private int lag;

	private String importerProperties;
	private String importerState;

	public HhdcContract() {
	}

	public HhdcContract(Provider hhdc, String name, HhEndDate startDate,
			HhEndDate finishDate, String chargeScript, String frequency,
			int lag, String importerProperties) throws HttpException {
		super(name, startDate, finishDate, chargeScript);
		if (hhdc.getRole().getCode() != MarketRole.HHDC) {
			throw new UserException("The provider must have the HHDC role.");
		}
		setParty(hhdc);
		intrinsicUpdate(name, chargeScript, frequency, lag, importerProperties);
	}

	void setParty(Provider hhdc) {
		this.hhdc = hhdc;
	}

	public Provider getParty() {
		return hhdc;
	}

	public String getFrequency() {
		return frequency;
	}

	void setFrequency(String frequency) {
		this.frequency = frequency;
	}

	public int getLag() {
		return lag;
	}

	void setLag(int lag) {
		this.lag = lag;
	}

	public String getImporterProperties() {
		return importerProperties;
	}

	void setImporterProperties(String properties) {
		this.importerProperties = properties;
	}

	public String getImporterState() {
		return importerState;
	}

	void setImporterState(String state) {
		this.importerState = state;
	}

	private void intrinsicUpdate(String name, String chargeScript,
			String frequency, int lag, String importerProperties)
			throws HttpException {
		super.internalUpdate(name, chargeScript);
		if (!(FREQUENCY_DAILY.equals(frequency) || FREQUENCY_MONTHLY
				.equals(frequency))) {
			throw new UserException("The frequency must be " + FREQUENCY_DAILY
					+ " or " + FREQUENCY_MONTHLY);
		}
		setFrequency(frequency);
		setLag(lag);
		setImporterProperties(importerProperties);
	}

	@SuppressWarnings("unchecked")
	public void update(String name, String chargeScript, String frequency,
			int lag, String importerProperties) throws HttpException {
		intrinsicUpdate(name, chargeScript, frequency, lag, importerProperties);
		updateNotification();
		// test if new dates agree with supply generation dates.

	}

	@SuppressWarnings("unchecked")
	void updateNotification() throws HttpException {
		super.updateNotification();
		for (Mpan mpan : (List<Mpan>) Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.dceService = :dceService and mpan.supplyGeneration.startDate >= :startDate and (mpan.supplyGeneration.finishDate.date <= :finishDate or (mpan.supplyGeneration.finishDate.date is null and :finishDate is null))")
				.setEntity("dceService", this).setTimestamp("startDate",
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
		if (inv.hasParameter("update-importer-state")) {
			String state = inv.getString("importer-state");
			setImporterState(state);
			Hiber.commit();
			inv.sendOk(document());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			String frequency = inv.getString("frequency");
			int lag = inv.getInteger("lag");
			String importerProperties = inv.getString("importer-properties");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(name, chargeScript, frequency, lag, importerProperties);
			Hiber.commit();
			inv.sendOk(document());
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
		} else if (ChannelSnags.URI_ID.equals(uriId)) {
			return getChannelSnagsInstance();
		} else if (SiteSnags.URI_ID.equals(uriId)) {
			return getSiteSnagsInstance();
		} else if (StarkAutomaticHhDataImporter.URI_ID.equals(uriId)) {
			return StarkAutomaticHhDataImporters.getImportersInstance()
					.findImporter(this);
		} else if (Accounts.URI_ID.equals(uriId)) {
			return new Accounts(this);
		} else {
			return null;
		}
	}

	public ChannelSnags getChannelSnagsInstance() {
		return new ChannelSnags(this);
	}

	public SiteSnags getSiteSnagsInstance() {
		return new SiteSnags(this);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "hhdc-contract");

		element.setAttribute("frequency", frequency);
		element.setAttribute("lag", Integer.toString(lag));
		element.setAttribute("has-stark-automatic-hh-data-importer",
				StarkAutomaticHhDataImporters.getImportersInstance()
						.findImporter(this) == null ? "false" : "true");
		return element;
	}
}