/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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

import java.net.URI;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.Snag;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.Query;
import org.hibernate.exception.ConstraintViolationException;
import org.python.core.Py;
import org.python.core.PyObject;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Contract extends PersistentEntity implements Comparable<Contract> {
	public static Contract getNonCoreContract(String name) throws HttpException {
		return getContract("Z", name);
	}

	public static Contract getDnoContract(String name) throws HttpException {
		return getContract("R", name);
	}

	public static Contract getSupplierContract(String name)
			throws HttpException {
		return getContract("X", name);
	}

	public static Contract getHhdcContract(String name) throws HttpException {
		return getContract("C", name);
	}

	public static Contract getMopContract(String name) throws HttpException {
		return getContract("M", name);
	}

	public static Contract getHhdcContract(Long id) throws HttpException {
		return getContract("C", id);
	}

	public static Contract getSupplierContract(Long id) throws HttpException {
		return getContract("X", id);
	}

	public static Contract getMopContract(Long id) throws HttpException {
		return getContract("M", id);
	}

	public static Contract getDnoContract(Long id) throws HttpException {
		return getContract("R", id);
	}

	public static Contract getContract(String marketRoleCode, Long id)
			throws HttpException {
		Contract contract = (Contract) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.market_role.code = :market_role_code and contract.id = :id")
				.setString("marketRoleCode", marketRoleCode).setLong("id", id)
				.uniqueResult();
		if (contract == null) {
			throw new UserException("There isn't a contract with id " + id
					+ " and market role code " + marketRoleCode);
		}
		return contract;
	}

	public static Contract getContract(String marketRoleCode, String name)
			throws HttpException {
		Contract contract = (Contract) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = :roleCode and contract.name = :name")
				.setString("name", name).setString("roleCode", marketRoleCode)
				.uniqueResult();
		if (contract == null) {
			throw new UserException("There isn't a contract with name " + name
					+ " and market role code " + marketRoleCode);
		}
		return contract;
	}

	public static void generalImportNonCore(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String isCoreStr = GeneralImport.addField(csvElement, "Is Core?",
					values, 0);
			boolean isCore = new Boolean(isCoreStr);
			String participantCode = GeneralImport.addField(csvElement,
					"Participant Code", values, 1);
			Participant participant = Participant
					.getParticipant(participantCode);
			String name = GeneralImport.addField(csvElement, "Name", values, 2);
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 3);
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 4);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 5);
			HhStartDate finishDate = finishDateStr.trim().length() == 0 ? null
					: new HhStartDate(finishDateStr);
			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 6);
			Contract.insertNonCoreContract(isCore, participant, name,
					startDate, finishDate, chargeScript, rateScript);
		} else if (action.equals("update")) {
			/*
			 * String script = values[3];
			 * csvElement.appendChild(getField("Script", script)); String
			 * template = values[4]; csvElement.appendChild(getField("Template",
			 * template)); Report report = Report.getReport(name);
			 */
		}
	}

	static public void generalImportDno(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {

			String dnoCode = GeneralImport.addField(csvElement, "DNO Code",
					values, 0);
			Party dno = Party.getDno(dnoCode);
			String isCoreStr = GeneralImport.addField(csvElement, "Is Core?",
					values, 1);
			boolean isCore = Boolean.parseBoolean(isCoreStr);

			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 3);
			HhStartDate finishDate = null;
			if (finishDateStr.length() > 0) {
				finishDate = new HhStartDate(finishDateStr);
			}
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 4);

			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 5);
			Contract.insertDnoContract(isCore, dno.getParticipant(), dnoCode,
					startDate, finishDate, chargeScript, rateScript);
		}
	}

	static public Contract insertNonCoreContract(boolean isCore,
			Participant participant, String name, HhStartDate startDate,
			HhStartDate finishDate, String chargeScript, String rateScript)
			throws HttpException {
		return insertContract(isCore, 'Z', participant, name, startDate,
				finishDate, chargeScript, rateScript);
	}

	static public Contract insertDnoContract(boolean isCore,
			Participant participant, String name, HhStartDate startDate,
			HhStartDate finishDate, String chargeScript, String rateScript)
			throws HttpException {
		return insertContract(isCore, 'R', participant, name, startDate,
				finishDate, chargeScript, rateScript);
	}

	static public Contract insertMopContract(Participant participant,
			String name, HhStartDate startDate, HhStartDate finishDate,
			String chargeScript, String rateScript) throws HttpException {
		return insertContract(false, 'M', participant, name, startDate,
				finishDate, chargeScript, rateScript);
	}

	static public Contract insertSupplierContract(Participant participant,
			String name, HhStartDate startDate, HhStartDate finishDate,
			String chargeScript, String rateScript) throws HttpException {
		return insertContract(false, 'X', participant, name, startDate,
				finishDate, chargeScript, rateScript);
	}

	static public Contract insertContract(boolean isCore, char roleCode,
			Participant participant, String name, HhStartDate startDate,
			HhStartDate finishDate, String chargeScript, String rateScript)
			throws HttpException {
		Contract contract = new Contract(isCore, roleCode, participant, name,
				startDate, finishDate, chargeScript);
		Hiber.session().save(contract);
		Hiber.session().flush();
		contract.insertFirstRateScript(startDate, finishDate, rateScript);
		return contract;
	}

	private MarketRole role;

	private Party party;

	private boolean isCore;

	private String name;

	private RateScript startRateScript;

	private RateScript finishRateScript;

	private String chargeScript;

	private String properties;

	private String state;

	private Set<RateScript> rateScripts;

	public Contract() {
	}

	public Contract(boolean isCore, char roleCode, Participant participant,
			String name, HhStartDate startDate, HhStartDate finishDate,
			String chargeScript) throws HttpException {
		setRole(MarketRole.getMarketRole(roleCode));
		internalUpdate(isCore, participant, name, chargeScript);
	}

	public MarketRole getRole() {
		return role;
	}

	void setRole(MarketRole role) {
		this.role = role;
	}

	public Party getParty() {
		return party;
	}

	void setParty(Party party) {
		this.party = party;
	}

	public boolean getIsCore() {
		return isCore;
	}

	void setIsCore(boolean isCore) {
		this.isCore = isCore;
	}

	public String getName() {
		return name;
	}

	void setName(String name) {
		this.name = name;
	}

	public RateScript getStartRateScript() {
		return startRateScript;
	}

	void setStartRateScript(RateScript startRateScript) {
		this.startRateScript = startRateScript;
	}

	public RateScript getFinishRateScript() {
		return finishRateScript;
	}

	void setFinishRateScript(RateScript finishRateScript) {
		this.finishRateScript = finishRateScript;
	}

	public String getChargeScript() {
		return chargeScript;
	}

	void setChargeScript(String chargeScript) {
		this.chargeScript = chargeScript;
	}

	public Set<RateScript> getRateScripts() {
		return rateScripts;
	}

	void setRateScripts(Set<RateScript> rateScripts) {
		this.rateScripts = rateScripts;
	}

	protected void internalUpdate(boolean isCore, Participant participant,
			String name, String chargeScript) throws HttpException {
		setParty(Party.getParty(participant, role));
		setIsCore(isCore);
		name = name.trim();
		if (name.length() == 0) {
			throw new UserException("The contract name can't be blank.");
		}
		setName(name);
		PythonInterpreter interp = new PythonInterpreter();
		interp.set("contract", this);
		try {
			interp.compile(chargeScript);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		}
		setChargeScript(chargeScript);
	}

	@SuppressWarnings("unchecked")
	public void delete() throws HttpException {
		for (RateScript script : (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract.id = :contractId order by script.startDate.date")
				.setLong("contractId", getId()).list()) {
			Hiber.session().delete(script);
		}
		Hiber.session().delete(this);
	}

	@SuppressWarnings("unchecked")
	public RateScript insertRateScript(HhStartDate startDate, String script)
			throws HttpException {
		Query rateScriptQuery = Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract order by script.startDate.date")
				.setEntity("contract", this);
		List<RateScript> rateScripts = (List<RateScript>) rateScriptQuery
				.list();
		RateScript lastRateScript = rateScripts.get(rateScripts.size() - 1);
		if (HhStartDate.isAfter(startDate, lastRateScript.getFinishDate())) {
			throw new UserException("For the contract " + getId() + " called "
					+ getName() + ", the start date " + startDate
					+ " is after the last rate script.");
		}

		RateScript coveredRateScript = (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :startDate and (script.finishDate is null or script.finishDate.date >= :startDate)")
				.setEntity("contract", this)
				.setTimestamp("startDate", startDate.getDate()).uniqueResult();
		HhStartDate finishDate = null;
		if (coveredRateScript == null) {
			finishDate = rateScripts.get(0).getStartDate().getPrevious();
		} else {
			if (coveredRateScript.getStartDate().equals(
					coveredRateScript.getFinishDate())) {
				throw new UserException(
						"The start date falls on a rate script which is only half an hour in length, and so cannot be subdivided further.");
			}
			if (startDate.equals(coveredRateScript.getStartDate())) {
				throw new UserException(
						"The start date is the same as the start date of an existing rate script.");
			}
			finishDate = coveredRateScript.getFinishDate();
			coveredRateScript.setFinishDate(startDate.getPrevious());
		}

		RateScript newRateScript = new RateScript(this, startDate, finishDate,
				script);
		getRateScripts().add(newRateScript);
		Hiber.flush();
		rateScripts = (List<RateScript>) rateScriptQuery.list();
		setStartRateScript(rateScripts.get(0));
		setFinishRateScript(rateScripts.get(rateScripts.size() - 1));
		Hiber.flush();
		return newRateScript;
	}

	protected HhStartDate getStartDate() {
		return getStartRateScript().getStartDate();
	}

	protected HhStartDate getFinishDate() {
		return getFinishRateScript().getFinishDate();
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Contract) {
			Contract contract = (Contract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public int compareTo(Contract arg0) {
		return 0;
	}

	public Snag getSnag(UriPathElement uriId) throws HttpException {
		Snag snag = (Snag) Hiber
				.session()
				.createQuery(
						"from Snag snag where snag.contract = :contract and snag.id = :snagId")
				.setEntity("contract", this)
				.setLong("snagId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	public void httpDelete(Invocation inv) throws HttpException {
	}

	public String toString() {
		return "Contract id " + getId() + " name " + getName();
	}

	public RateScript getPreviousRateScript(RateScript script)
			throws HttpException {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.finishDate.date = :scriptFinishDate")
				.setEntity("contract", this)
				.setTimestamp("scriptFinishDate",
						script.getStartDate().getPrevious().getDate())
				.uniqueResult();
	}

	public RateScript getNextRateScript(RateScript rateScript)
			throws HttpException {
		if (rateScript.getFinishDate() == null) {
			return null;
		}
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date = :scriptStartDate")
				.setEntity("contract", this)
				.setTimestamp("scriptStartDate",
						rateScript.getFinishDate().getNext().getDate())
				.uniqueResult();
	}

	public Invocable engine() throws HttpException {
		ScriptEngineManager engineMgr = new ScriptEngineManager();
		ScriptEngine scriptEngine = engineMgr.getEngineByName("jython");
		Invocable invocableEngine = null;
		try {
			scriptEngine.eval(chargeScript);
			scriptEngine.put("contract", this);
			invocableEngine = (Invocable) scriptEngine;
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		}
		return invocableEngine;
		// return invocableEngine(getChargeScript());
	}

	public RateScript insertFirstRateScript(HhStartDate startDate,
			HhStartDate finishDate, String rateScriptStr) throws HttpException {
		setRateScripts(new HashSet<RateScript>());
		RateScript rateScript = new RateScript(this, startDate, finishDate,
				rateScriptStr);
		Hiber.session().save(rateScript);
		rateScripts.add(rateScript);
		Hiber.flush();
		setStartRateScript(rateScript);
		setFinishRateScript(rateScript);
		return rateScript;
	}

	@SuppressWarnings("unchecked")
	public List<RateScript> rateScripts(HhStartDate from, HhStartDate to) {
		return Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :to and (script.finishDate.date is null or script.finishDate.date >= :from)")
				.setEntity("contract", this)
				.setTimestamp("from", from.getDate())
				.setTimestamp("to", to.getDate()).list();
	}

	public RateScript rateScript(HhStartDate date) {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :date and (script.finishDate.date is null or script.finishDate.date >= :date)")
				.setEntity("contract", this)
				.setTimestamp("date", date.getDate()).uniqueResult();
	}

	public Object callFunction(String name, Object... args)
			throws HttpException {
		Object result = null;
		PythonInterpreter interp = new PythonInterpreter();
		try {
			interp.set("contract", this);
			interp.exec(chargeScript);
			PyObject function = interp.get(name);
			if (function == null) {
				throw new UserException("There isn't a function called " + name);
			}
			result = function.__call__(Py.javas2pys(args)).__tojava__(
					Object.class);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		} finally {
			interp.cleanup();
		}
		return result;
	}

	public static Contract getContract(Long id) throws HttpException {
		Contract contract = (Contract) Hiber.session().get(Contract.class, id);
		if (contract == null) {
			throw new UserException("There isn't a contract with that id.");
		}
		return contract;
	}

	public Batch getBatch(String reference) throws HttpException {
		Batch batch = (Batch) Hiber
				.session()
				.createQuery(
						"from Batch batch where batch.contract.id = :contractId and batch.reference = :reference")
				.setLong("contractId", getId())
				.setString("reference", reference).uniqueResult();
		if (batch == null) {
			throw new UserException("There isn't a batch attached to contract "
					+ getId() + " with reference " + reference + ".");
		}
		return batch;
	}

	public Batch insertBatch(String reference, String description)
			throws HttpException {
		Batch batch = new Batch(this, reference, description);
		try {
			Hiber.session().save(batch);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException(
					"There's already a batch with that reference.");
		}
		return batch;
	}

	public boolean isCore() {
		return getId() % 2 == 1;
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

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("contract");

		element.setAttribute("id", getId().toString());

		element.setAttribute("is-core",
				new Boolean(getId() % 2 == 1).toString());
		element.setAttribute("name", name);
		if (chargeScript != null) {
			element.setAttribute("charge-script", chargeScript);
		}
		return element;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.NON_CORE_CONTRACTS_INSTANCE.getEditUri()
				.resolve(getUriId()).append("/");
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element contractElement = toXml(doc);
		source.appendChild(contractElement);
		Element partyElement = party.toXml(doc);
		contractElement.appendChild(partyElement);
		Element participantElement = party.getParticipant().toXml(doc);
		partyElement.appendChild(participantElement);
		for (Party party : (List<Party>) Hiber
				.session()
				.createQuery(
						"from Party party where party.role.code = :roleCode order by party.name")
				.setCharacter("roleCode", role.getCode()).list()) {
			Element ptyElement = party.toXml(doc);
			source.appendChild(ptyElement);
			Element ptcptElement = party.getParticipant().toXml(doc);
			ptyElement.appendChild(ptcptElement);
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendSeeOther(Chellow.NON_CORE_CONTRACTS_INSTANCE.getEditUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			Long partyId = inv.getLong("party_id");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");
			Party party = Party.getParty(partyId);
			try {
				update(party, name, chargeScript);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	protected void internalUpdate(Party party, String name, String chargeScript)
			throws HttpException {
		if (party.getRole() != this.role) {
			throw new UserException(
					"The party role doesn't match the contract market role.");
		}
		setParty(party);
		name = name.trim();
		if (name.length() == 0) {
			throw new UserException("The contract name can't be blank.");
		}
		setName(name);
		PythonInterpreter interp = new PythonInterpreter();
		interp.set("contract", this);
		try {
			interp.compile(chargeScript);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		}
		setChargeScript(chargeScript);
	}

	public void update(Party party, String name, String chargeScript)
			throws HttpException {
		internalUpdate(party, name, chargeScript);
		Hiber.flush();
		onUpdate();
	}

	void onUpdate(HhStartDate from, HhStartDate to) throws HttpException {
		// TODO Auto-generated method stub

	}

	void onUpdate() throws HttpException {
		onUpdate(null, null);
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

	@SuppressWarnings("unchecked")
	public void delete(RateScript rateScript) throws HttpException {
		List<RateScript> rateScriptList = (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract order by script.startDate.date")
				.setEntity("contract", this).list();
		if (rateScriptList.size() < 2) {
			throw new UserException("You can't delete the last rate script.");
		}
		rateScripts.remove(rateScript);
		if (rateScriptList.get(0).equals(rateScript)) {
			setStartRateScript(rateScriptList.get(1));
			Hiber.flush();
			rateScriptList.get(1).setStartDate(rateScript.getStartDate());
		} else if (rateScriptList.get(rateScriptList.size() - 1).equals(
				rateScript)) {
			setFinishRateScript(rateScriptList.get(rateScriptList.size() - 2));
			Hiber.flush();
			rateScriptList.get(rateScriptList.size() - 2).setFinishDate(
					rateScript.getFinishDate());
		} else {
			RateScript prevScript = getPreviousRateScript(rateScript);
			prevScript.setFinishDate(rateScript.getFinishDate());
		}
		Hiber.flush();
		onUpdate(rateScript.getStartDate(), rateScript.getFinishDate());
	}

	RateScripts rateScriptsInstance() {
		return new RateScripts(this);
	}
}
