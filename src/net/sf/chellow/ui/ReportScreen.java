package net.sf.chellow.ui;

import java.io.StringWriter;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ReportScreen implements ReportType {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("screen");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Report report;

	private ReportTemplate reportTemplate = new ReportTemplate(this);

	private ReportScript reportScript = new ReportScript(this);

	public ReportScreen(Report report) throws HttpException {
		this.report = report;
	}

	public Report getReport() {
		return report;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (ReportTemplate.URI_ID.equals(uriId)) {
			return reportTemplate;
		} else if (ReportScript.URI_ID.equals(uriId)) {
			return reportScript;
		} else if (ReportXmlOutput.URI_ID.equals(uriId)) {
			return new ReportXmlOutput(this);
		} else if (ReportOutput.URI_ID.equals(uriId)) {
			return new ReportOutput(this);
		} else {
			return null;
		}
	}

	public MonadUri getUri() throws HttpException {
		return report.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	ReportTemplate getTemplate() {
		return reportTemplate;
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element screenElement = (Element) toXml(doc);
		source.appendChild(screenElement);
		Element reportElement = (Element) getReport().toXml(doc);
		screenElement.appendChild(reportElement);
		Element reportsElement = (Element) getReport().getReports().toXml(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReport().getReports()
				.getOrganization().toXml(doc);
		reportsElement.appendChild(organizationElement);
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = doc.createElement("screen-report");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		return null;
	}

	public void run(Invocation inv, Document doc) throws HttpException {
		PythonInterpreter interp = new PythonInterpreter();
		Element source = doc.getDocumentElement();
		interp.set("doc", doc);
		interp.set("source", source);
		interp.set("organization", report.getReports().getOrganization());
		interp.set("inv", inv);
		StringWriter out = new StringWriter();
		interp.setOut(out);
		StringWriter err = new StringWriter();
		interp.setErr(err);
		try {
			interp.execfile(reportScript.getInputStream());
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
}
