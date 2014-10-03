/*******************************************************************************
 * 
 *  Copyright (c) Wessex Water Services Limited
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

import java.io.StringWriter;
import java.net.URI;
import java.util.Map;

import javax.servlet.ServletContext;

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
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.PersistentEntity;

import org.hibernate.exception.ConstraintViolationException;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Report extends PersistentEntity implements Urlable {

	public static Report findReport(Long id) throws HttpException {
		return (Report) Hiber.session().get(Report.class, id);
	}

	public static Report getReport(Long id) throws HttpException {
		Report report = findReport(id);
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

	public static Report insertReport(Long id, boolean isCore, String name,
			String script, String template) throws HttpException {
		Report report = new Report(id, isCore, name, script, template);
		try {
			Hiber.session().save(report);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			Hiber.rollBack();
			throw new UserException("There's already a report with that name."
					+ UserException.getStackTraceString(e));
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

		try {
			Element source = doc.getDocumentElement();
			interp.set("doc", doc);
			interp.set("source", source);
			interp.set("inv", inv);
			interp.set("template", getTemplate());
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
							.append('?' + inv.getRequest().getQueryString()
									+ ' ' + new MonadDate() + ' '
									+ inv.getRequest().getRemoteAddr())
							.toString());
			Hiber.close();
			interp.exec(script);
		} catch (Throwable e) {
			throw new UserException(e.getMessage() + " "
					+ HttpException.getStackTraceString(e));
		} finally {
			interp.cleanup();
		}
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.REPORTS_INSTANCE.getEditUri().resolve(getId())
				.append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportElement = toXml(doc);
		source.appendChild(reportElement);
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		Hiber.session().setReadOnly(this, false);
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendFound(Chellow.REPORTS_INSTANCE.getEditUri());
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
		Element element = doc.createElement("report");

		element.setAttribute("id", getId().toString());

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

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
