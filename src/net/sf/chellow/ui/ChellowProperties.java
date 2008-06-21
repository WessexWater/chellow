package net.sf.chellow.ui;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.util.InvalidPropertiesFormatException;
import java.util.Properties;

import net.sf.chellow.monad.Monad;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadUri;

public class ChellowProperties {
	static private File getPropertiesFile(MonadUri uri, String fileName)
			throws InternalException {
		if (uri == null) {
			throw new InternalException("The uri parameter can't be null.");
		}
		return new File(ChellowConfiguration.getConfigurationDirectory()
				.toString()
				+ uri.toString().replace("/", File.separator)
				+ File.separator
				+ fileName);
	}

	static private URL getPropertiesUrl(MonadUri uri, String fileName)
			throws InternalException {
		if (uri == null) {
			throw new InternalException("The uri parameter can't be null.");
		}
		try {
			return Monad.getContext().getResource(
					Monad.getConfigPrefix() + uri.toString() + fileName);
		} catch (MalformedURLException e) {
			throw new InternalException(e);
		}
	}

	static public boolean propertiesExists(MonadUri uri, String fileName)
			throws InternalException {
		File propertiesFile = getPropertiesFile(uri, fileName);
		if (propertiesExists(propertiesFile)) {
			return true;
		} else {
			return getPropertiesUrl(uri, fileName) != null;
		}
	}

	static public boolean propertiesExists(File propertiesFile) {
		return propertiesFile.exists() && propertiesFile.isFile();
	}

	private Properties properties = new Properties();

	private long lastModified = 0;

	private long urlLastModified = 0;

	private File propertiesFile;

	private URL propertiesUrl;

	public ChellowProperties(MonadUri uri, String fileName)
			throws InternalException, HttpException {
		propertiesFile = getPropertiesFile(uri, fileName);
		if (!propertiesExists(propertiesFile)) {
			propertiesFile = null;
			propertiesUrl = getPropertiesUrl(uri, fileName);
			if (propertiesUrl == null) {
				throw new NotFoundException();
			}
		}
	}

	public ChellowProperties(MonadUri uri) throws HttpException,
			InternalException {
		this(uri, "config.properties");
	}

	protected Properties getProperties() throws InternalException {
		try {
			InputStream is = null;
			if (propertiesFile != null) {
				if (propertiesFile.lastModified() > lastModified) {
					is = new FileInputStream(propertiesFile);
					lastModified = propertiesFile.lastModified();
				}
			} else {
				URLConnection con = propertiesUrl.openConnection();
				if (con.getLastModified() > urlLastModified) {
					is = con.getInputStream();
					urlLastModified = con.getLastModified();
				}
			}
			if (is != null) {
				properties = new Properties();
				properties.load(is);
				is.close();
			}
		} catch (InvalidPropertiesFormatException e) {
			throw new InternalException(e);
		} catch (FileNotFoundException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
		return properties;
	}

	protected String getProperty(String name) throws InternalException {
		String value = getProperties().getProperty(name);
		if (value == null) {
			return null;
		}
		return ChellowConfiguration.getOverrideProperty(value, value);
	}

	protected void setProperty(String name, String value)
			throws InternalException {
		Properties properties = getProperties();
		properties.setProperty(name, value);
		if (!propertiesFile.exists()) {
			throw new InternalException("The properties file '"
					+ propertiesFile.toString() + "'.");
		}
		try {
			FileOutputStream os = new FileOutputStream(propertiesFile);
			properties.store(os, null);
			os.close();
		} catch (FileNotFoundException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public long getLastModified() {
		return lastModified;
	}
}