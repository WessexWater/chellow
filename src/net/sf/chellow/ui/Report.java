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
package net.sf.chellow.ui;

import java.io.IOException;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.util.List;

import javax.script.Invocable;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;
import javax.script.ScriptException;
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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.PersistentEntity;

import org.hibernate.exception.ConstraintViolationException;
import org.python.core.PyException;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Report extends PersistentEntity {
	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		String idString = GeneralImport.addField(csvElement, "Id", values, 0);
		Long id = null;
		String name = GeneralImport.addField(csvElement, "Name", values, 1);
		String script = GeneralImport.addField(csvElement, "Script", values, 2);
		String template = null;
		if (values.length > 3) {
			template = GeneralImport
					.addField(csvElement, "Template", values, 3);
		}
		if (action.equals("insert")) {
			if (idString.trim().length() > 0) {
				id = new Long(idString);
			}
			Report.insertReport(id, name, script, template);
		} else if (action.equals("update")) {
			Report report = Report.getReport(id);
			report.update(name, script, template);
		}
	}

	public static Report getReport(Long id) throws HttpException {
		Report report = (Report) Hiber.session().get(Report.class, id);
		if (report == null) {
			throw new NotFoundException("The report " + id + " can't be found.");
		}
		return report;
	}

	public static Report getReport(String name) throws HttpException {
		Report report = (Report) Hiber.session().createQuery(
				"from Report report where report.name = :name").setString(
				"name", name).uniqueResult();
		if (report == null) {
			throw new NotFoundException("Can't find the report '" + name + "'.");
		}
		return report;
	}

	public static void loadReports(ServletContext context) throws HttpException {
		try {
			GeneralImport process = new GeneralImport(null, context
					.getResource("/WEB-INF/reports.xml").openStream(), "xml");
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

	public static Report insertReport(Long id, String name, String script,
			String template) throws HttpException {
		Report report = new Report(id, name, script, template);
		try {
			Hiber.session().save(report);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			Hiber.rollBack();
			throw new UserException("There's already a report with that name.");
		}
		return report;
	}

	private String name;

	private String script;

	private String template;

	public Report() {
	}

	public Report(Long id, String name, String script, String template)
			throws HttpException {
		Configuration configuration = Configuration.getConfiguration();
		boolean isCore = name.startsWith("0 ");

		if (id == null) {
			if (isCore) {
				id = configuration.nextCoreReportId();
			} else {
				id = configuration.nextUserReportId();
			}
		} else {
			if (isCore) {
				if (id > configuration.getCoreReportId()) {
					configuration.setCoreReportId(id);
				}
			} else {
				if (id > configuration.getUserReportId()) {
					configuration.setUserReportId(id);
				}
			}
		}
		boolean isOdd = id % 2 == 1;
		if (isOdd != isCore) {
			throw new UserException(
					"The ids of core reports must be odd, those of user reports must be even. Report id "
							+ id
							+ ", Is Odd? "
							+ isOdd
							+ ", is core? "
							+ isCore + ".");
		}
		setId(id);
		update(name, script, template);
	}

	public String getName() {
		return name;
	}

	void setName(String name) {
		this.name = name;
	}

	public String getScript() {
		return script;
	}

	void setScript(String script) {
		this.script = script;
	}

	public String getTemplate() {
		return template;
	}

	void setTemplate(String template) {
		this.template = template;
	}

	public void update(String name, String script, String template) {
		setName(name);
		setScript(script);
		if (template != null && template.trim().length() == 0) {
			template = null;
		}
		setTemplate(template);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (ReportOutput.URI_ID.equals(uriId)) {
			return new ReportOutput(this);
		} else if (ReportXmlOutput.URI_ID.equals(uriId)) {
			return new ReportXmlOutput(this);
		} else {
			throw new NotFoundException();
		}
	}

	public Object callFunction(String functionName, Object[] args)
			throws HttpException {
		Object result = null;
		ScriptEngineManager manager = new ScriptEngineManager();
		ScriptEngine engine = manager.getEngineByName("jython");
		try {
			result = ((Invocable) engine).invokeFunction(functionName, args);
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

	public void run(Invocation inv, Document doc) throws HttpException {
		PythonInterpreter interp = new PythonInterpreter();
		Element source = doc.getDocumentElement();
		interp.set("doc", doc);
		interp.set("source", source);
		interp.set("inv", inv);
		StringWriter out = new StringWriter();
		interp.setOut(out);
		StringWriter err = new StringWriter();
		interp.setErr(err);
		try {
			interp.exec(script);
			/*
			 * } catch (PyException e) {
			 * inv.getResponse().setContentType("text/html"); Object obj =
			 * e.value.__tojava__(HttpException.class); if (obj instanceof
			 * HttpException) { throw (HttpException) obj; } else { throw new
			 * UserException(e.toString()); }
			 */
		} catch (Throwable e) {
			if (out.toString().length() > 0) {
				source.appendChild(new MonadMessage(out.toString()).toXml(doc));
			}
			if (err.toString().length() > 0) {
				source.appendChild(new MonadMessage(err.toString()).toXml(doc));
			}
			throw new UserException(e.getMessage() + " "
					+ HttpException.getStackTraceString(e));
		}
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.REPORTS_INSTANCE.getUri().resolve(getId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportElement = toXml(doc);
		source.appendChild(reportElement);
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendFound(Chellow.REPORTS_INSTANCE.getUri());
		} else {
			String name = inv.getString("name");
			String script = inv.getString("script");
			String template = inv.getString("template");

			if (!inv.isValid()) {
				throw new UserException();
			}
			script = script.replace("\r", "").replace("\t", "    ");
			template = template.length() == 0 ? null : template.replace("\r",
					"").replace("\t", "    ");
			Document doc = MonadUtils.newSourceDocument();
			Element source = doc.getDocumentElement();
			Element scriptElement = doc.createElement("script");
			source.appendChild(scriptElement);
			scriptElement.setTextContent(script);
			source.setAttribute("script", script);
			if (template != null) {
				Element templateElement = doc.createElement("template");
				source.appendChild(templateElement);
				templateElement.setTextContent(template);
			}
			if (!inv.isValid()) {
				Element reportElement = toXml(doc);
				source.appendChild(reportElement);
				throw new UserException(doc);
			}
			update(name, script, template);
			Hiber.commit();
			Element reportElement = toXml(doc);
			source.appendChild(reportElement);
			inv.sendOk(doc);
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "report");
		element.setAttribute("name", name);
		Element scriptElement = doc.createElement("script");
		element.appendChild(scriptElement);
		scriptElement.setTextContent(script);
		if (template != null) {
			Element templateElement = doc.createElement("template");
			element.appendChild(templateElement);
			templateElement.setTextContent(template);
		}
		return element;
	}

	public void delete() {
		Hiber.session().delete(this);
		Hiber.flush();
	}
}
