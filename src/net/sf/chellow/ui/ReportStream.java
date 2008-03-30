package net.sf.chellow.ui;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ReportStream implements ReportType {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("stream");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private Report report;

	private ReportScript reportScript = new ReportScript(this);

	public ReportStream(Report report) throws ProgrammerException,
			UserException {
		this.report = report;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (ReportScript.URI_ID.equals(uriId)) {
			return reportScript;
		} else if (ReportStreamOutput.URI_ID.equals(uriId)) {
			return new ReportStreamOutput(this);
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

	private Document document() throws ProgrammerException, UserException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element streamElement = (Element) toXML(doc);
		source.appendChild(streamElement);
		Element reportElement = (Element) report.toXML(doc);
		streamElement.appendChild(reportElement);
		Element reportsElement = (Element) report.getReports().toXML(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) report.getReports()
				.getOrganization().toXML(doc);
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
		Element element = doc.createElement("stream-report");
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	ReportScript getScript() {
		return reportScript;
	}

	public Report getReport() {
		return report;
	}
}