package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MeterTypes implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("meter-types");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public MeterTypes() {
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
		Element meterTypesElement = doc.createElement("meter-types");
		source.appendChild(meterTypesElement);
		for (MeterType meterType : (List<MeterType>) Hiber
				.session()
				.createQuery("from MeterType meterType order by meterType.code")
				.list()) {
			meterTypesElement.appendChild(meterType.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public MeterType getChild(UriPathElement uriId) throws HttpException {
		return MeterType.getMeterType(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}
}
