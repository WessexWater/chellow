package net.sf.chellow.ui;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Report extends PersistentEntity {
	private String name;

	private String script;
	
	private String template;

	public Report(String name, String script, String template) throws HttpException {
		update(name, script, template);
	}
	
	public String getName() {
		return name;
	}
	
	void setName(String name) {
		this.name = name;
	}
	
	public String getScript() {
		return script;
	}
	
	void setScript(String script) {
		this.script = script;
	}
	
	public String getTemplate() {
		return template;
	}
	
	void setTemplate(String template) {
		this.template = template;
	}
	
	private void update(String name, String script, String template) {
		setName(name);
		setScript(script);
		setTemplate(template);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
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

	public MonadUri getUri() throws HttpException {
		return reportsInstance().getUri().resolve(getId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element reportElement = toXml(doc);
		source.appendChild(reportElement);
		reportElement.appendChild(reports.getOrganization().toXml(doc));
		return doc;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "report");
		element.setAttribute("name", "name");
		element.setAttribute("script", script);
		if (template != null) {
			element.setAttribute("template", template);
		}
		return element;
	}
}