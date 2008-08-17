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

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;

import net.sf.chellow.hhimport.HhDataImportProcesses;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.Snag;

import org.python.core.PyException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public abstract class Service extends PersistentEntity implements
		Comparable<Service>, Urlable {

	public static Service getService(Long id) throws HttpException {
		Service service = (Service) Hiber.session().get(Service.class, id);
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

	public Service() {
	}

	public Service(String name, HhEndDate startDate,
			String chargeScript) throws HttpException {
		rateScripts = new HashSet<RateScript>();
		RateScript rateScript = new RateScript(this, startDate, null,
				chargeScript);
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
		setName(name);
		setChargeScript(chargeScript);
	}

	@SuppressWarnings("unchecked")
	public void update(String name, String chargeScript) throws HttpException {
		internalUpdate(name, chargeScript);
		updateNotification();
	}

	void updateNotification() throws HttpException {
		updateNotification(null, null);
	}

	public void delete() throws HttpException {
		updateNotification(startRateScript.getStartDate(), finishRateScript
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
		updateNotification(rateScript.getStartDate(), rateScript
				.getFinishDate());
	}

	protected HhEndDate getStartDate() {
		return getStartRateScript().getStartDate();
	}

	protected HhEndDate getFinishDate() {
		return getFinishRateScript().getFinishDate();
	}

	@SuppressWarnings("unchecked")
	void updateNotification(HhEndDate from, HhEndDate to) throws HttpException {
		if (from == null) {
			from = getStartDate();
		}
		if (to == null) {
			to = getFinishDate();
		}
		List<Bill> bills = null;
		if (to == null) {
			bills = (List<Bill>) Hiber.session().createQuery(
					"from Bill bill where bill.finishDate.date >= :from")
					.setTimestamp("from", from.getDate()).list();
		} else {
			bills = (List<Bill>) Hiber
					.session()
					.createQuery(
							"from Bill bill where (bill.finishDate.date >= :from) and (bill.startDate.date <= :to)")
					.setTimestamp("from", from.getDate()).setTime("to",
							to.getDate()).list();
		}
		for (Bill bill : bills) {
			bill.check();
		}
	}

	public Element toXml(Document doc) throws HttpException {
		return toXml(doc, "service");
	}

	public Element toXml(Document doc, String elementName) throws HttpException {
		Element element = super.toXml(doc, elementName);

		element.setAttribute("name", name);
		//startRateScript.setLabel("start");
		//element.appendChild(startRateScript.toXml(doc));
		//finishRateScript.setLabel("finish");
		//element.appendChild(finishRateScript.toXml(doc));
		if (chargeScript != null) {
			element.setAttribute("charge-script", chargeScript
					.replace("\r", "").replace("\t", "    "));
		}
		return element;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Service) {
			Service contract = (Service) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public int compareTo(Service arg0) {
		return 0;
	}

	public Snag getSnag(UriPathElement uriId) throws HttpException,
			InternalException {
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

	public HhDataImportProcesses getHhDataImportProcessesInstance() {
		return new HhDataImportProcesses(this);
	}

	public void httpDelete(Invocation inv) throws HttpException {
	}

	public String toString() {
		return "Contract id " + getId() + " name " + getName();
	}

	public BillElement billElement(String name, String chargeScript,
			Account account, HhEndDate from, HhEndDate to)
			throws HttpException {
		BillElement billElement = null;

		try {
			Object[] args = { account, from, to };
			billElement = (BillElement) engine().invokeFunction(
					name + "Element", args);
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
		return billElement;
	}

	public Invocable invocableEngine(String chargeScript) throws HttpException {
		ScriptEngineManager engineMgr = new ScriptEngineManager();
		ScriptEngine scriptEngine = engineMgr.getEngineByName("jython");
		Invocable invocableEngine = null;
		try {
			scriptEngine.eval(chargeScript);
			scriptEngine.put("service", this);
			invocableEngine = (Invocable) scriptEngine;
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		}
		return invocableEngine;
	}

	public BillElement billElement(Account account, HhEndDate from, HhEndDate to)
			throws HttpException {
		return billElement("total", getChargeScript(), account, from, to);
	}

	public BillElement billElement(String name, Account account,
			HhEndDate from, HhEndDate to) throws HttpException {
		return billElement(name, getChargeScript(), account, from, to);
	}

	public RateScript getPreviousRateScript(RateScript script)
			throws HttpException {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.service = :service and script.finishDate.date = :scriptFinishDate")
				.setEntity("service", this).setTimestamp("scriptFinishDate",
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
						"from RateScript script where script.service = :service and script.startDate.date = :scriptStartDate")
				.setEntity("service", this).setTimestamp("scriptStartDate",
						rateScript.getFinishDate().getNext().getDate())
				.uniqueResult();
	}

	public Invocable engine() throws HttpException {
		return invocableEngine(getChargeScript());
	}

	@SuppressWarnings("unchecked")
	public RateScript insertRateScript(HhEndDate startDate, String script)
			throws HttpException {
		List<RateScript> rateScripts = (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.service = :service order by script.startDate.date")
				.setEntity("service", this).list();
		RateScript rateScript = rateScripts.get(rateScripts.size() - 1);
		if (rateScript.getFinishDate() != null
				&& startDate.getDate().after(
						rateScript.getFinishDate().getDate())) {
			throw new UserException(
					"The start date is after the last rate script.");
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
		updateNotification(newRateScript.getStartDate(), newRateScript
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
						"from RateScript script where script.service = :service and script.startDate.date <= :to and (script.finishDate.date is null or script.finishDate.date >= :from)")
				.setEntity("service", this)
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate()).list();
	}

	@SuppressWarnings("unchecked")
	public RateScript rateScript(HhEndDate date) {
		return (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.service = :service and script.startDate.date <= :date and (script.finishDate.date is null or script.finishDate.date >= :date)")
				.setEntity("service", this)
				.setTimestamp("date", date.getDate()).uniqueResult();
	}

	public Object callFunction(String functionName, Object[] args)
			throws HttpException {
		Object result = null;
		try {
			result = invocableEngine(getChargeScript()).invokeFunction(
					functionName, args);
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
}