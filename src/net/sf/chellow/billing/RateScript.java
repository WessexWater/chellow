/*******************************************************************************
 * 
 *  Copyright (c) 2005-2014 Wessex Water Services Limited
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
import java.util.Date;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.PersistentEntity;

import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RateScript extends PersistentEntity {
	static public RateScript getRateScript(Long id) {
		return (RateScript) Hiber.session().get(RateScript.class, id);
	}

	private Contract contract;

	private HhStartDate startDate;

	private HhStartDate finishDate;

	private String script;

	public RateScript() {
	}

	public RateScript(Contract contract, HhStartDate startDate,
			HhStartDate finishDate, String script) throws HttpException {
		setContract(contract);
		internalUpdate(startDate, finishDate, script);
	}

	public Contract getContract() {
		return contract;
	}

	void setContract(Contract contract) {
		this.contract = contract;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public String getScript() {
		return script;
	}

	void setScript(String script) {
		this.script = script;
	}

	void internalUpdate(HhStartDate startDate, HhStartDate finishDate,
			String script) throws HttpException {
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new UserException(
					"The start date can't be after the finish date");
		}
		PythonInterpreter interp = new PythonInterpreter();
		try {
			interp.compile(script);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		}
		setScript(script);
	}

	public void update(HhStartDate startDate, HhStartDate finishDate,
			String script) throws HttpException {
		RateScript previousRateScript = contract.getPreviousRateScript(this);
		RateScript nextRateScript = contract.getNextRateScript(this);

		internalUpdate(startDate, finishDate, script);
		if (previousRateScript != null) {
			if (!previousRateScript.getStartDate().getDate()
					.before(startDate.getDate())) {
				throw new UserException(
						"The start date must be after the start date of the previous rate script.");
			}
			previousRateScript.internalUpdate(
					previousRateScript.getStartDate(), startDate.getPrevious(),
					previousRateScript.getScript());
		}
		if (nextRateScript != null) {
			if (finishDate == null) {
				throw new UserException(
						"The finish date must be before the finish date of the next rate script.");
			}
			if (nextRateScript.getFinishDate() != null
					&& !finishDate.getDate().before(
							nextRateScript.getFinishDate().getDate())) {
				throw new UserException(
						"The finish date must be before the finish date of the next rate script.");
			}
			nextRateScript.internalUpdate(finishDate.getNext(),
					nextRateScript.getFinishDate(), nextRateScript.getScript());
		}
		Hiber.flush();
	}

	public Invocable invocableEngine() throws HttpException {
		ScriptEngineManager engineMgr = new ScriptEngineManager();
		ScriptEngine scriptEngine = engineMgr.getEngineByName("jython");
		Invocable invocableEngine = null;
		try {
			scriptEngine.eval(script);
			invocableEngine = (Invocable) scriptEngine;
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		}
		return invocableEngine;
	}

	@Override
	public MonadUri getEditUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "rate-script");

		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		element.setAttribute("script", script);
		return element;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		if (inv.hasParameter("delete")) {
			try {
				contract.delete(this);
				Hiber.commit();
			} catch (UserException e) {
				Hiber.rollBack();
				e.setDocument(document());
				throw e;
			}
			inv.sendSeeOther(contract.rateScriptsInstance().getEditUri());
		} else {
			String script = inv.getString("script");
			Date startDate = inv.getDateTime("start");
			HhStartDate finishDate = null;
			boolean hasFinished = inv.getBoolean("has-finished");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			script = script.replace("\r", "").replace("\t", "    ");
			if (hasFinished) {
				Date finishDateRaw = inv.getDateTime("finish");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				finishDate = HhStartDate.roundDown(finishDateRaw);
			}
			try {
				update(HhStartDate.roundDown(startDate), finishDate, script);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("contract",
				new XmlTree("party"))));
		sourceElement.appendChild(MonadDate.getMonthsXml(doc));
		sourceElement.appendChild(MonadDate.getDaysXml(doc));
		sourceElement.appendChild(MonadDate.getHoursXml(doc));
		sourceElement.appendChild(HhStartDate.getHhMinutesXml(doc));
		sourceElement.appendChild(new MonadDate().toXml(doc));
		return doc;
	}
}