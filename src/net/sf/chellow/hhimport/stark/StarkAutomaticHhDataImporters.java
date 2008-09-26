package net.sf.chellow.hhimport.stark;

import java.io.IOException;
import java.io.StringReader;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Map.Entry;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;

public class StarkAutomaticHhDataImporters extends TimerTask {
	private static StarkAutomaticHhDataImporters importersInstance;

	private static Timer timer;

	public synchronized static StarkAutomaticHhDataImporters start()
			throws InternalException {
		if (importersInstance == null) {
			importersInstance = new StarkAutomaticHhDataImporters();
			timer = new Timer(true);
			timer.schedule(importersInstance, 0, 60 * 60 * 1000);
		}
		return importersInstance;
	}

	public static StarkAutomaticHhDataImporters getImportersInstance() {
		return importersInstance;
	}

	private InternalException programmerException;

	private Logger logger = Logger.getLogger("net.sf.chellow");

	private final Map<Long, StarkAutomaticHhDataImporter> importers = new HashMap<Long, StarkAutomaticHhDataImporter>();

	public InternalException getProgrammerException() {
		return programmerException;
	}

	public StarkAutomaticHhDataImporter findImporter(HhdcContract contract)
			throws HttpException {
		Properties props = new Properties();
		StarkAutomaticHhDataImporter importer = null;

		try {
			props.load(new StringReader(contract.getImporterProperties()));
		} catch (IOException e) {
			throw new InternalException(e);
		}
		if (props.getProperty("importer.name").equals(
				"StarkAutomaticHhDataImporter")) {
			importer = importers.get(contract.getId());
			if (importer == null
					|| !importer.getPropertiesString().equals(
							contract.getImporterProperties())) {
				try {
					importer = new StarkAutomaticHhDataImporter(contract);
					importers.put(contract.getId(), importer);
				} catch (HttpException e) {
					logger.logp(Level.SEVERE, "StarkAutomaticHhDataImporter",
							"run",
							"Problem creating new Stark Automatic Hh Data Importer. "
									+ e.getMessage(), e);
				}
			}
		}
		return importer;
	}

	@SuppressWarnings("unchecked")
	public void run() {
		try {
			for (Entry<Long, StarkAutomaticHhDataImporter> importerEntry : importers
					.entrySet()) {
				if (!StarkAutomaticHhDataImporter.importerExists(importerEntry
						.getValue().getUri())) {
					importers.remove(importerEntry.getKey());
				}
			}
			for (HhdcContract dceService : (List<HhdcContract>) Hiber.session()
					.createQuery("from DceService service").list()) {
				findImporter(dceService);
			}
			for (StarkAutomaticHhDataImporter importer : importers.values()) {
				importer.run();
			}
			Hiber.close();
		} catch (InternalException e) {
			throw new RuntimeException(e);
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}
}