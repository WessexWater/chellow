package net.sf.chellow.hhimport.stark;

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.ChellowProperties;

public class StarkHhDownloaderEtcProperties extends ChellowProperties {
	public StarkHhDownloaderEtcProperties(MonadUri uri) throws InternalException, HttpException {
		super(uri, "etc.properties");
	}

	public String getHostname() throws InternalException {
		return getProperty("hostname");
	}

	public String getUsername() throws InternalException {
		return getProperty("username");
	}

	public String getPassword() throws InternalException {
		return getProperty("password");
	}

	public List<String> getDirectories() throws InternalException {
		List<String> directories = new ArrayList<String>();
		String directory = null;
		for (int i = 0; (directory = getProperty("directory" + i)) != null; i++) {
			directories.add(directory);
		}
		return directories;
	}
}
