package net.sf.chellow.ui;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
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

	public ReportStream(Report report) throws HttpException {
		this.report = report;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (ReportScript.URI_ID.equals(uriId)) {
			return reportScript;
		} else if (ReportStreamOutput.URI_ID.equals(uriId)) {
			return new ReportStreamOutput(this);
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

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element streamElement = toXml(doc);
		source.appendChild(streamElement);
		Element reportElement = report.toXml(doc);
		streamElement.appendChild(reportElement);
		Element reportsElement = report.getReports().toXml(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = report.getReports()
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

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("stream-report");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		return null;
	}

	ReportScript getScript() {
		return reportScript;
	}

	public Report getReport() {
		return report;
	}
}