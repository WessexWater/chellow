package net.sf.chellow.physical;

import java.io.IOException;
import java.io.StringReader;
import java.util.Properties;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
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

	private String implicitUserProperties;

	private String chellowProperties;

	public Configuration() {
	}

	int getVersion() {
		return version;
	}

	void setVersion(int version) {
		this.version = version;
	}

	public String getImplicitUserProperties() {
		return implicitUserProperties;
	}

	void setImplicitUserProperties(String implicitUserProperties) {
		this.implicitUserProperties = implicitUserProperties;
	}

	public String getChellowProperties() {
		return chellowProperties;
	}

	void setChellowProperties(String chellowProperties) {
		this.chellowProperties = chellowProperties;
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
		String implicitUserProperties = inv
				.getString("implicit-user-properties");
		String chellowProperties = inv.getString("chellow-properties");
		if (!inv.isValid()) {
			throw new UserException();
		}
		update(implicitUserProperties, chellowProperties);
		Hiber.commit();
		inv.sendOk(document());
	}

	public void update(String implicitUserProperties, String chellowProperties)
			throws HttpException {
		Properties impProps = new Properties();
		Properties chellowProps = new Properties();
		try {
			impProps.load(new StringReader(implicitUserProperties));
			setImplicitUserProperties(implicitUserProperties);
			chellowProps.load(new StringReader(chellowProperties));
			setChellowProperties(chellowProperties);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	@Override
	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("configuration");
		element.setAttribute("version", Integer.toString(version));
		Element impProps = doc.createElement("implicit-user-properties");
		element.appendChild(impProps);
		impProps.setTextContent(implicitUserProperties);
		Element chellowProps = doc.createElement("chellow-properties");
		element.appendChild(chellowProps);
		chellowProps.setTextContent(chellowProperties);
		return element;
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element configElement = toXml(doc);
		source.appendChild(configElement);
		return doc;
	}

	public String getChellowProperty(String name) throws HttpException {
		Properties props = new Properties();
		try {
			props.load(new StringReader(chellowProperties));
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return props.getProperty(name);
	}
}