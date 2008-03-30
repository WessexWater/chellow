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
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

public class ChellowProperties {
	static private File getPropertiesFile(MonadUri uri, String fileName)
			throws ProgrammerException {
		if (uri == null) {
			throw new ProgrammerException("The uri parameter can't be null.");
		}
		return new File(ChellowConfiguration.getConfigurationDirectory()
				.toString()
				+ uri.toString().replace("/", File.separator)
				+ File.separator
				+ fileName);
	}

	static private URL getPropertiesUrl(MonadUri uri, String fileName)
			throws ProgrammerException {
		if (uri == null) {
			throw new ProgrammerException("The uri parameter can't be null.");
		}
		try {
			return Monad.getContext().getResource(
					Monad.getConfigPrefix() + uri.toString() + fileName);
		} catch (MalformedURLException e) {
			throw new ProgrammerException(e);
		}
	}

	static public boolean propertiesExists(MonadUri uri, String fileName)
			throws ProgrammerException {
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
			throws ProgrammerException, UserException {
		propertiesFile = getPropertiesFile(uri, fileName);
		if (!propertiesExists(propertiesFile)) {
			propertiesFile = null;
			propertiesUrl = getPropertiesUrl(uri, fileName);
			if (propertiesUrl == null) {
				throw UserException.newNotFound();
			}
		}
	}

	public ChellowProperties(MonadUri uri) throws UserException,
			ProgrammerException {
		this(uri, "config.properties");
	}

	protected Properties getProperties() throws ProgrammerException {
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
			throw new ProgrammerException(e);
		} catch (FileNotFoundException e) {
			throw new ProgrammerException(e);
		} catch (IOException e) {
			throw new ProgrammerException(e);
		}
		return properties;
	}

	protected String getProperty(String name) throws ProgrammerException {
		String value = getProperties().getProperty(name);
		if (value == null) {
			return null;
		}
		return ChellowConfiguration.getOverrideProperty(value, value);
	}

	protected void setProperty(String name, String value)
			throws ProgrammerException {
		Properties properties = getProperties();
		properties.setProperty(name, value);
		if (!propertiesFile.exists()) {
			throw new ProgrammerException("The properties file '"
					+ propertiesFile.toString() + "'.");
		}
		try {
			FileOutputStream os = new FileOutputStream(propertiesFile);
			properties.store(os, null);
			os.close();
		} catch (FileNotFoundException e) {
			throw new ProgrammerException(e);
		} catch (IOException e) {
			throw new ProgrammerException(e);
		}
	}

	public long getLastModified() {
		return lastModified;
	}
}