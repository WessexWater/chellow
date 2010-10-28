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

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.Snag;
import net.sf.chellow.physical.Supply;

import org.hibernate.exception.ConstraintViolationException;
import org.python.core.Py;
import org.python.core.PyException;
import org.python.core.PyObject;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class Contract extends PersistentEntity implements
		Comparable<Contract> {

	public static Contract getService(Long id) throws HttpException {
		Contract service = (Contract) Hiber.session().get(Contract.class, id);
		if (service == null) {
			throw new UserException("There isn't a service with that id.");
		}
		return service;
	}

	private String name;

	private RateScript startRateScript;

	private RateScript finishRateScript;

	private String chargeScript;

	private Set<RateScript> rateScripts;

	public Contract() {
	}

	public Contract(Long id, Boolean isCore, String name,
			HhStartDate startDate, HhStartDate finishDate, String chargeScript)
			throws HttpException {
		Configuration configuration = Configuration.getConfiguration();

		if (id == null) {
			if (isCore) {
				id = configuration.nextCoreContractId();
			} else {
				id = configuration.nextUserContractId();
			}
		} else {
			isCore = id % 2 == 1;
			if (isCore) {
				if (id > configuration.getCoreContractId()) {
					configuration.setCoreContractId(id);
				}
			} else {
				if (id > configuration.getUserContractId()) {
					configuration.setUserContractId(id);
				}
			}
		}
		setId(id);
		internalUpdate(name, chargeScript);
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

	protected void internalUpdate(String name, String chargeScript)
			throws HttpException {
		setName(name.trim());
		PythonInterpreter interp = new PythonInterpreter();
		interp.set("contract", this);
		try {
			interp.compile(chargeScript);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		}
		setChargeScript(chargeScript);
	}

	public void update(String name, String chargeScript) throws HttpException {
		internalUpdate(name, chargeScript);
		Hiber.flush();
		onUpdate();
	}

	void onUpdate() throws HttpException {
		onUpdate(null, null);
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

	public void delete(RateScript rateScript) throws HttpException {
		List<RateScript> rateScriptList = new ArrayList<RateScript>(rateScripts);
		if (rateScriptList.size() < 2) {
			throw new UserException("You can't delete the last rate script.");
		}
		if (rateScriptList.get(0).equals(rateScript)) {
			rateScriptList.get(1).setStartDate(rateScript.getStartDate());
			setStartRateScript(rateScriptList.get(1));
			rateScripts.remove(rateScript);
		} else if (rateScriptList.get(rateScriptList.size() - 1).equals(
				rateScript)) {
			rateScriptList.get(rateScriptList.size() - 2).setFinishDate(
					rateScript.getFinishDate());
			setFinishRateScript(rateScriptList.get(rateScriptList.size() - 2));
			rateScripts.remove(rateScript);
		} else {
			RateScript prevScript = getPreviousRateScript(rateScript);
			prevScript.setFinishDate(rateScript.getFinishDate());
			rateScripts.remove(rateScript);
		}
		Hiber.flush();
		onUpdate(rateScript.getStartDate(), rateScript.getFinishDate());
	}

	protected HhStartDate getStartDate() {
		return getStartRateScript().getStartDate();
	}

	protected HhStartDate getFinishDate() {
		return getFinishRateScript().getFinishDate();
	}

	abstract void onUpdate(HhStartDate from, HhStartDate to)
			throws HttpException;

	public Element toXml(Document doc) throws HttpException {
		return toXml(doc, "service");
	}

	public Element toXml(Document doc, String elementName) throws HttpException {
		Element element = super.toXml(doc, elementName);
		element.setAttribute("is-core", new Boolean(getId() % 2 == 1)
				.toString());
		element.setAttribute("name", name);
		if (chargeScript != null) {
			element.setAttribute("charge-script", chargeScript);
		}
		return element;
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
				.setEntity("contract", this).setLong("snagId",
						Long.parseLong(uriId.getString())).uniqueResult();
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

	@SuppressWarnings("unchecked")
	public Map<String, Double> virtualBill(Supply supply, HhStartDate from,
			HhStartDate to) throws HttpException {
		Map<String, Double> bill = null;

		try {
			Object[] args = { supply, from, to };
			bill = (Map<String, Double>) engine().invokeFunction(
					"virtual_bill", args);
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		} catch (NoSuchMethodException e) {
			throw new UserException("For the service " + getUri()
					+ " the script has no such method: " + e.getMessage());
		} catch (PyException e) {
			Object obj = e.value.__tojava__(HttpException.class);
			if (obj instanceof HttpException) {
				throw (HttpException) obj;
			} else {
				throw new UserException(e.toString());
			}
		}
		return bill;
	}

	public RateScript getPreviousRateScript(RateScript script)
			throws HttpException {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.finishDate.date = :scriptFinishDate")
				.setEntity("contract", this).setTimestamp("scriptFinishDate",
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
				.setEntity("contract", this).setTimestamp("scriptStartDate",
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

	public RateScript insertFirstRateScript(Long id, HhStartDate startDate,
			HhStartDate finishDate, String rateScriptStr) throws HttpException {
		setRateScripts(new HashSet<RateScript>());
		RateScript rateScript = new RateScript(this, id, startDate, finishDate,
				rateScriptStr);
		Hiber.session().save(rateScript);
		rateScripts.add(rateScript);
		Hiber.flush();
		setStartRateScript(rateScript);
		setFinishRateScript(rateScript);
		return rateScript;
	}

	@SuppressWarnings("unchecked")
	public RateScript insertRateScript(Long id, HhStartDate startDate,
			String script) throws HttpException {
		List<RateScript> rateScripts = (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract order by script.startDate.date")
				.setEntity("contract", this).list();
		RateScript rateScript = rateScripts.get(rateScripts.size() - 1);
		if (rateScript.getFinishDate() != null
				&& startDate.getDate().after(
						rateScript.getFinishDate().getDate())) {
			throw new UserException("For the contract " + getId() + " called "
					+ getName() + ", the start date " + startDate
					+ " is after the last rate script.");
		}
		HhStartDate finishDate = rateScript.getStartDate().getPrevious();
		for (int i = 0; i < rateScripts.size(); i++) {
			rateScript = rateScripts.get(i);
			if (!startDate.getDate()
					.before(rateScript.getStartDate().getDate())
					&& (rateScript.getFinishDate() == null || !startDate
							.getDate().after(
									rateScript.getFinishDate().getDate()))) {
				if (rateScript.getStartDate()
						.equals(rateScript.getFinishDate())) {
					throw new UserException(
							"The start date falls on a rate script which is only half an hour in length, and so cannot be subdivided further.");
				}
				if (startDate.equals(rateScript.getStartDate())) {
					throw new UserException(
							"The start date is the same as the start date of an existing rate script.");
				}
				finishDate = rateScript.getFinishDate();
				rateScript.setFinishDate(startDate.getPrevious());
			}
		}
		RateScript newRateScript = new RateScript(this, id,
				startDate == null ? rateScripts.get(rateScripts.size())
						.getFinishDate().getNext() : startDate, finishDate,
				script);
		getRateScripts().add(newRateScript);
		RateScript[] scripts = getRateScripts().toArray(new RateScript[0]);
		setStartRateScript(scripts[0]);
		setFinishRateScript(scripts[scripts.length - 1]);
		Hiber.flush();
		onUpdate(newRateScript.getStartDate(), newRateScript.getFinishDate());
		return newRateScript;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RateScripts.URI_ID.equals(uriId)) {
			return rateScriptsInstance();
		} else {
			throw new NotFoundException();
		}
	}

	RateScripts rateScriptsInstance() {
		return new RateScripts(this);
	}

	@SuppressWarnings("unchecked")
	public List<RateScript> rateScripts(HhStartDate from, HhStartDate to) {
		return Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :to and (script.finishDate.date is null or script.finishDate.date >= :from)")
				.setEntity("contract", this).setTimestamp("from",
						from.getDate()).setTimestamp("to", to.getDate()).list();
	}

	public RateScript rateScript(HhStartDate date) {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :date and (script.finishDate.date is null or script.finishDate.date >= :date)")
				.setEntity("contract", this).setTimestamp("date",
						date.getDate()).uniqueResult();
	}

	public Object callFunction(String name, Object... args)
			throws HttpException {
		PythonInterpreter interp = new PythonInterpreter();
		// StringWriter out = new StringWriter();
		// interp.setOut(out);
		// StringWriter err = new StringWriter();
		// interp.setErr(err);
		interp.set("contract", this);
		try {
			interp.exec(chargeScript);
		} catch (PyException e) {
			Object obj = e.value.__tojava__(HttpException.class);
			if (obj instanceof HttpException) {
				throw (HttpException) obj;
			} else {
				throw new UserException(e.toString());
			}
		} catch (Throwable e) {
			throw new UserException(e.getMessage());
			// + " " + out.toString() + " "
			// + err.toString() + " ");
		}
		try {
			PyObject function = interp.get(name);
			if (function == null) {
				throw new UserException("There isn't a function called " + name);
			}
			return function.__call__(Py.javas2pys(args)).__tojava__(
					Object.class);
		} catch (PyException pye) {
			throw new UserException(HttpException.getStackTraceString(pye));
		}
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
				.setLong("contractId", getId()).setString("reference",
						reference).uniqueResult();
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
			throw new UserException("There's already a batch with that name.");
		}
		return batch;
	}

	public boolean isCore() {
		return getId() % 2 == 1;
	}

	public Batches batchesInstance() {
		return new Batches(this);
	}

	public abstract Party getParty();

	public abstract String missingBillSnagDescription();
}
