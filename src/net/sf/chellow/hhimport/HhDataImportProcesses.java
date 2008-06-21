package net.sf.chellow.hhimport;

import java.util.HashMap;
import java.util.Map;

import net.sf.chellow.billing.Service;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;


public class HhDataImportProcesses implements Urlable {
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

	private Service service;

	public HhDataImportProcesses(Service service) {
		this.service = service;
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

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		Map<Long, HhDataImportProcess> contractProcesses = processes
				.get(service.getId());
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

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();
		Element hhDataImportsElement = (Element) toXML(doc);
		source.appendChild(hhDataImportsElement);
		hhDataImportsElement.appendChild(service.toXml(doc, new XmlTree(
						"provider", new XmlTree("organization"))));
		Map<Long, HhDataImportProcess> contractProcesses = processes
				.get(service.getId());
		if (contractProcesses != null) {
			for (HhDataImportProcess process : contractProcesses.values()) {
				hhDataImportsElement.appendChild(process.toXml(doc));
			}
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		FileItem fileItem = inv.getFileItem("import-file");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			HhDataImportProcess hhImportProcess = new HhDataImportProcess(
					service.getId(), processSerial++, fileItem);
			hhImportProcess.start();

			Map<Long, HhDataImportProcess> contractProcesses = processes
					.get(service.getId());
			if (contractProcesses == null) {
				processes.put(service.getId(),
						new HashMap<Long, HhDataImportProcess>());
			}
			contractProcesses = processes.get(service.getId());
			contractProcesses.put(Long.parseLong(hhImportProcess.getUriId()
					.toString()), hhImportProcess);
			inv.sendCreated(document(), hhImportProcess.getUri());
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws InternalException, HttpException {
		return doc.createElement("hh-data-imports");
	}

	public Node getXML(XmlTree tree, Document doc) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return service.getUri().resolve(getUriId()).append("/");
	}
}