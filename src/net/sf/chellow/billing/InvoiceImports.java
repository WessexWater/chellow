package net.sf.chellow.billing;

import java.util.HashMap;
import java.util.Map;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
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
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
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

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		Map<Long, InvoiceImport> batchImports = imports.get(batch.getId());
		if (batchImports == null) {
			throw UserException.newNotFound();
		}
		InvoiceImport billImport = batchImports.get(Long.parseLong(uriId
				.toString()));
		if (billImport == null) {
			throw UserException.newNotFound();
		}
		return billImport;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();
		Element billImportsElement = (Element) toXML(doc);
		source.appendChild(billImportsElement);
		billImportsElement.appendChild(batch.getXML(new XmlTree("service",
				new XmlTree("provider", new XmlTree("organization"))), doc));
		Map<Long, InvoiceImport> batchImports = imports.get(batch.getId());
		if (batchImports != null) {
			for (InvoiceImport billImport : batchImports.values()) {
				billImportsElement.appendChild(billImport.toXML(doc));
			}
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		FileItem fileItem = inv.getFileItem("file");
		if (!inv.isValid()) {
			throw UserException.newInvalidParameter(document(), null);
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
		} catch (UserException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		return doc.createElement("invoice-imports");
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return batch.getUri().resolve(getUriId()).append("/");
	}
}