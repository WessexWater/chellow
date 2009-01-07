package net.sf.chellow.hhimport.stark;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Map.Entry;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.hhimport.StarkAutomaticHhDataImporter;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;

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
		StarkAutomaticHhDataImporter importer = null;
		if ("StarkAutomaticHhDataImporter".equals(contract
				.getProperty("importer.name"))) {
			importer = importers.get(contract.getId());
			if (importer == null) {
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
		if (importer == null) {
			if (importers.containsKey(contract.getId())) {
				importers.remove(contract.getId());
			}
		}
		return importer;
	}

	@SuppressWarnings("unchecked")
	public void run() {
		try {
			for (Entry<Long, StarkAutomaticHhDataImporter> importerEntry : importers
					.entrySet()) {
				if (HhdcContract.findHhdcContract(importerEntry.getKey()) == null) {
					importers.remove(importerEntry.getKey());
				}
			}
			for (HhdcContract contract : (List<HhdcContract>) Hiber.session()
					.createQuery("from HhdcContract contract").list()) {
				findImporter(contract);
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