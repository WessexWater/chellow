package net.sf.chellow.ui;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
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

	public MonadUri getUri() throws HttpException {
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

				process = new GeneralImport(getUri().resolve(
						new UriPathElement(Long.toString(processId))).append(
						"/"), new InputStreamReader(fileItem.getInputStream(),
						"UTF-8"), fileName.substring(fileName.length() - 3));
			} catch (UnsupportedEncodingException e) {
				throw new InternalException(e);
			} catch (IOException e) {
				throw new InternalException(e);
			}
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
}
