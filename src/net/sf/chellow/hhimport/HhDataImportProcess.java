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

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.data08.HhDatumRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.MonadMessage;
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

	private List<String> messages = new ArrayList<String>();

	private HhConverter converter;

	private long suppliesChecked;
	
	private Integer batchSize = null;

	private List<Supply> supplies = null;

	private Long id;

	private Long dceServiceId;

	public HhDataImportProcess(Long dceServiceId, Long id, FileItem item)
			throws InternalException, HttpException {
		try {
			initialize(dceServiceId, id, item.getInputStream(), item.getName(), item.getSize());
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}
	
	public HhDataImportProcess(Long contractId, Long id, InputStream is,
			String fileName, long fileSize) throws InternalException, HttpException {
		initialize(contractId, id, is, fileName, fileSize);
	}

	public void initialize(Long dceServiceId, Long id, InputStream is,
			String fileName, long size) throws InternalException, HttpException {
		this.dceServiceId = dceServiceId;
		this.id = id;
		if (size == 0) {
			throw new UserException("File has zero length");
		}
		fileName = fileName.toLowerCase();
		if (!fileName.endsWith(".df2") && !fileName.endsWith(".stark.csv") && !fileName.endsWith(".simple.csv") && !fileName.endsWith(".zip")) {
			throw new UserException("The extension of the filename '"
							+ fileName
							+ "' is not one of the recognized extensions; '.zip', '.df2', '.stark.csv', '.simple.csv'.");
		}
		if (fileName.endsWith(".zip")) {
			ZipInputStream zin;
			try {
				zin = new ZipInputStream(new BufferedInputStream(is));
				ZipEntry entry = zin.getNextEntry();
				if (entry == null) {
					throw new UserException(null, "Can't find an entry within the zip file.");
				} else {
					is = zin;
					fileName = entry.getName();
				}
				// extract data
				// open output streams
			} catch (IOException e) {
				throw new InternalException(e);
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
			throw new UserException("The extension of the filename '"
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
			throw new InternalException(e);
		} catch (SecurityException e) {
			throw new InternalException(e);
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (InstantiationException e) {
			throw new InternalException(e);
		} catch (IllegalAccessException e) {
			throw new InternalException(e);
		} catch (InvocationTargetException e) {
			Throwable cause = e.getCause();
			if (cause instanceof HttpException) {
				throw (HttpException) cause;
			} else {
				throw new InternalException(e);
			}
		} catch (NoSuchMethodException e) {
			throw new InternalException(e);
		} catch (ClassNotFoundException e) {
			throw new InternalException(e);
		}
	}

	@SuppressWarnings("unchecked")
	public void run() {
		try {
			HhdcContract dceService = HhdcContract.getHhdcContract(dceServiceId);
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
			messages.add("ProgrammerException : ");
			throw new RuntimeException(e);
		} catch (InternalException e) {
			messages.add("ProgrammerException : "
					+ e.getMessage());
			throw new RuntimeException(e);
		} catch (HttpException e) {
			messages.add(e.getMessage());
		} catch (Throwable e) {
			messages.add("Problem at line number: "
					+ converter.lastLineNumber() + " " + e);
			ChellowLogger.getLogger().logp(Level.SEVERE, "HhDataImportProcessor", "run",
					"Problem in run method " + e.getMessage(), e);
		} finally {
			Hiber.rollBack();
			Hiber.close();
			try {
				converter.close();
			} catch (InternalException e) {
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

	public UriPathElement getUriId() throws InternalException, HttpException {
			return new UriPathElement(Long.toString(id));
	}

	public Urlable getChild(UriPathElement urlId) throws InternalException,
			NotFoundException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return getDceService().getHhDataImportProcessesInstance().getUri().resolve(
				getUriId()).append("/");
	}
	
	private HhdcContract getDceService() throws HttpException, InternalException {
		return HhdcContract.getHhdcContract(dceServiceId);
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processElement = (Element) toXml(doc);
		source.appendChild(processElement);
		processElement.appendChild(getDceService().toXml(doc, new XmlTree("provider",
						new XmlTree("organization"))));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
	
	public String status() {
		return supplies == null ?  "Processing line number "
				+ converter.lastLineNumber() + " and batch size is " + batchSize + "." :
					"Checking supply " + (suppliesChecked + 1)
					+ " of " + supplies.size() + ".";
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element importElement = doc.createElement("hh-data-import");
		importElement.setAttribute("uri-id", getUriId().toString());
		importElement.setAttribute("progress", status());
		if (!this.isAlive()) {
			importElement.setAttribute("successful",
					messages.isEmpty() ? "true" : "false");
		}
		for (String message : messages) {
			importElement.appendChild(new MonadMessage(message).toXml(doc));
		}
		return importElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
	
	public List<String> getMessages() {
		return messages;
	}
}