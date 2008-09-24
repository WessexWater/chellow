package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Mtcs implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("mtcs");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Mtcs() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUrlId())
				.append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element mtcsElement = doc.createElement("mtcs");
		source.appendChild(mtcsElement);

		for (Mtc mtc : (List<Mtc>) Hiber
				.session()
				.createQuery(
						"select mtc from Mtc mtc left outer join mtc.dso dso order by mtc.code, dso.code.string")
				.list()) {
			mtcsElement.appendChild(mtc.toXml(doc, new XmlTree("dso").put(
					"meterType").put("paymentType")));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Mtc getChild(UriPathElement uriId) throws HttpException {
		return Mtc.getMtc(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}
}