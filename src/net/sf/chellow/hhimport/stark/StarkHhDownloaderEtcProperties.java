package net.sf.chellow.hhimport.stark;

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.ChellowProperties;

public class StarkHhDownloaderEtcProperties extends ChellowProperties {
	public StarkHhDownloaderEtcProperties(MonadUri uri) throws ProgrammerException, UserException {
		super(uri, "etc.properties");
	}

	public String getHostname() throws ProgrammerException {
		return getProperty("hostname");
	}

	public String getUsername() throws ProgrammerException {
		return getProperty("username");
	}

	public String getPassword() throws ProgrammerException {
		return getProperty("password");
	}

	public List<String> getDirectories() throws ProgrammerException {
		List<String> directories = new ArrayList<String>();
		String directory = null;
		for (int i = 0; (directory = getProperty("directory" + i)) != null; i++) {
			directories.add(directory);
		}
		return directories;
	}
}
