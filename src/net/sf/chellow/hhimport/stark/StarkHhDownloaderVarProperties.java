package net.sf.chellow.hhimport.stark;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.ChellowProperties;

public class StarkHhDownloaderVarProperties extends ChellowProperties {
	public StarkHhDownloaderVarProperties(MonadUri uri) throws InternalException, HttpException {
		super(uri, "var.properties");
	}
private String getPropertyNameLastImportDate(int directory) {
	return "lastImportDate" + directory;
}
private String getPropertyNameLastImportName(int directory) {
	return "lastImportName" + directory;
}
	public MonadDate getLastImportDate(int directory) throws InternalException {
		String lastImportDateStr = getProperty(getPropertyNameLastImportDate(directory));
		MonadDate lastImportDate = null;
		if (lastImportDateStr != null && lastImportDateStr.length() != 0) {
			try {
				lastImportDate = new MonadDate(lastImportDateStr);
			} catch (HttpException e) {
				throw new InternalException(lastImportDateStr + e.getMessage());
			}
		}
		return lastImportDate;
	}

	public void setLastImportDate(int directory, MonadDate lastImportDate)
			throws InternalException {
		setProperty(getPropertyNameLastImportDate(directory), lastImportDate.toString());
	}

	public String getLastImportName(int directory) throws InternalException {
		return getProperty(getPropertyNameLastImportName(directory));
	}

	public void setLastImportName(int directory, String name) throws InternalException {
		setProperty(getPropertyNameLastImportName(directory), name);
	}
}