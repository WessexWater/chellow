package net.sf.chellow.ui;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.io.Writer;
import java.net.URISyntaxException;
import java.net.URL;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ReportTemplate implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static final String TEMPLATE_FILE_NAME = "report-template.xsl";
	static {
		try {
			URI_ID = new UriPathElement("template");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private ReportScreen report;

	public ReportTemplate(ReportScreen report) throws InternalException,
			HttpException {
		this.report = report;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}
	
	public ReportScreen getReportScreen() {
		return report;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return report.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element templateElement = (Element) toXml(doc); 
		source.appendChild(templateElement);
		Element screenElement = (Element) getReportScreen().toXml(doc);
		templateElement.appendChild(screenElement);
		Element reportElement = (Element) getReportScreen().getReport().toXml(doc);
		screenElement.appendChild(reportElement);
		Element reportsElement = (Element) getReportScreen().getReport().getReports().toXml(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReportScreen().getReport().getReports().getOrganization().toXml(doc);
		reportsElement.appendChild(organizationElement);
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		MonadString templateText = inv.getMonadString("template-text");
		URL templateUrl = Monad.getConfigResource(getUri().append(
				TEMPLATE_FILE_NAME));
		Reader isr = null;
		Writer osr = null;
		try {
			isr = new StringReader(templateText.getString());
			osr = new FileWriter(new File(templateUrl.toURI()));
			int c;
			while ((c = isr.read()) != -1) {
				osr.write(c);
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		} finally {
			try {
				if (isr != null) {
					isr.close();
				}
				if (osr != null) {
					osr.close();
				}
			} catch (IOException e) {
				throw new InternalException(e);
			}
		}
		inv.sendSeeOther(getUri());
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws InternalException, HttpException,
			DesignerException {
		Element element = doc.createElement("template");
		InputStreamReader inputStream = null;
		StringWriter stringWriter = null;
		try {
			inputStream = new InputStreamReader(Monad.getConfigIs(getUri()
					.toString(), TEMPLATE_FILE_NAME), "UTF-8");
			stringWriter = new StringWriter();
			int c;
			while ((c = inputStream.read()) != -1) {
				stringWriter.write(c);
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} finally {
			try {
				if (inputStream != null) {
					inputStream.close();
				}
				if (stringWriter != null) {
					stringWriter.close();
				}
			} catch (IOException e) {
				throw new InternalException(e);
			}
		}
		element.setTextContent(stringWriter.toString().replace("\r", "")
				.replace("\t", "    "));
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
