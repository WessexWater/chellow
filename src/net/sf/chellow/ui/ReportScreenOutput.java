package net.sf.chellow.ui;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
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

	public ReportScreenOutput(ReportScreen reportScreen) throws InternalException,
			HttpException {
		this.reportScreen = reportScreen;
	}
	
	public ReportScreen getReportScreen() {
		return reportScreen;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return reportScreen.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		try {
			//long startMillis = System.currentTimeMillis();
			//Debug.print("Start request: " + (System.currentTimeMillis() - startMillis));
			Document doc = MonadUtils.newSourceDocument();
			Element source = doc.getDocumentElement();
			Element reportElement = (Element) toXml(doc);
			source.appendChild(reportElement);
			reportScreen.run(inv, doc);
			//Debug.print("Created XML: " + (System.currentTimeMillis() - startMillis));
			inv.sendOk(doc, reportScreen.getTemplate().getUri().toString(),
					ReportTemplate.TEMPLATE_FILE_NAME);
			//Debug.print("Finished request: " + (System.currentTimeMillis() - startMillis));
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	private Document document() throws InternalException, HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
        Element outputElement = (Element) toXml(doc);
        source.appendChild(outputElement);
        Element screenElement = (Element) getReportScreen().toXml(doc);
        outputElement.appendChild(screenElement);
        Element reportElement = (Element) getReportScreen().getReport().toXml(doc);
        screenElement.appendChild(reportElement);
        Element reportsElement = (Element) getReportScreen().getReport().getReports().toXml(doc);
        reportElement.appendChild(reportsElement);
        Element organizationElement = (Element) getReportScreen().getReport().getReports().getOrganization().toXml(doc);
        reportsElement.appendChild(organizationElement);
		return doc;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = doc.createElement("screen-report-output");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
	
	public void run(Invocation inv, Document doc) throws InternalException,
	DesignerException, HttpException {
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
