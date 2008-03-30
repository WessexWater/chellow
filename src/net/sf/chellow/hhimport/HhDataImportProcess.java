package net.sf.chellow.hhimport;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import net.sf.chellow.billing.DceService;
import net.sf.chellow.data08.HhDatumRaw;
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
import net.sf.chellow.physical.Channel;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.ui.ChellowLogger;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;


public class HhDataImportProcess extends Thread implements Urlable,
		XmlDescriber {
	private boolean halt = false;

	private List<VFMessage> messages = new ArrayList<VFMessage>();

	private HhConverter converter;

	private long suppliesChecked;
	
	private Integer batchSize = null;

	private List<Supply> supplies = null;

	private Long id;

	private Long dceServiceId;

	public HhDataImportProcess(Long dceServiceId, Long id, FileItem item)
			throws ProgrammerException, UserException {
		try {
			initialize(dceServiceId, id, item.getInputStream(), item.getName(), item.getSize());
		} catch (IOException e) {
			throw new ProgrammerException(e);
		}
	}
	
	public HhDataImportProcess(Long contractId, Long id, InputStream is,
			String fileName, long fileSize) throws ProgrammerException, UserException {
		initialize(contractId, id, is, fileName, fileSize);
	}

	public void initialize(Long dceServiceId, Long id, InputStream is,
			String fileName, long size) throws ProgrammerException, UserException {
		this.dceServiceId = dceServiceId;
		this.id = id;
		if (size == 0) {
			throw UserException.newInvalidParameter(null, 
					"File has zero length");
		}
		fileName = fileName.toLowerCase();
		if (!fileName.endsWith(".df2") && !fileName.endsWith(".stark.csv") && !fileName.endsWith(".simple.csv") && !fileName.endsWith(".zip")) {
			throw UserException
					.newInvalidParameter("The extension of the filename '"
							+ fileName
							+ "' is not one of the recognized extensions; '.zip', '.df2', '.stark.csv', '.simple.csv'.");
		}
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
		String converterName;
		if (fileName.endsWith(".df2")) {
			converterName = "net.sf.chellow.hhimport.stark.StarkDF2HHConverter";
		} else if (fileName.endsWith(".stark.csv")) {
			converterName = "net.sf.chellow.hhimport.stark.StarkCsvHhConverter";
		} else if (fileName.endsWith(".simple.csv")) {
			converterName = "net.sf.chellow.hhimport.HhConverterCsvSimple";
		} else {
			throw UserException
					.newInvalidParameter("The extension of the filename '"
							+ fileName
							+ "' is not one of the recognized extensions; '.df2', '.stark.csv', '.simple.csv'.");
		}

		try {
			converter = (HhConverter) Class
					.forName(converterName)
					.getConstructor(new Class<?>[] { Reader.class })
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
		} catch (ClassNotFoundException e) {
			throw new ProgrammerException(e);
		}
	}

	@SuppressWarnings("unchecked")
	public void run() {
		try {
			DceService dceService = DceService.getDceService(dceServiceId);
			List<HhDatumRaw> data = new ArrayList<HhDatumRaw>();
			HhDatumRaw firstDatumRaw = null;
			while (!shouldHalt() && converter.hasNext()) {
				HhDatumRaw datum;
				try {
					datum = converter.next();
				} catch (RuntimeException e) {
					if (e.getCause() != null) {
						throw e.getCause();
					} else {
						throw e;
					}
				}
				if (firstDatumRaw == null) {
					firstDatumRaw = datum;
				} else if (data.size() > 1000 || !(datum.getMpanCore().equals(
						firstDatumRaw.getMpanCore())
						&& datum.getIsImport().equals(
								firstDatumRaw.getIsImport())
						&& datum.getIsKwh().equals(firstDatumRaw.getIsKwh()) && datum
						.getEndDate().getDate().equals(data.get(data.size() - 1).getEndDate()
										.getNext().getDate()))) {
					batchSize = data.size();
					Channel.addHhData(dceService, data);
					Hiber.close();
					data.clear();
					firstDatumRaw = datum;
				}
				data.add(datum);
			}
			if (!data.isEmpty()) {
				Channel.addHhData(dceService, data);
			}
			Hiber.close();
			// check hh data - supply level
			supplies = (List<Supply>) Hiber.session()
					.createQuery("from Supply").list();
			for (int i = 0; i < supplies.size(); i++) {
				suppliesChecked = i;
				Supply.getSupply(supplies.get(i).getId())
						.checkForMissingFromLatest();
				Hiber.close();
			}
		} catch (IOException e) {
			messages.add(new VFMessage("ProgrammerException : "
					+ e.getMessage()));
			throw new RuntimeException(e);
		} catch (UserException e) {
			messages.add(e.getVFMessage());
		} catch (ProgrammerException e) {
			messages.add(new VFMessage("ProgrammerException : "
					+ e.getMessage()));
			throw new RuntimeException(e);
		} catch (Throwable e) {
			messages.add(new VFMessage("Problem at line number: "
					+ converter.lastLineNumber() + " " + e));
			ChellowLogger.getLogger().logp(Level.SEVERE, "HhDataImportProcessor", "run",
					"Problem in run method " + e.getMessage(), e);
		} finally {
			Hiber.rollBack();
			Hiber.close();
			try {
				converter.close();
			} catch (ProgrammerException e) {
				throw new RuntimeException(e);
			}
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
		return getDceService().getHhDataImportProcessesInstance().getUri().resolve(
				getUriId()).append("/");
	}
	
	private DceService getDceService() throws UserException, ProgrammerException {
		return DceService.getDceService(dceServiceId);
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processElement = (Element) toXML(doc);
		source.appendChild(processElement);
		processElement.appendChild(getDceService().getXML(new XmlTree("provider",
				new XmlTree("organization")), doc));
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
	
	public String status() {
		return supplies == null ?  "Processing line number "
				+ converter.lastLineNumber() + " and batch size is " + batchSize + "." :
					"Checking supply " + (suppliesChecked + 1)
					+ " of " + supplies.size() + ".";
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element importElement = doc.createElement("hh-data-import");
		importElement.setAttribute("uri-id", getUriId().toString());
		importElement.setAttribute("progress", status());
		if (!this.isAlive()) {
			importElement.setAttribute("successful",
					messages.isEmpty() ? "true" : "false");
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