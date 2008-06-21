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
			throws InternalException, HttpException {
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
		Document doc = MonadUtils.newSourceDocument();
		try {
			reportScreen.run(inv, doc);
			inv.sendOk(doc, null,
					null);
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element scriptOutputElement = (Element) toXml(doc);
		source.appendChild(scriptOutputElement);
		Element screenElement = (Element) getReportScreen().toXml(doc);
		scriptOutputElement.appendChild(screenElement);
		Element reportElement = (Element) getReportScreen().getReport().toXml(
				doc);
		screenElement.appendChild(reportElement);
		Element reportsElement = (Element) getReportScreen().getReport()
				.getReports().toXml(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReportScreen().getReport()
				.getReports().getOrganization().toXml(doc);
		reportsElement.appendChild(organizationElement);
		return doc;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException,
			DesignerException {
		Element element = doc.createElement("report-script-output");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}