package net.sf.chellow.physical;

import java.io.IOException;
import java.io.StringReader;
import java.util.Properties;

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class Configuration extends PersistentEntity {
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
		.createQuery("from DatabaseVersion").uniqueResult();
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

	public Urlable getChild(UriPathElement uriId) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException, InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	public void httpPost(Invocation inv) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		
	}

	public void httpDelete(Invocation inv) throws InternalException, DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		// TODO Auto-generated method stub
		return null;
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