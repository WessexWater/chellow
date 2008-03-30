package net.sf.chellow.ui;

import java.io.StringWriter;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.python.core.PyException;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ReportScreen implements ReportType {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("screen");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	private Report report;

	private ReportTemplate reportTemplate = new ReportTemplate(this);

	private ReportScript reportScript = new ReportScript(this);

	public ReportScreen(Report report) throws ProgrammerException,
			UserException {
		this.report = report;
	}
	
	public Report getReport() {
		return report;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (ReportTemplate.URI_ID.equals(uriId)) {
			return reportTemplate;
		} else if (ReportScript.URI_ID.equals(uriId)) {
			return reportScript;
		} else if (ReportScriptOutput.URI_ID.equals(uriId)) {
			return new ReportScriptOutput(this);
		} else if (ReportScreenOutput.URI_ID.equals(uriId)) {
			return new ReportScreenOutput(this);
		} else {
			return null;
		}
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return report.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	ReportTemplate getTemplate() {
		return reportTemplate;
	}

	private Document document() throws ProgrammerException, UserException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element screenElement = (Element) toXML(doc);
		source.appendChild(screenElement);
		Element reportElement = (Element) getReport().toXML(doc);
		screenElement.appendChild(reportElement);
		Element reportsElement = (Element) getReport().getReports().toXML(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReport().getReports().getOrganization().toXML(doc);
		reportsElement.appendChild(organizationElement);
		return doc;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = doc.createElement("screen-report");
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void run(Invocation inv, Document doc) throws ProgrammerException,
			DesignerException, UserException {
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
		} catch (PyException e) {
			inv.getResponse().setContentType("text/html");
			Object obj = e.value.__tojava__(UserException.class);
			if (obj instanceof UserException) {
				throw (UserException) obj;
			} else {
				throw UserException.newInvalidParameter(e.toString());
			}
		}
		if (out.toString().length() > 0) {
			source.appendChild(new VFMessage(out.toString()).toXML(doc));
		}
		if (err.toString().length() > 0) {
			source.appendChild(new VFMessage(err.toString()).toXML(doc));
		}
	}
}
