package net.sf.chellow.ui;

import java.util.HashMap;
import java.util.Map;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
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

public class HeaderImportProcesses implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	private static long processSerial = 0;

	public static final Map<Long, HeaderImportProcess> processes = new HashMap<Long, HeaderImportProcess>();

	static {
		try {
			URI_ID = new UriPathElement("header-data-imports");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public HeaderImportProcesses() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.HEADER_IMPORT_PROCESSES.getUri().resolve(getUriId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element processesElement = toXml(doc);
		source.appendChild(processesElement);
			for (HeaderImportProcess process : processes.values()) {
				processesElement.appendChild(process.toXml(doc));
			}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		FileItem fileItem = inv.getFileItem("import-file");
		HeaderImportProcess process;

		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			long processId = processSerial++;
			process = new HeaderImportProcess(getUri().resolve(
					new UriPathElement(Long.toString(processId))).append("/"),
					fileItem);
			processes.put(processId, process);
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
		process.start();
		inv.sendCreated(document(), process.getUri());
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		return processes.get(Long.parseLong(urlId.toString()));
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("header-import-processes");
		return element;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
		
	}
}
