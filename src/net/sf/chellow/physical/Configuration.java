/*******************************************************************************
 * 
 *  Copyright (c) 2005-2014 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/
package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.text.DecimalFormat;
import java.util.Properties;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.MonadUtils;
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

	static public Configuration getConfiguration() {
		Configuration config = (Configuration) Hiber.session()
				.createQuery("from Configuration").uniqueResult();
		if (config == null) {
			config = new Configuration("");
			Hiber.setReadWrite();
			Hiber.session().save(config);
			Hiber.flush();
		}
		return config;
	}

	private String properties;

	private long coreReportId;

	private long userReportId;

	public Configuration() {
	}

	public Configuration(String properties) {
		setId(0L);
		setProperties(properties);
		setCoreReportId(1);
		setUserReportId(0);
	}

	public String getProperties() {
		return properties;
	}

	void setProperties(String properties) {
		this.properties = properties;
	}

	public long getCoreReportId() {
		return coreReportId;
	}

	public void setCoreReportId(long id) {
		coreReportId = id;
	}

	public long getUserReportId() {
		return userReportId;
	}

	public void setUserReportId(long id) {
		userReportId = id;
	}

	public void update(String properties) throws HttpException {
		Properties props = new Properties();
		try {
			props.load(new StringReader(properties));
			setProperties(properties);
		} catch (IOException e) {
			throw new InternalException(e);
		}
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

	public long nextCoreReportId() {
		coreReportId += 2;
		return coreReportId;
	}

	public long nextUserReportId() {
		userReportId += 2;
		return userReportId;
	}


	public MonadUri getEditUri() {
		return null;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("configuration");
		try {
			Reader is = new InputStreamReader(Monad.getContext()
					.getResource("/WEB-INF/VERSION").openStream(), "UTF-8");
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

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		String properties = inv.getString("properties");
		if (!inv.isValid()) {
			throw new UserException();
		}
		properties = properties.replace("\r", "").replace("\t", "    ");

		Element propertiesElement = doc.createElement("properties");
		source.appendChild(propertiesElement);
		propertiesElement.setTextContent(properties);

		try {
			update(properties);
		} catch (UserException e) {
			e.setDocument(doc);
			throw e;
		}
		Hiber.commit();
		Element configElement = toXml(doc);
		source.appendChild(configElement);
		inv.sendOk(doc);
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element configElement = toXml(doc);
		source.appendChild(configElement);
		DecimalFormat df = new DecimalFormat("###,###,###,###,##0");
		Runtime runtime = Runtime.getRuntime();
		source.setAttribute("free-memory", df.format(runtime.freeMemory()));
		source.setAttribute("max-memory", df.format(runtime.maxMemory()));
		source.setAttribute("total-memory", df.format(runtime.totalMemory()));
		return doc;
	}
}
