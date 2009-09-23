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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.ChellowLogger;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class BillImport extends Thread implements Urlable, XmlDescriber {
	private static final Map<String, Class<? extends BillConverter>> CONVERTERS;

	static {
		CONVERTERS = new HashMap<String, Class<? extends BillConverter>>();
		CONVERTERS.put("mm", BillConverterMm.class);
		CONVERTERS.put("csv", BillConverterCsv.class);
		CONVERTERS.put("bgb.edi", BillConverterBgbEdi.class);
		CONVERTERS.put("sse.edi", BillConverterSseEdi.class);
	}
	private boolean halt = false;

	private List<String> messages = Collections
			.synchronizedList(new ArrayList<String>());

	private List<Map<RawBill, String>> failedBills = Collections
			.synchronizedList(new ArrayList<Map<RawBill, String>>());
	private List<RawBill> successfulBills = null;

	private BillConverter converter;

	private Long id;

	private Long batchId;

	public BillImport(Long batchId, Long id, FileItem item)
			throws HttpException {
		try {
			initialize(batchId, id, item.getInputStream(), item.getName(), item
					.getSize());
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	public BillImport(Long batchId, Long id, InputStream is, String fileName,
			long fileSize) throws HttpException {
		initialize(batchId, id, is, fileName, fileSize);
	}

	public void initialize(Long batchId, Long id, InputStream is,
			String fileName, long size) throws HttpException {
		this.batchId = batchId;
		this.id = id;
		if (size == 0) {
			throw new UserException(null, "File has zero length");
		}
		fileName = fileName.toLowerCase();
		/*
		 * if (!fileName.endsWith(".mm") && !fileName.endsWith(".zip") &&
		 * !fileName.endsWith(".csv")) { throw UserException
		 * .newInvalidParameter("The extension of the filename '" + fileName +
		 * "' is not one of the recognized extensions; 'zip', 'mm', 'csv'."); }
		 */
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
		int locationOfDot = fileName.indexOf(".");
		if (locationOfDot == -1 || locationOfDot == fileName.length() - 1) {
			throw new UserException(
					"The file name must have an extension (eg. '.zip')");
		}
		String extension = fileName.substring(locationOfDot + 1);
		Class<? extends BillConverter> converterClass = CONVERTERS
				.get(extension);
		if (converterClass == null) {
			StringBuilder recognizedExtensions = new StringBuilder();
			for (String allowedExtension : CONVERTERS.keySet()) {
				recognizedExtensions.append(" " + allowedExtension);
			}
			throw new UserException(
					"The extension '"
							+ extension
							+ "' of the filename '"
							+ fileName
							+ "' is not one of the recognized extensions; "
							+ recognizedExtensions
							+ " and it is not a '.zip' file containing a file with one of the recognized extensions.");
		}
		try {
			converter = converterClass.getConstructor(
					new Class<?>[] { Reader.class }).newInstance(
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
		}
	}

	public void run() {
		try {
			List<RawBill> rawBills = converter.getRawBills();
			Batch batch = getBatch();
			Hiber.flush();
			successfulBills = Collections
					.synchronizedList(new ArrayList<RawBill>());
			for (RawBill rawBill : rawBills) {
				Hiber.flush();
				if (shouldHalt()) {
					throw new UserException(
							"The import has been halted by the user, some bills may have been imported though.");
				}
				try {
					Hiber.flush();
					batch.insertBill(rawBill);
					Hiber.commit();
					Hiber.flush();
					successfulBills.add(rawBill);
				} catch (HttpException e) {
					Hiber.flush();
					Map<RawBill, String> billMap = new HashMap<RawBill, String>();
					billMap.put(rawBill, e.getMessage());
					failedBills.add(billMap);
					Hiber.rollBack();
					Hiber.flush();
				}
			}
			// Account.checkAllMissingFromLatest();
			if (failedBills.isEmpty()) {
				messages
						.add("All the bills have been successfully loaded and attached to the batch.");
			} else {
				messages
						.add("The import has finished, but not all bills were successfully loaded.");
			}
		} catch (InternalException e) {
			messages.add("ProgrammerException : "
					+ HttpException.getStackTraceString(e));
			throw new RuntimeException(e);
		} catch (HttpException e) {
			messages.add(e.getMessage());
		} catch (Throwable e) {
			messages.add("Throwable " + HttpException.getStackTraceString(e));
			ChellowLogger.getLogger().logp(Level.SEVERE,
					"HhDataImportProcessor", "run",
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

	public UriPathElement getUriId() throws HttpException {
		return new UriPathElement(Long.toString(id));
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws HttpException {
		return getBatch().billImportsInstance().getUri().resolve(getUriId())
				.append("/");
	}

	private Batch getBatch() throws HttpException {
		return Batch.getBatch(batchId);
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processElement = toXml(doc);
		source.appendChild(processElement);
		processElement.appendChild(getBatch().toXml(doc,
				new XmlTree("contract", new XmlTree("party"))));
		inv.sendOk(doc);
	}

	public Element toXml(Document doc) throws HttpException {
		Element importElement = doc.createElement("bill-import");
		boolean isAlive = this.isAlive();
		importElement.setAttribute("id", getUriId().toString());
		importElement
				.setAttribute("progress", successfulBills == null ? converter
						.getProgress() : "There have been "
						+ successfulBills.size() + " successful imports, and "
						+ failedBills.size() + " failures."
						+ (isAlive ? "The thread is still alive." : ""));
		if (!isAlive && successfulBills != null) {
			Element failedElement = doc.createElement("failed-bills");
			importElement.appendChild(failedElement);
			Element successfulElement = doc.createElement("successful-bills");
			importElement.appendChild(successfulElement);
			for (Map<RawBill, String> billMap : failedBills) {
				for (Entry<RawBill, String> entry : billMap.entrySet()) {
					Element billRawElement = (Element) entry.getKey().toXml(
							doc, new XmlTree("registerReads"));
					failedElement.appendChild(billRawElement);
					billRawElement.appendChild(new MonadMessage(entry
							.getValue()).toXml(doc));
				}
			}
			for (RawBill billRaw : successfulBills) {
				successfulElement.appendChild(billRaw.toXml(doc, new XmlTree(
						"registerReads")));
			}
		}
		for (String message : messages) {
			importElement.appendChild(new MonadMessage(message).toXml(doc));
		}
		return importElement;
	}

	public List<String> getMessages() {
		return messages;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		throw new NotFoundException();
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		throw new NotFoundException();
	}

	@Override
	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
