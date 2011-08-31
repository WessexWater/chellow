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
package net.sf.chellow.ui;

import java.io.IOException;
import java.net.URI;
import java.util.HashMap;
import java.util.Map;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class GeneralImports implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	private static long processSerial = 0;

	public static final Map<Long, GeneralImport> processes = new HashMap<Long, GeneralImport>();

	static {
		try {
			URI_ID = new UriPathElement("general-imports");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public GeneralImports() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUriId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processesElement = toXml(doc);
		source.appendChild(processesElement);
		for (GeneralImport process : processes.values()) {
			processesElement.appendChild(process.toXml(doc));
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		FileItem fileItem = inv.getFileItem("import-file");
		GeneralImport process;

		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			long processId = processSerial++;
			try {
				String fileName = fileItem.getName();
				int idx = fileName.indexOf(".");
				if (idx == -1) {
					throw new UserException(
							"The file name must contain a '.' character.");
				}
				String extension = fileName.substring(idx + 1);
				if (extension.length() != 3) {
					throw new UserException("The file name extension '" + extension
							+ "' must be 3 characters long.");
				}
				process = new GeneralImport(getEditUri().resolve(
						new UriPathElement(Long.toString(processId))).append(
						"/"), fileItem.getInputStream(), extension);
			} catch (IOException e) {
				throw new InternalException(e);
			}
			processes.put(processId, process);
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
		process.start();
		inv.sendSeeOther(process.getEditUri());
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		return processes.get(Long.parseLong(urlId.toString()));
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("general-imports");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		return null;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
