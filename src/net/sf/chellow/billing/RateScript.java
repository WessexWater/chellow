/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import java.util.Date;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.PersistentEntity;

import org.python.core.PyException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RateScript extends PersistentEntity {
	static public RateScript getRateScript(Long id) {
		return (RateScript) Hiber.session().get(RateScript.class, id);
	}

	private Service service;

	private HhEndDate startDate;

	private HhEndDate finishDate;

	private String script;

	public RateScript() {
	}

	public RateScript(Service service, HhEndDate startDate,
			HhEndDate finishDate, String script) throws HttpException {
		setService(service);
		internalUpdate(startDate, finishDate, script);
	}

	public Service getService() {
		return service;
	}

	void setService(Service service) {
		this.service = service;
	}

	public HhEndDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhEndDate startDate) {
		this.startDate = startDate;
	}

	public HhEndDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhEndDate finishDate) {
		this.finishDate = finishDate;
	}

	public String getScript() {
		return script;
	}

	void setScript(String script) {
		this.script = script;
	}

	void internalUpdate(HhEndDate startDate, HhEndDate finishDate, String script)
			throws InternalException {
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new InternalException(
					"start date can't be after the finish date");
		}
		setScript(script);
	}

	public void update(HhEndDate startDate, HhEndDate finishDate, String script)
			throws HttpException {
		HhEndDate originalStartDate = getStartDate();
		HhEndDate originalFinishDate = getFinishDate();
		RateScript previousRateScript = service.getPreviousRateScript(this);
		RateScript nextRateScript = service.getNextRateScript(this);

		internalUpdate(startDate, finishDate, script);
		if (previousRateScript != null) {
			if (!previousRateScript.getStartDate().getDate().before(
					finishDate.getDate())) {
				throw new UserException(
						"The start date must be after the start date of the previous rate script.");
			}
			previousRateScript.internalUpdate(
					previousRateScript.getStartDate(),
					finishDate.getPrevious(), previousRateScript.getScript());
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
			nextRateScript.internalUpdate(finishDate.getNext(), nextRateScript
					.getFinishDate(), nextRateScript.getScript());
		}
		Hiber.flush();
		HhEndDate checkFinishDate = null;
		if (originalFinishDate == null) {
			checkFinishDate = getFinishDate();
		} else if (finishDate != null) {
			checkFinishDate = finishDate.getDate().after(
					originalFinishDate.getDate()) ? finishDate
					: originalFinishDate;
		}
		HhEndDate checkStartDate = null;
		if (originalStartDate == null) {
			checkStartDate = getStartDate();
		} else {
			checkStartDate = startDate.getDate().before(
					originalStartDate.getDate()) ? startDate
					: originalStartDate;
		}
		service.updateNotification(checkStartDate, checkFinishDate);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "rate-script");

		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		element.setAttributeNode(MonadString.toXml(doc, "script", script
				.replace("\r", "").replace("\t", "    ")));
		return element;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws HttpException {
		return getService().rateScriptsInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		String script = inv.getString("script");
		if (inv.hasParameter("test")) {
			Long billId = inv.getLong("bill_id");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			Bill bill = Bill.getBill(billId);
			Document doc = document();
			Element source = doc.getDocumentElement();

			source.appendChild(bill.getElement().toXml(doc));
			inv.sendOk(doc);
		} else if (inv.hasParameter("delete")) {
			service.delete(this);
			Hiber.commit();
			inv.sendFound(service.rateScriptsInstance().getUri());
		} else {
			Date startDate = inv.getDate("start-date");
			Date finishDate = null;
			boolean hasFinished = inv.getBoolean("has-finished");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			if (hasFinished) {
				finishDate = inv.getDate("finish-date");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
			}
			try {
				update(HhEndDate.roundDown(startDate).getNext(),
						finishDate == null ? null : HhEndDate
								.roundDown(finishDate), script);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();

		if (service instanceof DsoService) {
			sourceElement.appendChild(toXml(doc, new XmlTree("service",
					new XmlTree("dso"))));
		} else {
			sourceElement.appendChild(toXml(doc, new XmlTree("service",
					new XmlTree("provider").put("organization"))));
		}
		sourceElement.appendChild(MonadDate.getMonthsXml(doc));
		sourceElement.appendChild(MonadDate.getDaysXml(doc));
		sourceElement.appendChild(new MonadDate().toXml(doc));
		return doc;
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

	public Object getRate(String rateName) throws HttpException {
		Object rate = null;
		try {
			rate = invocableEngine().invokeFunction(rateName, new Object[0]);
		} catch (ScriptException e) {
			throw new UserException(e.getMessage());
		} catch (NoSuchMethodException e) {
			throw new UserException("The rate script " + getUri()
					+ " has no such method: " + e.getMessage());
		} catch (PyException e) {
			Object obj = e.value.__tojava__(HttpException.class);
			if (obj instanceof HttpException) {
				throw (HttpException) obj;
			} else {
				throw new UserException(e.toString());
			}
		}
		return rate;
	}
}