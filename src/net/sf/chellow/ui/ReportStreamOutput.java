package net.sf.chellow.ui;

import java.io.IOException;
import java.io.PrintWriter;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.python.core.PyException;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ReportStreamOutput implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("output");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	private ReportStream reportStream;

	public ReportStreamOutput(ReportStream reportStream)
			throws InternalException, HttpException {
		this.reportStream = reportStream;
	}

	public ReportStream getReportStream() {
		return reportStream;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return reportStream.getUri().resolve(URI_ID).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		try {
			PythonInterpreter interp = new PythonInterpreter();
			interp.set("organization", reportStream.getReport().getReports()
					.getOrganization());
			interp.set("inv", inv);
			try {
				interp.execfile(reportStream.getScript().getInputStream());
			} catch (PyException e) {
				if (inv.getResponse().isCommitted()) {
					PrintWriter pw;
					try {
						pw = inv.getResponse().getWriter();
					} catch (IOException e1) {
						throw new InternalException(e1);
					}
					pw.append(e.toString());
					pw.close();
				} else {
					inv.getResponse().setContentType("text/html");
					Object obj = e.value.__tojava__(HttpException.class);
					if (obj instanceof HttpException) {
						throw (HttpException) obj;
					} else {
						throw new UserException(e.toString());
					}
				}
			}
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
		Element screenElement = (Element) getReportStream().toXml(doc);
		outputElement.appendChild(screenElement);
		Element reportElement = (Element) getReportStream().getReport().toXml(
				doc);
		screenElement.appendChild(reportElement);
		Element reportsElement = (Element) getReportStream().getReport()
				.getReports().toXml(doc);
		reportElement.appendChild(reportsElement);
		Element organizationElement = (Element) getReportStream().getReport()
				.getReports().getOrganization().toXml(doc);
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
		Element element = doc.createElement("stream-report-output");
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
		 * PythonInterpreter interp = new PythonInterpreter(); Element source =
		 * doc.getDocumentElement(); interp.set("doc", doc);
		 * interp.set("source", source); interp.set("organization",
		 * report.getReports().getOrganization()); interp.set("inv", inv);
		 * StringWriter out = new StringWriter(); interp.setOut(out);
		 * StringWriter err = new StringWriter(); interp.setErr(err); try {
		 * interp.execfile(reportScript.getInputStream()); } catch (PyException
		 * e) { inv.getResponse().setContentType("text/html"); Object obj =
		 * e.value.__tojava__(UserException.class); if (obj instanceof
		 * UserException) { throw (UserException) obj; } else { throw
		 * UserException.newInvalidParameter(e.toString()); } } if
		 * (out.toString().length() > 0) { source.appendChild(new
		 * VFMessage(out.toString()).toXML(doc)); } if (err.toString().length() >
		 * 0) { source.appendChild(new VFMessage(err.toString()).toXML(doc)); }
		 */
	}
}
