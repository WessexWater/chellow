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
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.util.List;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
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
import net.sf.chellow.physical.Participant;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.NonUniqueResultException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class NonCoreContract extends Contract {
	public static NonCoreContract getNonCoreContract(String name)
			throws HttpException {
		NonCoreContract contract = findNonCoreContract(name);
		if (contract == null) {
			throw new NotFoundException(
					"There isn't a non core contract called '" + name + "'");
		}
		return contract;
	}

	public static NonCoreContract findNonCoreContract(String name)
			throws HttpException {
		try {
			return (NonCoreContract) Hiber
					.session()
					.createQuery(
							"from NonCoreContract contract where contract.name = :name")
					.setString("name", name).uniqueResult();
		} catch (NonUniqueResultException e) {
			throw new InternalException(
					"There is more than 1 non-core contract with name " + name
							+ ".");
		}
	}

	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String idStr = GeneralImport.addField(csvElement, "Id", values, 0);
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			String isCoreStr = GeneralImport.addField(csvElement, "Is Core?",
					values, 1);
			Boolean isCore = null;
			if (id == null) {
				isCore = new Boolean(isCoreStr);
			}
			String participantCode = GeneralImport.addField(csvElement,
					"Participant Code", values, 2);
			Participant participant = Participant
					.getParticipant(participantCode);
			String name = GeneralImport.addField(csvElement, "Name", values, 3);
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 4);
			String rateScriptIdStr = GeneralImport.addField(csvElement,
					"Rate Script Id", values, 5);
			Long rateScriptId = rateScriptIdStr.length() > 0 ? new Long(
					rateScriptIdStr) : null;
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 6);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 7);
			HhStartDate finishDate = finishDateStr.trim().length() == 0 ? null
					: new HhStartDate(finishDateStr);
			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 8);
			NonCoreContract.insertNonCoreContract(id, isCore, participant,
					name, startDate, finishDate, chargeScript, rateScriptId,
					rateScript);
		} else if (action.equals("update")) {
			/*
			 * String script = values[3];
			 * csvElement.appendChild(getField("Script", script)); String
			 * template = values[4]; csvElement.appendChild(getField("Template",
			 * template)); Report report = Report.getReport(name);
			 */
		}
	}

	public static void loadNonCoreContracts(ServletContext context)
			throws HttpException {
		try {
			GeneralImport process = new GeneralImport(null, context
					.getResource("/WEB-INF/non-core-contracts.xml")
					.openStream(), "xml");
			process.run();
			List<MonadMessage> errors = process.getErrors();
			if (!errors.isEmpty()) {
				throw new InternalException(errors.get(0).getDescription());
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	static public NonCoreContract insertNonCoreContract(Long id,
			Boolean isCore, Participant participant, String name,
			HhStartDate startDate, HhStartDate finishDate, String chargeScript,
			Long rateScriptId, String rateScript) throws HttpException {
		NonCoreContract contract = new NonCoreContract(id, isCore, participant,
				name, startDate, finishDate, chargeScript);
		Hiber.session().save(contract);
		Hiber.session().flush();
		contract.insertFirstRateScript(rateScriptId, startDate, finishDate,
				rateScript);
		return contract;
	}

	private Provider nonCore;

	public NonCoreContract() {
	}

	public NonCoreContract(Long id, Boolean isCore, Participant participant,
			String name, HhStartDate startDate, HhStartDate finishDate,
			String chargeScript) throws HttpException {
		super(id, isCore, name, startDate, finishDate, chargeScript);
		setParty(Provider.getProvider(participant,
				MarketRole.getMarketRole(MarketRole.NON_CORE_ROLE)));
		internalUpdate(name, chargeScript);
	}

	void setParty(Provider nonCore) {
		this.nonCore = nonCore;
	}

	public Provider getParty() {
		return nonCore;
	}

	public void update(String name, String chargeScript) throws HttpException {
		super.update(name, chargeScript);
		Hiber.flush();
	}

	protected void internalUpdate(Provider provider, String name,
			String chargeScript) throws HttpException {
		if (provider.getRole().getCode() != MarketRole.NON_CORE_ROLE) {
			throw new InternalException(
					"The provider must be of type Z for a non-core service.");
		}
		super.internalUpdate(name, chargeScript);
		setParty(provider);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof NonCoreContract) {
			NonCoreContract contract = (NonCoreContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.NON_CORE_SERVICES_INSTANCE.getEditUri().resolve(getUriId())
				.append("/");
	}

	public void delete() throws HttpException {
		super.delete();
		Hiber.session().delete(this);
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendSeeOther(Chellow.NON_CORE_SERVICES_INSTANCE.getEditUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");
			try {
				update(name, chargeScript);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("party", new XmlTree(
				"participant"))));
		for (Provider provider : (List<Provider>) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.role.code = :roleCode order by provider.name")
				.setCharacter("roleCode", MarketRole.NON_CORE_ROLE).list()) {
			source.appendChild(provider.toXml(doc, new XmlTree("participant")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	/*
	 * public HhDataImportProcesses getHhDataImportProcessesInstance() { return
	 * new HhDataImportProcesses(this); }
	 */
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "non-core-contract");
		return element;
	}

	@Override
	public String missingBillSnagDescription() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	void onUpdate(HhStartDate from, HhStartDate to) throws HttpException {
		// TODO Auto-generated method stub

	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
