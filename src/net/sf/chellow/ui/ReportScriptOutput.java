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

public class ReportScriptOutput implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("script-output");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private ReportScreen reportScreen;

	public ReportScriptOutput(ReportScreen reportScreen)
			throws ProgrammerException, UserException {
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
		Document doc = MonadUtils.newSourceDocument();
		try {
			reportScreen.run(inv, doc);
			inv.sendOk(doc, null,
					null);
		} catch (UserException e) {
			e.setDocument(document());
			throw e;
		}
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element scriptOutputElement = (Element) toXML(doc);
		source.appendChild(scriptOutputElement);
		Element screenElement = (Element) getReportScreen().toXML(doc);
		scriptOutputElement.appendChild(screenElement);
		Element reportElement = (Element) getReportScreen().getReport().toXML(
				doc);
		screenElement.appendChild(reportElement);
		Element reportsElement = (Element) getReportScreen().getReport()
				.getReports().toXML(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReportScreen().getReport()
				.getReports().getOrganization().toXML(doc);
		reportsElement.appendChild(organizationElement);
		return doc;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws ProgrammerException, UserException,
			DesignerException {
		Element element = doc.createElement("report-script-output");
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}