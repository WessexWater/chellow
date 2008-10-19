package net.sf.chellow.billing;

import java.util.HashMap;
import java.util.Map;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class InvoiceImports implements Urlable {
	static public final MonadUri URI_ID;

	static private long processSerial = 0;

	static private final Map<Long, Map<Long, InvoiceImport>> imports = new HashMap<Long, Map<Long, InvoiceImport>>();

	static {
		try {
			URI_ID = new MonadUri("invoice-imports");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Batch batch;

	public InvoiceImports(Batch batch) {
		this.batch = batch;
	}

	public MonadUri getUriId() {
		return URI_ID;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		Map<Long, InvoiceImport> batchImports = imports.get(batch.getId());
		if (batchImports == null) {
			throw new NotFoundException();
		}
		InvoiceImport billImport = batchImports.get(Long.parseLong(uriId
				.toString()));
		if (billImport == null) {
			throw new NotFoundException();
		}
		return billImport;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billImportsElement = toXML(doc);
		source.appendChild(billImportsElement);
		billImportsElement.appendChild(batch.toXml(doc, new XmlTree("contract",
				new XmlTree("party"))));
		Map<Long, InvoiceImport> batchImports = imports.get(batch.getId());
		if (batchImports != null) {
			for (InvoiceImport billImport : batchImports.values()) {
				billImportsElement.appendChild(billImport.toXml(doc));
			}
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		FileItem fileItem = inv.getFileItem("file");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			InvoiceImport importare = new InvoiceImport(batch.getId(),
					processSerial++, fileItem);
			importare.start();

			Map<Long, InvoiceImport> batchImports = imports.get(batch.getId());
			if (batchImports == null) {
				imports.put(batch.getId(), new HashMap<Long, InvoiceImport>());
			}
			batchImports = imports.get(batch.getId());
			batchImports.put(Long.parseLong(importare.getUriId().toString()),
					importare);
			inv.sendCreated(document(), importare.getUri());
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Element toXML(Document doc) throws HttpException {
		return doc.createElement("invoice-imports");
	}

	public Node getXML(XmlTree tree, Document doc) throws HttpException {
		return null;
	}

	public MonadUri getUri() throws HttpException {
		return batch.getUri().resolve(getUriId()).append("/");
	}
}