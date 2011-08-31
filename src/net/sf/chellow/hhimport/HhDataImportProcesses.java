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

import java.net.URI;
import java.util.HashMap;
import java.util.Map;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhDataImportProcesses extends EntityList {
	static public final MonadUri URI_ID;

	static private long processSerial = 0;

	static private final Map<Long, Map<Long, HhDataImportProcess>> processes = new HashMap<Long, Map<Long, HhDataImportProcess>>();

	static {
		try {
			URI_ID = new MonadUri("hh-data-imports");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private HhdcContract contract;

	public HhDataImportProcesses(HhdcContract contract) {
		this.contract = contract;
	}

	/*
	 * public HhDataImportProcesses(FileItem item) throws ProgrammerException,
	 * UserException, DeployerException { hhImporter = new
	 * HhImportProcess(item); }
	 * 
	 * public HhDataImportProcesses(InputStream is, String converterName) throws
	 * ProgrammerException, UserException, DeployerException { hhImporter = new
	 * HhImportProcess(is, converterName); }
	 * 
	 * public void run() { hhImporter.run(); }
	 */

	/*
	 * public static synchronized boolean buildHhImportDocument(Invocation inv,
	 * Document doc) throws ProgrammerException, UserException,
	 * DeployerException { boolean isFinished = false; Element source =
	 * (Element) doc.getFirstChild(); ManualHhImporter importThread =
	 * (ManualHhImporter) inv.getRequest()
	 * .getSession().getAttribute(HH_IMPORT_THREAD); if (importThread == null) {
	 * importThread = new ManualHhImporter(inv.getFileItem("importFile"));
	 * 
	 * inv.getRequest().getSession().setAttribute(HH_IMPORT_THREAD,
	 * importThread); importThread.start(); } if (importThread.isAlive()) {
	 * source .setAttribute( "progress", importThread.getHhImporter() == null ?
	 * "Preparing to import." : importThread.getHhImporter() .getProgress());
	 * inv.getResponse().setHeader("Refresh", "5"); } else {
	 * inv.getRequest().getSession().setAttribute(HH_IMPORT_THREAD, null);
	 * isFinished = true; ProgrammerException programmerException = importThread
	 * .getHhImporter().getProgrammerException(); if (programmerException !=
	 * null) { throw programmerException; }
	 * source.appendChild(importThread.getHhImporter().getMessage().toXML(
	 * doc)); } return isFinished; }
	 */
	/*
	 * public HhImportProcess getHhImporter() { return hhImporter; }
	 */

	public MonadUri getUriId() {
		return URI_ID;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		Map<Long, HhDataImportProcess> contractProcesses = processes
				.get(contract.getId());
		if (contractProcesses == null) {
			throw new NotFoundException();
		}
		HhDataImportProcess process = contractProcesses.get(Long
				.parseLong(uriId.toString()));
		if (process == null) {
			throw new NotFoundException();
		}
		return process;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element hhDataImportsElement = toXml(doc);
		source.appendChild(hhDataImportsElement);
		hhDataImportsElement.appendChild(contract.toXml(doc, new XmlTree(
				"party")));
		Map<Long, HhDataImportProcess> contractProcesses = processes
				.get(contract.getId());
		if (contractProcesses != null) {
			for (HhDataImportProcess process : contractProcesses.values()) {
				hhDataImportsElement.appendChild(process.toXml(doc));
			}
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		FileItem fileItem = inv.getFileItem("import-file");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			HhDataImportProcess hhImportProcess = new HhDataImportProcess(
					contract.getId(), processSerial++, fileItem);
			hhImportProcess.start();

			Map<Long, HhDataImportProcess> contractProcesses = processes
					.get(contract.getId());
			if (contractProcesses == null) {
				processes.put(contract.getId(),
						new HashMap<Long, HhDataImportProcess>());
			}
			contractProcesses = processes.get(contract.getId());
			contractProcesses.put(Long.parseLong(hhImportProcess.getUriId()
					.toString()), hhImportProcess);
			inv.sendSeeOther(hhImportProcess.getEditUri());
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("hh-data-imports");
	}

	public MonadUri getEditUri() throws HttpException {
		return contract.getEditUri().resolve(getUriId()).append("/");
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
