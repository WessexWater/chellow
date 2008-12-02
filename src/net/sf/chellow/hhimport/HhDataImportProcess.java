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
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhDatum;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.ui.ChellowLogger;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class HhDataImportProcess extends Thread implements Urlable,
		XmlDescriber {
	private List<Boolean> halt = new ArrayList<Boolean>();

	private List<String> messages = new ArrayList<String>();

	private HhConverter converter;

	private long suppliesChecked;
	// private Integer batchSize = null;

	private List<SupplyGeneration> supplyGenerations = null;

	private Long id;

	private Long hhdcContractId;

	public HhDataImportProcess(Long hhdcContractId, Long id, FileItem item)
			throws HttpException {
		try {
			initialize(hhdcContractId, id, item.getInputStream(), item
					.getName(), item.getSize());
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public HhDataImportProcess(Long contractId, Long id, InputStream is,
			String fileName, long fileSize) throws HttpException {
		initialize(contractId, id, is, fileName, fileSize);
	}

	public void initialize(Long hhdcContractId, Long id, InputStream is,
			String fileName, long size) throws HttpException {
		halt.add(false);
		this.hhdcContractId = hhdcContractId;
		this.id = id;
		if (size == 0) {
			throw new UserException("File has zero length");
		}
		fileName = fileName.toLowerCase();
		if (!fileName.endsWith(".df2") && !fileName.endsWith(".stark.csv")
				&& !fileName.endsWith(".simple.csv")
				&& !fileName.endsWith(".zip")) {
			throw new UserException(
					"The extension of the filename '"
							+ fileName
							+ "' is not one of the recognized extensions; '.zip', '.df2', '.stark.csv', '.simple.csv'.");
		}
		if (fileName.endsWith(".zip")) {
			ZipInputStream zin;
			try {
				zin = new ZipInputStream(new BufferedInputStream(is));
				ZipEntry entry = zin.getNextEntry();
				if (entry == null) {
					throw new UserException(null,
							"Can't find an entry within the zip file.");
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
			throw new UserException(
					"The extension of the filename '"
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
			HhDatum.insert(converter, halt, messages);
			/*
			 * HhDatumRaw datum = converter.next(); String mpanCoreStr =
			 * datum.getMpanCore(); MpanCore mpanCore =
			 * MpanCore.getMpanCore(mpanCoreStr); SupplyGeneration generation =
			 * mpanCore .getSupply().getGeneration(datum.getEndDate());
			 * 
			 * if (generation == null) { throw new UserException("HH datum has
			 * been ignored: " + datum.toString() + "."); } Channel channel =
			 * generation.getChannel(datum.getIsImport(), datum .getIsKwh());
			 * HhEndDate genFinishDate = generation.getFinishDate(); List<HhDatumRaw>
			 * data = new ArrayList<HhDatumRaw>(); data.add(datum); HhDatumRaw
			 * firstDatum = datum; if (!converter.hasNext()) { batchSize =
			 * data.size(); try { channel.addHhData(data); } catch
			 * (UserException e) { messages.add(e.getMessage()); } } while
			 * (!shouldHalt() && converter.hasNext()) { try { datum =
			 * converter.next(); } catch (RuntimeException e) { if (e.getCause() !=
			 * null) { throw e.getCause(); } else { throw e; } } if (data.size() >
			 * 100 || !(mpanCoreStr.equals(datum.getMpanCore()) &&
			 * datum.getIsImport() == firstDatum .getIsImport() &&
			 * datum.getIsKwh() == firstDatum.getIsKwh() && datum
			 * .getEndDate().getDate().equals( data.get(data.size() -
			 * 1).getEndDate() .getNext().getDate())) || (genFinishDate != null &&
			 * genFinishDate.getDate() .before(datum.getEndDate().getDate()))) {
			 * batchSize = data.size(); try { channel.addHhData(data); } catch
			 * (UserException e) { messages.add(e.getMessage()); }
			 * Hiber.close(); data.clear(); mpanCoreStr = datum.getMpanCore();
			 * mpanCore = MpanCore.getMpanCore(mpanCoreStr); generation =
			 * mpanCore.getSupply() .getGeneration(datum.getEndDate()); if
			 * (generation == null) { throw new UserException("HH datum has been
			 * ignored: " + datum.toString() + "."); } channel =
			 * generation.getChannel(datum.getIsImport(), datum .getIsKwh());
			 * genFinishDate = generation.getFinishDate(); } data.add(datum); }
			 * if (!data.isEmpty()) { channel.addHhData(data); }
			 */
			Hiber.close();
			// check hh data - supply level
			supplyGenerations = (List<SupplyGeneration>) Hiber
					.session()
					.createQuery(
							"select supplyGeneration from SupplyGeneration supplyGeneration where supplyGeneration.finishDate.date is null")
					.list();
			for (int i = 0; i < supplyGenerations.size(); i++) {
				suppliesChecked = i;
				SupplyGeneration.getSupplyGeneration(
						supplyGenerations.get(i).getId())
						.checkForMissingFromLatest(null);
				Hiber.close();
			}
		} catch (InternalException e) {
			messages.add("ProgrammerException : "
					+ HttpException.getStackTraceString(e));
			throw new RuntimeException(e);
		} catch (HttpException e) {
			messages.add(e.getMessage());
		} catch (Throwable e) {
			messages.add("Problem at line number: "
					+ converter.lastLineNumber() + " "
					+ HttpException.getStackTraceString(e));
			ChellowLogger.getLogger().logp(Level.SEVERE,
					"HhDataImportProcessor", "run",
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

	public void halt() {
		halt.set(0, true);
	}

	public UriPathElement getUriId() throws HttpException {
		return new UriPathElement(Long.toString(id));
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws HttpException {
		return getHhdcContract().getHhDataImportProcessesInstance().getUri()
				.resolve(getUriId()).append("/");
	}

	private HhdcContract getHhdcContract() throws HttpException {
		return HhdcContract.getHhdcContract(hhdcContractId);
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processElement = toXml(doc);
		source.appendChild(processElement);
		processElement.appendChild(getHhdcContract().toXml(doc,
				new XmlTree("party")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public String status() {
		return supplyGenerations == null ? "Processing line number "
				+ converter.lastLineNumber() + "." : "Checking supply "
				+ (suppliesChecked + 1) + " of " + supplyGenerations.size()
				+ ".";
	}

	public Element toXml(Document doc) throws HttpException {
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