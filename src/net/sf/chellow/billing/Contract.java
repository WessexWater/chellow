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
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.Snag;

import org.hibernate.Criteria;
import org.hibernate.criterion.Restrictions;
import org.hibernate.exception.ConstraintViolationException;
import org.python.core.PyException;
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

	// private Party party;

	private String name;

	private RateScript startRateScript;

	private RateScript finishRateScript;

	private String chargeScript;

	private Set<RateScript> rateScripts;

	public Contract() {
	}

	public Contract(String name, HhEndDate startDate, HhEndDate finishDate,
			String chargeScript, String rateScriptStr) throws HttpException {
		// setParty(party);
		rateScripts = new HashSet<RateScript>();
		RateScript rateScript = new RateScript(this, startDate, finishDate,
				rateScriptStr);
		rateScripts.add(rateScript);
		setStartRateScript(rateScript);
		setFinishRateScript(rateScript);
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
		setChargeScript(chargeScript);
	}

	public void update(String name, String chargeScript) throws HttpException {
		internalUpdate(name, chargeScript);
		onUpdate();
	}

	void onUpdate() throws HttpException {
		onUpdate(null, null);
	}

	public void delete() throws HttpException {
		onUpdate(startRateScript.getStartDate(), finishRateScript
				.getFinishDate());
	}

	public void delete(RateScript rateScript) throws HttpException {
		List<RateScript> rateScriptList = new ArrayList<RateScript>(rateScripts);
		if (rateScriptList.size() < 2) {
			throw new UserException("You can't delete the last rate script.");
		}
		if (!rateScriptList.get(0).equals(rateScript)
				&& !rateScriptList.get(rateScriptList.size() - 1).equals(
						rateScript)) {
			throw new UserException(
					"You can only delete the first and last rate scripts.");
		}
		getRateScripts().remove(rateScript);
		Hiber.flush();
		onUpdate(rateScript.getStartDate(), rateScript
				.getFinishDate());
	}

	protected HhEndDate getStartDate() {
		return getStartRateScript().getStartDate();
	}

	protected HhEndDate getFinishDate() {
		return getFinishRateScript().getFinishDate();
	}

	@SuppressWarnings("unchecked")
	void onUpdate(HhEndDate from, HhEndDate to) throws HttpException {
		if (from == null) {
			from = getStartDate();
		}
		if (to == null) {
			to = getFinishDate();
		}
		Criteria criteria = Hiber.session().createCriteria(Bill.class).add(
				Restrictions.ge("finishDate.date", from.getDate()));
		if (to != null) {
			criteria.add(Restrictions.le("startDate.date", to.getDate()));
		}
		for (Bill bill : (List<Bill>) criteria.list()) {
			bill.check();
		}
	}

	public Element toXml(Document doc) throws HttpException {
		return toXml(doc, "service");
	}

	public Element toXml(Document doc, String elementName) throws HttpException {
		Element element = super.toXml(doc, elementName);

		element.setAttribute("name", name);
		// startRateScript.setLabel("start");
		// element.appendChild(startRateScript.toXml(doc));
		// finishRateScript.setLabel("finish");
		// element.appendChild(finishRateScript.toXml(doc));
		if (chargeScript != null) {
			element.setAttribute("charge-script", chargeScript
					.replace("\r", "").replace("\t", "    "));
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

	public VirtualBill virtualBill(String name, Account account,
			HhEndDate from, HhEndDate to) throws HttpException {
		VirtualBill bill = null;

		try {
			Object[] args = { account, from, to };
			bill = (VirtualBill) engine().invokeFunction(name + "VirtualBill",
					args);
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

	/*
	 * public Invocable invocableEngine(String chargeScript) throws
	 * HttpException { ScriptEngineManager engineMgr = new
	 * ScriptEngineManager(); ScriptEngine scriptEngine =
	 * engineMgr.getEngineByName("jython"); Invocable invocableEngine = null;
	 * try { scriptEngine.eval(chargeScript); scriptEngine.put("service", this);
	 * invocableEngine = (Invocable) scriptEngine; } catch (ScriptException e) {
	 * throw new UserException(e.getMessage()); } return invocableEngine; }
	 */
	public VirtualBill billElement(Account account, HhEndDate from, HhEndDate to)
			throws HttpException {
		return virtualBill("total", account, from, to);
	}

	public VirtualBill billElement(String name, Account account,
			HhEndDate from, HhEndDate to) throws HttpException {
		return virtualBill(name, account, from, to);
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

	@SuppressWarnings("unchecked")
	public RateScript insertRateScript(HhEndDate startDate, String script)
			throws HttpException {
		List<RateScript> rateScripts = (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract order by script.startDate.date")
				.setEntity("contract", this).list();
		RateScript rateScript = rateScripts.get(rateScripts.size() - 1);
		if (rateScript.getFinishDate() != null
				&& startDate.getDate().after(
						rateScript.getFinishDate().getDate())) {
			throw new UserException(
					"For the contract " + getId() + " called "+ getName() + ", the start date " + startDate + " is after the last rate script.");
		}
		HhEndDate finishDate = rateScript.getStartDate().getPrevious();
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
		RateScript newRateScript = new RateScript(this,
				startDate == null ? rateScripts.get(rateScripts.size())
						.getFinishDate().getNext() : startDate, finishDate,
				script);
		getRateScripts().add(newRateScript);
		Hiber.flush();
		onUpdate(newRateScript.getStartDate(), newRateScript
				.getFinishDate());
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
	public List<RateScript> rateScripts(HhEndDate from, HhEndDate to) {
		return Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :to and (script.finishDate.date is null or script.finishDate.date >= :from)")
				.setEntity("contract", this).setTimestamp("from",
						from.getDate()).setTimestamp("to", to.getDate()).list();
	}

	public RateScript rateScript(HhEndDate date) {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.startDate.date <= :date and (script.finishDate.date is null or script.finishDate.date >= :date)")
				.setEntity("contract", this).setTimestamp("date",
						date.getDate()).uniqueResult();
	}

	public Object callFunction(String functionName, Object[] args)
			throws HttpException {
		Object result = null;
		try {
			result = engine().invokeFunction(functionName, args);
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		} catch (NoSuchMethodException e) {
			throw new UserException("The charge script " + getUri()
					+ " has no such method: " + e.getMessage());
		} catch (PyException e) {
			Object obj = e.value.__tojava__(HttpException.class);
			if (obj instanceof HttpException) {
				throw (HttpException) obj;
			} else {
				throw new UserException(e.toString());
			}
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

	public Batch insertBatch(String reference) throws HttpException {
		Batch batch = new Batch(this, reference);
		Hiber.session().save(batch);
		return batch;
	}

	@SuppressWarnings("unchecked")
	public void deleteAccount(Account account) throws HttpException {
		if (!account.getContract().equals(this)) {
			throw new UserException(
					"The account isn't attached to this contract.");
		}
		if ((Long) Hiber.session().createQuery(
				"select count(*) from Bill bill where bill.account = :account")
				.setEntity("account", account).uniqueResult() > 0) {
			throw new UserException(
					"Can't delete this account as there are still bills attached to it.");
		}
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from Mpan mpan where mpan.supplierAccount.id = :accountId")
				.setLong("accountId", account.getId()).uniqueResult() > 0) {
			throw new UserException(
					"Can't delete this account as there are still MPANs attached to it.");
		}
		for (AccountSnag snag : (List<AccountSnag>) Hiber.session()
				.createQuery(
						"from AccountSnag snag where snag.account = :account")
				.setEntity("account", account).list()) {
			Hiber.session().delete(snag);
			Hiber.flush();
		}
		Hiber.session().delete(account);
		Hiber.flush();
	}

	public Accounts accountsInstance() {
		return new Accounts(this);
	}

	public Account insertAccount(String reference) throws HttpException {
		reference = reference.trim();
		Account account = new Account(this, reference);
		try {
			Hiber.session().save(account);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException(
					"There's already an account with the reference, '"
							+ reference + "' attached to this provider.");
		}
		return account;
	}

	public AccountSnags getSnagsAccountInstance() {
		return new AccountSnags(this);
	}

	public Account getAccount(String reference) throws HttpException {
		Account account = findAccount(reference);
		if (account == null) {
			throw new NotFoundException("The account '" + reference
					+ "' can't be found.");
		}
		return account;
	}

	public Account findAccount(String reference) throws HttpException {
		return (Account) Hiber
				.session()
				.createQuery(
						"from Account account where account.contract = :contract and account.reference = :reference")
				.setEntity("contract", this).setString("reference", reference)
				.uniqueResult();
	}

	public Batches batchesInstance() {
		return new Batches(this);
	}

	public abstract Party getParty();
}
