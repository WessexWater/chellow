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

public class Report implements Urlable, XmlDescriber {
	private Long id;

	private Reports reports;

	private ChellowProperties properties;

	

	public Report(Reports reports, Long id, MonadUri uri)
			throws ProgrammerException, UserException {
		this.id = id;
		this.reports = reports;
		if (ChellowProperties.propertiesExists(uri, "report.properties")) {
			properties = new ChellowProperties(uri, "report.properties");
		} else {
			throw UserException
					.newInvalidParameter("Can't find the 'report.properties' file at "
							+ uri + ".");
		}
	}

	public Reports getReports() {
		return reports;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (ReportScreen.URI_ID.equals(uriId)) {
			return new ReportScreen(this);
			/*
		} else if (ReportTemplate.URI_ID.equals(uriId)) {
//			return reportTemplate;
		} else if (ReportScript.URI_ID.equals(uriId)) {
//			return reportScript;
 * 
 */
		} else if (ReportStream.URI_ID.equals(uriId)) {
			return new ReportStream(this);
		} else {
			return null;
		}
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return reports.getUri().resolve(id).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	private Document document() throws ProgrammerException, UserException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportElement = (Element) toXML(doc);
		source.appendChild(reportElement);
		reportElement.appendChild(reports.getOrganization().toXML(doc));
		return doc;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = doc.createElement("report");
		element.setAttribute("name", properties.getProperty("name"));
		element.setAttribute("id", id.toString());
		return element;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}
