package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dsos implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("dsos");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Dsos() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUrlId())
				.append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element dsosElement = doc.createElement("dsos");
		source.appendChild(dsosElement);

		for (Dso dso : (List<Dso>) Hiber.session().createQuery(
				"from Dso dso order by dso.code.string").list()) {
			dsosElement.appendChild(dso.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Dso getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		Dso dso = (Dso) Hiber.session().createQuery(
				"from Dso dso where dso.id = :dsoId").setLong("dsoId",
				Long.parseLong(uriId.getString())).uniqueResult();
		if (dso == null) {
			throw new NotFoundException();
		}
		return dso;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}
}
