package net.sf.chellow.ui;

import java.io.IOException;
import java.util.logging.FileHandler;
import java.util.logging.Logger;

import net.sf.chellow.monad.MonadFormatter;

public class ChellowLogger {
	static private Logger logger = Logger.getLogger("net.sf.chellow");
	
	static {
		FileHandler fh;
		try {
			fh = new FileHandler("%t/chellow.log");
		} catch (SecurityException e) {
			throw new RuntimeException(e);
		} catch (IOException e) {
			throw new RuntimeException(e);
		}
		fh.setFormatter(new MonadFormatter());
		logger.addHandler(fh);
	}
	
	static public Logger getLogger() {
		return logger;
	}
}
