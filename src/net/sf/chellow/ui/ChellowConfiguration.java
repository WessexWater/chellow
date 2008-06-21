package net.sf.chellow.ui;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.Properties;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.InternalException;

public class ChellowConfiguration {
	private static File configurationDirectory = null;

	public static void setConfigurationDirectory(ServletContext context, String configDirStr) {
		File directory = new File(configDirStr);
		
		if (!directory.isAbsolute()) {
			directory = new File(context.getRealPath("") + File.separator + configDirStr);
		}
		configurationDirectory = directory;
	}

	public static File getConfigurationDirectory() {
		return configurationDirectory;
	}

	public static String getChellowProperty(String name)
			throws InternalException {
		Properties chellowProperties = new Properties();
		String value = null;
		try {
			FileInputStream is = new FileInputStream(configurationDirectory
					+ File.separator + "chellow.properties");
			chellowProperties.load(is);
			is.close();
		} catch (FileNotFoundException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
		value = chellowProperties.getProperty(name);
		return value;
	}

	public static String getOverrideProperty(String name, String defaultValue)
			throws InternalException {
		String overrideFileName = getChellowProperty("overrideFile");
		if (overrideFileName == null) {
			return defaultValue;
		}
		Properties overrideProperties = new Properties();
		File overrideFile = new File(overrideFileName);
		if (overrideFile.exists()) {
			try {
				FileInputStream is = new FileInputStream(overrideFile);
				overrideProperties.load(is);
				is.close();
			} catch (FileNotFoundException e) {
				throw new InternalException(e);
			} catch (IOException e) {
				throw new InternalException(e);
			}
			return overrideProperties.getProperty(name, defaultValue);
		} else {
			return defaultValue;
		}
	}
}