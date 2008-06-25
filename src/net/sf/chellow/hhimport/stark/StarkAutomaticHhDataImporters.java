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
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadUri;

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

	public StarkAutomaticHhDataImporter findImporter(HhdcContract service)
			throws InternalException, HttpException {
		MonadUri importerUri = service.getUri().resolve(
				StarkAutomaticHhDataImporter.URI_ID);
		StarkAutomaticHhDataImporter importer = null;
		if (StarkAutomaticHhDataImporter.importerExists(importerUri)) {
			importer = importers.get(service.getId());
			if (importer == null) {
				try {
					importer = new StarkAutomaticHhDataImporter(service
							.getId());
					importers.put(service.getId(), importer);
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