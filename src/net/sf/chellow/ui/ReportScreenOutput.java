package net.sf.chellow.ui;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ReportScreenOutput implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("output");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private ReportScreen reportScreen;

	public ReportScreenOutput(ReportScreen reportScreen) throws ProgrammerException,
			UserException {
		this.reportScreen = reportScreen;
	}
	
	public ReportScreen getReportScreen() {
		return reportScreen;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return reportScreen.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		try {
			//long startMillis = System.currentTimeMillis();
			//Debug.print("Start request: " + (System.currentTimeMillis() - startMillis));
			Document doc = MonadUtils.newSourceDocument();
			Element source = doc.getDocumentElement();
			Element reportElement = (Element) toXML(doc);
			source.appendChild(reportElement);
			reportScreen.run(inv, doc);
			//Debug.print("Created XML: " + (System.currentTimeMillis() - startMillis));
			inv.sendOk(doc, reportScreen.getTemplate().getUri().toString(),
					ReportTemplate.TEMPLATE_FILE_NAME);
			//Debug.print("Finished request: " + (System.currentTimeMillis() - startMillis));
		} catch (UserException e) {
			e.setDocument(document());
			throw e;
		}
	}

	private Document document() throws ProgrammerException, UserException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
        Element outputElement = (Element) toXML(doc);
        source.appendChild(outputElement);
        Element screenElement = (Element) getReportScreen().toXML(doc);
        outputElement.appendChild(screenElement);
        Element reportElement = (Element) getReportScreen().getReport().toXML(doc);
        screenElement.appendChild(reportElement);
        Element reportsElement = (Element) getReportScreen().getReport().getReports().toXML(doc);
        reportElement.appendChild(reportsElement);
        Element organizationElement = (Element) getReportScreen().getReport().getReports().getOrganization().toXML(doc);
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
		Element element = doc.createElement("screen-report-output");
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
	
	public void run(Invocation inv, Document doc) throws ProgrammerException,
	DesignerException, UserException {
		/*
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
*/
}
}
