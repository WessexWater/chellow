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
import java.io.UnsupportedEncodingException;
import java.net.URI;
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
import org.python.core.PyJavaType;
import org.python.core.PyObject;
import org.python.util.PythonInterpreter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class BillImport extends Thread implements Urlable, XmlDescriber {
	private boolean halt = false;

	private List<String> messages = Collections
			.synchronizedList(new ArrayList<String>());

	private List<Map<RawBill, String>> failedBills = Collections
			.synchronizedList(new ArrayList<Map<RawBill, String>>());
	private List<RawBill> successfulBills = null;

	private BillParser parser;

	private Long id;

	private Long batchId;

	public BillImport(Long batchId, Long id, FileItem item)
			throws HttpException {
		try {
			initialize(batchId, id, item.getInputStream(), item.getName(),
					item.getSize());
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
		if (fileName.endsWith(".zip")) {
			try {
				is = new ZipInputStream(new BufferedInputStream(is));
				ZipEntry entry = ((ZipInputStream) is).getNextEntry();
				if (entry == null) {
					throw new UserException(null,
							"Can't find an entry within the zip file.");
				}
				fileName = entry.getName();

				// extract data
				// open output streams
			} catch (IOException e) {
				throw new InternalException(e);
			}
		}
		int locationOfDot = fileName.lastIndexOf(".");
		if (locationOfDot == -1 || locationOfDot == fileName.length() - 1) {
			throw new UserException(
					"The file name must have an extension (eg. '.zip')");
		}
		int location2Dot = fileName.lastIndexOf(".", locationOfDot - 1);
		if (location2Dot != -1) {
			locationOfDot = location2Dot;
		}
		String extension = fileName.substring(locationOfDot + 1);
		Contract parserContract = Contract.getNonCoreContract("bill-parser-"
				+ extension);
		try {
			PythonInterpreter interpreter = new PythonInterpreter();
			interpreter.exec(parserContract.getChargeScript());
			PyObject parserClass = interpreter.get("Parser");
			parser = (BillParser) parserClass
					.__call__(
							PyJavaType.wrapJavaObject(new InputStreamReader(is,
									"UTF-8"))).__tojava__(BillParser.class);
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		}
	}

	public void run() {
		try {
			List<RawBill> rawBills = parser.getRawBills();
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
					Hiber.setReadWrite();
					Bill bill = batch.insertBill(rawBill);
					Hiber.commit();
					Hiber.flush();
					successfulBills.add(rawBill);
					Hiber.session().evict(bill);
				} catch (HttpException e) {
					Hiber.flush();
					Map<RawBill, String> billMap = new HashMap<RawBill, String>();
					String message = null;
					if (e instanceof InternalException) {
						message = e.getStackTraceString();
					} else {
						message = e.getMessage();
					}
					billMap.put(rawBill, message);
					failedBills.add(billMap);
					Hiber.rollBack();
					Hiber.flush();
				}
			}
			if (failedBills.isEmpty()) {
				messages.add("All the bills have been successfully loaded and attached to the batch.");
			} else {
				messages.add("The import has finished, but not all bills were successfully loaded.");
			}
		} catch (InternalException e) {
			messages.add("ProgrammerException : "
					+ HttpException.getStackTraceString(e));
			throw new RuntimeException(e);
		} catch (HttpException e) {
			String msg = e.getMessage();
			if (msg == null) {
				messages.add("HttpException: "
						+ HttpException.getStackTraceString(e));
			} else {
				messages.add(msg);
			}
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

	public MonadUri getEditUri() throws HttpException {
		return getBatch().billImportsInstance().getEditUri()
				.resolve(getUriId()).append("/");
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
				.setAttribute(
						"progress",
						successfulBills == null ? parser.getProgress()
								: "There have been "
										+ successfulBills.size()
										+ " successful imports, and "
										+ failedBills.size()
										+ " failures."
										+ (isAlive ? "The thread is still alive."
												: ""));
		if (!isAlive && successfulBills != null) {
			Element failedElement = doc.createElement("failed-bills");
			importElement.appendChild(failedElement);
			Element successfulElement = doc.createElement("successful-bills");
			importElement.appendChild(successfulElement);
			for (Map<RawBill, String> billMap : failedBills) {
				for (Entry<RawBill, String> entry : billMap.entrySet()) {
					Element billRawElement = (Element) entry.getKey().toXml(
							doc, new XmlTree("registerReads").put("type"));
					failedElement.appendChild(billRawElement);
					billRawElement.appendChild(new MonadMessage(entry
							.getValue()).toXml(doc));
				}
			}
			for (RawBill billRaw : successfulBills) {
				successfulElement.appendChild(billRaw.toXml(doc, new XmlTree(
						"registerReads").put("type")));
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

	public URI getViewUri() throws HttpException {
		return null;
	}
}