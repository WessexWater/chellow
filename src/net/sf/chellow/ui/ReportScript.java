package net.sf.chellow.ui;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
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

public class ReportScript implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	private static final String REPORT_FILE_NAME = "report.py";

	static {
		try {
			URI_ID = new UriPathElement("script");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private ReportType reportType;

	public ReportScript(ReportType reportType) throws InternalException,
			HttpException {
		this.reportType = reportType;
	}
	
	public ReportType getReportType() {
		return reportType;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return reportType.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element scriptElement = (Element) toXml(doc);
		source.appendChild(scriptElement);
		Element typeElement = (Element) getReportType().toXml(doc);
		scriptElement.appendChild(typeElement);
		Element reportElement = (Element) getReportType().getReport().toXml(doc);
		typeElement.appendChild(reportElement);
		Element reportsElement = (Element) getReportType().getReport().getReports().toXml(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReportType().getReport().getReports().getOrganization().toXml(doc);
		reportsElement.appendChild(organizationElement);
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		MonadString scriptText = inv.getMonadString("script-text");
		URL scriptUrl = Monad.getConfigResource(getUri().append(
				REPORT_FILE_NAME));
		Reader isr = null;
		Writer osr = null;
		try {
			isr = new StringReader(scriptText.getString());
			osr = new FileWriter(new File(scriptUrl.toURI()));
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

	Reader getReader() throws InternalException, DesignerException,
			HttpException {
		try {
			return new InputStreamReader(getInputStream(), "UTF-8");
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		}
	}

	InputStream getInputStream() throws InternalException, DesignerException,
			HttpException {
		return Monad.getConfigIs(getUri().toString(), REPORT_FILE_NAME);
	}

	public Node toXml(Document doc) throws InternalException, HttpException,
			DesignerException {
		Element element = doc.createElement("report-script");
		Reader reader = null;
		StringWriter stringWriter = null;
		try {
			reader = getReader();
			stringWriter = new StringWriter();
			int c;
			while ((c = reader.read()) != -1) {
				stringWriter.write(c);
			}
		} catch (IOException e) {
			throw new InternalException(e);
		} finally {
			try {
				if (reader != null) {
					reader.close();
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