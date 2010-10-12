/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/
package net.sf.chellow.hhimport;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Map.Entry;
import java.util.concurrent.locks.ReentrantLock;
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
		importersInstance = new AutomaticHhDataImporters();
		timer = new Timer("HH Data Importer Timer", true);
		timer.schedule(importersInstance, 0, 60 * 60 * 1000);
		return importersInstance;
	}

	public static AutomaticHhDataImporters getImportersInstance() {
		return importersInstance;
	}

	private InternalException programmerException;

	private Logger logger = Logger.getLogger("net.sf.chellow");

	private final Map<Long, AutomaticHhDataImporter> importers = new HashMap<Long, AutomaticHhDataImporter>();

	private ReentrantLock lock = new ReentrantLock();

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

	public boolean isLocked() {
		return lock.isLocked();
	}

	@SuppressWarnings("unchecked")
	public void run() {
		if (lock.tryLock()) {
			try {
				for (Entry<Long, AutomaticHhDataImporter> importerEntry : importers
						.entrySet()) {
					if (HhdcContract.findHhdcContract(importerEntry.getKey()) == null) {
						importers.remove(importerEntry.getKey());
					}
				}
				for (HhdcContract contract : (List<HhdcContract>) Hiber
						.session().createQuery("from HhdcContract contract")
						.list()) {
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
				lock.unlock();
			}
		}
	}
}
