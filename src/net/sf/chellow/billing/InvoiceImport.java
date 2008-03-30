package net.sf.chellow.billing;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.logging.Level;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.ui.ChellowLogger;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;


public class InvoiceImport extends Thread implements Urlable,
		XmlDescriber {
	private static final Map<String, Class<? extends InvoiceConverter>> CONVERTERS;
	
	static {
		CONVERTERS = new HashMap<String, Class<? extends InvoiceConverter>>();
		CONVERTERS.put("mm", InvoiceConverterMm.class);
		CONVERTERS.put("csv", InvoiceConverterCsv.class);
		CONVERTERS.put("edi", InvoiceConverterEdi.class);
	}
	private boolean halt = false;

	private List<VFMessage> messages = new ArrayList<VFMessage>();
	
	private List<Map<InvoiceRaw, VFMessage>> failedInvoices = Collections.synchronizedList(new ArrayList<Map<InvoiceRaw, VFMessage>>());
	private List<InvoiceRaw> successfulInvoices = null;
	
	private InvoiceConverter converter;

	private Long id;

	private Long batchId;

	public InvoiceImport(Long batchId, Long id, FileItem item)
			throws ProgrammerException, UserException {
		try {
			initialize(batchId, id, item.getInputStream(), item.getName(), item.getSize());
		} catch (IOException e) {
			throw new ProgrammerException(e);
		}
	}
	
	public InvoiceImport(Long batchId, Long id, InputStream is,
			String fileName, long fileSize) throws ProgrammerException, UserException {
		initialize(batchId, id, is, fileName, fileSize);
	}

	public void initialize(Long batchId, Long id, InputStream is,
			String fileName, long size) throws ProgrammerException, UserException {
		this.batchId = batchId;
		this.id = id;
		if (size == 0) {
			throw UserException.newInvalidParameter(null, 
					"File has zero length");
		}
		fileName = fileName.toLowerCase();
		/*
		 * if (!fileName.endsWith(".mm") && !fileName.endsWith(".zip") &&
		 * !fileName.endsWith(".csv")) { throw UserException
		 * .newInvalidParameter("The extension of the filename '" + fileName + "'
		 * is not one of the recognized extensions; 'zip', 'mm', 'csv'."); }
		 */
		if (fileName.endsWith(".zip")) {
			ZipInputStream zin;
			try {
				zin = new ZipInputStream(new BufferedInputStream(is));
				ZipEntry entry = zin.getNextEntry();
				if (entry == null) {
					throw UserException
							.newInvalidParameter(null, "Can't find an entry within the zip file.");
				} else {
					is = zin;
					fileName = entry.getName();
				}
				// extract data
				// open output streams
			} catch (IOException e) {
				throw new ProgrammerException(e);
			}
		}
		int locationOfDot = fileName.lastIndexOf("."); 
		if (locationOfDot == -1 || locationOfDot == fileName.length() - 1) {
			throw UserException.newInvalidParameter("The file name must have an extension (eg. '.zip')");
		}
		String extension = fileName.substring(locationOfDot + 1);
		Class<? extends InvoiceConverter> converterClass = CONVERTERS.get(extension);
		if (converterClass == null) {
			StringBuilder recognizedExtensions = new StringBuilder();
			for (String allowedExtension : CONVERTERS.keySet()) {
				recognizedExtensions.append(" " + allowedExtension);
			}
			throw UserException
			.newInvalidParameter("The extension of the filename '"
					+ fileName
					+ "' is not one of the recognized extensions; " + recognizedExtensions + " and it is not a '.zip' file containing a file with one of the recognized extensions.");
		}
		/*
		 * if (fileName.endsWith(".mm")) { converterClass =
		 * InvoiceConverterMm.class; } else if (fileName.endsWith(".csv")) {
		 * converterClass = InvoiceConverterCsv.class; } else { throw
		 * UserException .newInvalidParameter("The extension of the filename '" +
		 * fileName + "' is not one of the recognized extensions; '.mm'."); }
		 */
		try {
			converter = converterClass.
					getConstructor(new Class<?>[] { Reader.class })
					.newInstance(
							new Object[] { new InputStreamReader(is, "UTF-8") });
		} catch (IllegalArgumentException e) {
			throw new ProgrammerException(e);
		} catch (SecurityException e) {
			throw new ProgrammerException(e);
		} catch (UnsupportedEncodingException e) {
			throw new ProgrammerException(e);
		} catch (InstantiationException e) {
			throw new ProgrammerException(e);
		} catch (IllegalAccessException e) {
			throw new ProgrammerException(e);
		} catch (InvocationTargetException e) {
			Throwable cause = e.getCause();
			if (cause instanceof UserException) {
				throw (UserException) cause;
			} else {
				throw new ProgrammerException(e);
			}
		} catch (NoSuchMethodException e) {
			throw new ProgrammerException(e);
		}
	}

	@SuppressWarnings("unchecked")
	public void run() {
		try {
			List<InvoiceRaw> rawInvoices = converter.getRawInvoices(); 
			Batch batch = getBatch();
			Hiber.flush();
			successfulInvoices = Collections.synchronizedList(new ArrayList<InvoiceRaw>());
			for (InvoiceRaw rawInvoice : rawInvoices) {
				Hiber.flush();
				if (shouldHalt()) {
					throw UserException.newInvalidParameter("The import has been halted by the user, some bills may have been imported though.");
				}
				try {
					Hiber.flush();
					batch.insertInvoice(rawInvoice);
					Hiber.commit();
					Hiber.flush();
					successfulInvoices.add(rawInvoice);
				} catch (UserException e) {
					Hiber.flush();
					Map<InvoiceRaw, VFMessage> invoiceMap = new HashMap<InvoiceRaw, VFMessage>();
					invoiceMap.put(rawInvoice, e.getVFMessage());
					failedInvoices.add(invoiceMap);
					Hiber.rollBack();
					Hiber.flush();
				}
			}
			if (failedInvoices.isEmpty()) {
			messages.add(new VFMessage("All the invoices have been successfully loaded and attached to the batch."));
			} else {
			messages.add(new VFMessage("The import has finished, but not all invoices were successfully loaded."));	
			}
			Organization organization = null;
			Provider provider = batch.getService().getProvider();
			if (provider instanceof ProviderOrganization) {
				organization = ((ProviderOrganization) provider).getOrganization();
			}
			Account.checkAllMissingFromLatest(organization);
		} catch (UserException e) {
			messages.add(e.getVFMessage());
		} catch (ProgrammerException e) {
			messages.add(new VFMessage("ProgrammerException : "
					+ e.getMessage()));
			throw new RuntimeException(e);
		} catch (Throwable e) {
			messages.add(new VFMessage("Throwable " + e.getMessage()));
			ChellowLogger.getLogger().logp(Level.SEVERE, "HhDataImportProcessor", "run",
					"Problem in run method " + e.getMessage(), e);
		} finally {
			Hiber.rollBack();
			Hiber.close();
		}
	}

	public synchronized void halt() {
		halt = true;
	}

	private boolean shouldHalt() {
		return halt;
	}

	public UriPathElement getUriId() throws ProgrammerException, UserException {
			return new UriPathElement(Long.toString(id));
	}

	public Urlable getChild(UriPathElement urlId) throws ProgrammerException,
			UserException {
		throw UserException.newNotFound();
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return getBatch().invoiceImportsInstance().getUri().resolve(
				getUriId()).append("/");
	}
	
	private Batch getBatch() throws UserException, ProgrammerException {
		return Batch.getBatch(batchId);
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processElement = (Element) toXML(doc);
		source.appendChild(processElement);
		processElement.appendChild(getBatch().getXML(new XmlTree("service", new XmlTree("provider",
				new XmlTree("organization"))), doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws ProgrammerException, UserException, DesignerException {
		Element importElement = doc.createElement("invoice-import");
		boolean isAlive = this.isAlive();
		importElement.setAttribute("id", getUriId().toString());
		importElement.setAttribute("progress", successfulInvoices == null ? converter.getProgress() : "There have been " + successfulInvoices.size() + " successful imports, and " + failedInvoices.size() + " failures.");
		if (!isAlive && successfulInvoices != null) {
			Element failedElement = doc.createElement("failed-invoices");
			importElement.appendChild(failedElement);
			Element successfulElement = doc.createElement("successful-invoices");
			importElement.appendChild(successfulElement);
			for (Map<InvoiceRaw, VFMessage> invoiceMap : failedInvoices) {
				for (Entry<InvoiceRaw, VFMessage> entry : invoiceMap.entrySet()) {
					Element invoiceRawElement = (Element) entry.getKey().getXML(new XmlTree("registerReads"), doc);
					failedElement.appendChild(invoiceRawElement);
					invoiceRawElement.appendChild(entry.getValue().toXML(doc));
				}
			}
			for (InvoiceRaw invoiceRaw : successfulInvoices) {
				successfulElement.appendChild(invoiceRaw.getXML(new XmlTree("registerReads"), doc));
			}
		}
		for (VFMessage message : messages) {
			importElement.appendChild(message.toXML(doc));
		}
		return importElement;
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
	
	public List<VFMessage> getMessages() {
		return messages;
	}
}