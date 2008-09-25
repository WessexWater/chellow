package net.sf.chellow.ui;

import java.io.StringWriter;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.PersistentEntity;

import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Report extends PersistentEntity {
	public static Report getReport(Long id) throws HttpException {
		Report report = (Report) Hiber.session().get(Report.class, id);
		if (report == null) {
			throw new NotFoundException("The report " + id + " can't be found.");
		}
		return report;
	}
	private String name;

	private String script;
	
	private String template;

	public Report(String name, String script, String template) throws HttpException {
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
	
	private void update(String name, String script, String template) {
		setName(name);
		setScript(script);
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
		} catch (PyException e) {
			inv.getResponse().setContentType("text/html");
			Object obj = e.value.__tojava__(HttpException.class);
			if (obj instanceof HttpException) {
				throw (HttpException) obj;
			} else {
				throw new UserException(e.toString());
			}
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
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportElement = toXml(doc);
		source.appendChild(reportElement);
		return doc;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "report");
		element.setAttribute("name", "name");
		element.setAttribute("script", script);
		if (template != null) {
			element.setAttribute("template", template);
		}
		return element;
	}
}