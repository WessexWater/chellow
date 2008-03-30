package net.sf.chellow.hhimport.stark;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.ChellowProperties;

public class StarkHhDownloaderVarProperties extends ChellowProperties {
	public StarkHhDownloaderVarProperties(MonadUri uri) throws ProgrammerException, UserException {
		super(uri, "var.properties");
	}
private String getPropertyNameLastImportDate(int directory) {
	return "lastImportDate" + directory;
}
private String getPropertyNameLastImportName(int directory) {
	return "lastImportName" + directory;
}
	public MonadDate getLastImportDate(int directory) throws ProgrammerException {
		String lastImportDateStr = getProperty(getPropertyNameLastImportDate(directory));
		MonadDate lastImportDate = null;
		if (lastImportDateStr != null && lastImportDateStr.length() != 0) {
			try {
				lastImportDate = new MonadDate(lastImportDateStr);
			} catch (UserException e) {
				throw new ProgrammerException(lastImportDateStr + e.getMessage());
			}
		}
		return lastImportDate;
	}

	public void setLastImportDate(int directory, MonadDate lastImportDate)
			throws ProgrammerException {
		setProperty(getPropertyNameLastImportDate(directory), lastImportDate.toString());
	}

	public String getLastImportName(int directory) throws ProgrammerException {
		return getProperty(getPropertyNameLastImportName(directory));
	}

	public void setLastImportName(int directory, String name) throws ProgrammerException {
		setProperty(getPropertyNameLastImportName(directory), name);
	}
}