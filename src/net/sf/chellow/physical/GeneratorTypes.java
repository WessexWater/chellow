package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class GeneratorTypes implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("generator-types");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public GeneratorTypes() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUrlPath() throws HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUriId());
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();

		for (GeneratorType type : (List<GeneratorType>) Hiber.session().createQuery("from GeneratorType type order by type.code").list()) {
			sourceElement.appendChild(type.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public GeneratorType getChild(UriPathElement urlId) throws HttpException {
		return GeneratorType.getGeneratorType(Long.parseLong(urlId.toString()));
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUri());
	}
}