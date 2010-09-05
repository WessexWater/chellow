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
import java.util.Map;

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
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.PersistentEntity;

import org.hibernate.exception.ConstraintViolationException;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Report extends PersistentEntity {
	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String idString = GeneralImport.addField(csvElement, "Id", values,
					0);
			Long id = null;
			if (idString.length() > 0) {
				id = new Long(idString);
			}
			String isCoreStr = GeneralImport.addField(csvElement, "Is Core?",
					values, 1);
			boolean isCore = Boolean.parseBoolean(isCoreStr);
			String name = GeneralImport.addField(csvElement, "Name", values, 2);
			String script = GeneralImport.addField(csvElement, "Script",
					values, 3);
			String template = null;
			if (values.length > 4) {
				template = GeneralImport.addField(csvElement, "Template",
						values, 4);
			}
			Report.insertReport(id, isCore, name, script, template);
		} else if (action.equals("update")) {
			String idString = GeneralImport.addField(csvElement, "Id", values,
					0);
			Long id = new Long(idString);
			String name = GeneralImport.addField(csvElement, "Name", values, 1);
			String script = GeneralImport.addField(csvElement, "Script",
					values, 2);
			String template = null;
			if (values.length > 3) {
				template = GeneralImport.addField(csvElement, "Template",
						values, 3);
			}
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
		Report report = (Report) Hiber.session()
				.createQuery("from Report report where report.name = :name")
				.setString("name", name).uniqueResult();
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

	public static Report insertReport(Long id, boolean isCore, String name,
			String script, String template) throws HttpException {
		Report report = new Report(id, isCore, name, script, template);
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

	public Report(Long id, boolean isCore, String name, String script,
			String template) throws HttpException {
		Configuration configuration = Configuration.getConfiguration();

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

	public void update(String name, String script, String template)
			throws HttpException {
		setName(name);
		try {
			PythonInterpreter interp = new PythonInterpreter();
			interp.compile(script);
			setScript(script);
		} catch (Throwable e) {
			throw new UserException(HttpException.getStackTraceString(e));
		}
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

	@SuppressWarnings("unchecked")
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

		ServletContext ctx = inv.getMonad().getServletConfig()
				.getServletContext();
		Map<Long, String> request_map = (Map<Long, String>) ctx
				.getAttribute(ContextListener.CONTEXT_REQUEST_MAP);
		request_map.put(
				Thread.currentThread().getId(),
				inv.getRequest()
						.getRequestURL()
						.append('?' + inv.getRequest().getQueryString() + ' '
								+ new MonadDate() + ' '
								+ inv.getRequest().getRemoteAddr()).toString());

		try {
			interp.exec(script);
		} catch (Throwable e) {
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
			try {
				update(name, script, template);
			} catch (UserException e) {
				e.setDocument(doc);
				throw e;
			}
			Hiber.commit();
			Element reportElement = toXml(doc);
			source.appendChild(reportElement);
			inv.sendOk(doc);
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "report");
		element.setAttribute("is-core",
				new Boolean(getId() % 2 == 1).toString());
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
