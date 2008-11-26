package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.util.Properties;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Configuration extends PersistentEntity {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("configuration");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	static public void setDatabaseVersion(int version) {
		Configuration configuration = getConfiguration();
		if (configuration == null) {
			configuration = new Configuration();
			configuration.setVersion(version);
			configuration.setProperties("");
			Hiber.session().save(configuration);
			Hiber.flush();
		} else {
			configuration.setVersion(version);
			Hiber.flush();
		}
	}

	static public Configuration getConfiguration() {
		return (Configuration) Hiber.session()
				.createQuery("from Configuration").uniqueResult();
	}

	private int version;

	private String properties;

	public Configuration() {
	}

	int getVersion() {
		return version;
	}

	void setVersion(int version) {
		this.version = version;
	}

	public String getProperties() {
		return properties;
	}

	void setProperties(String properties) {
		this.properties = properties;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		String properties = inv.getString("properties");
		if (!inv.isValid()) {
			throw new UserException();
		}
		update(properties);
		Hiber.commit();
		inv.sendOk(document());
	}

	public void update(String properties)
			throws HttpException {
		Properties props = new Properties();
		try {
			props.load(new StringReader(properties));
			setProperties(properties);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	@Override
	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("configuration");
		element.setAttribute("db-version", Integer.toString(version));
		try {
			Reader is = new InputStreamReader(Monad.getContext().getResource(
					"/WEB-INF/VERSION").openStream(), "UTF-8");
			int c;
			StringWriter sr = new StringWriter();
			while ((c = is.read()) != -1) {
				sr.write(c);
			}
			element.setAttribute("version", sr.toString());
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
		Element propsElement = doc.createElement("properties");
		element.appendChild(propsElement);
		propsElement.setTextContent(properties);
		return element;
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element configElement = toXml(doc);
		source.appendChild(configElement);
		return doc;
	}

	public String getProperty(String name) throws HttpException {
		Properties props = new Properties();
		try {
			props.load(new StringReader(properties));
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return props.getProperty(name);
	}
}