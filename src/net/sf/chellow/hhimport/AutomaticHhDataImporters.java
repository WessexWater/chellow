package net.sf.chellow.hhimport;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Map.Entry;
import java.util.logging.Level;
import java.util.logging.Logger;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;

public class AutomaticHhDataImporters extends TimerTask {
	private static AutomaticHhDataImporters importersInstance;

	private static Timer timer;

	public synchronized static AutomaticHhDataImporters start()
			throws InternalException {
		if (importersInstance == null) {
			importersInstance = new AutomaticHhDataImporters();
			timer = new Timer("HH Data Importer Timer", true);
			timer.schedule(importersInstance, 0, 60 * 60 * 1000);
		}
		return importersInstance;
	}

	public static AutomaticHhDataImporters getImportersInstance() {
		return importersInstance;
	}

	private InternalException programmerException;

	private Logger logger = Logger.getLogger("net.sf.chellow");

	private final Map<Long, AutomaticHhDataImporter> importers = new HashMap<Long, AutomaticHhDataImporter>();
	
	private boolean running;
	
	public InternalException getProgrammerException() {
		return programmerException;
	}

	public AutomaticHhDataImporter findImporter(HhdcContract contract)
			throws HttpException {
		AutomaticHhDataImporter importer = null;
		if (contract.getProperty("has.importer") != null) {
			importer = importers.get(contract.getId());
			if (importer == null) {
				try {
					importer = new AutomaticHhDataImporter(contract);
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

	public boolean isRunning() {
		return running;
	}

	public void run() {
		if (canRun()) {
			run2();
		} 
	}
	
	public synchronized boolean canRun() {
		if (running) {
			return false;
		} else {
			running = true;
			return true;
		}
	}

	@SuppressWarnings("unchecked")
	public void run2() {
		try {
			for (Entry<Long, AutomaticHhDataImporter> importerEntry : importers
					.entrySet()) {
				if (HhdcContract.findHhdcContract(importerEntry.getKey()) == null) {
					importers.remove(importerEntry.getKey());
				}
			}
			for (HhdcContract contract : (List<HhdcContract>) Hiber.session()
					.createQuery("from HhdcContract contract").list()) {
				findImporter(contract);
			}
			for (AutomaticHhDataImporter importer : importers.values()) {
				importer.run();
			}
			Hiber.close();
		} catch (InternalException e) {
			throw new RuntimeException(e);
		} catch (HttpException e) {
			throw new RuntimeException(e);
		} finally {
			running = false;
		}
	}
}