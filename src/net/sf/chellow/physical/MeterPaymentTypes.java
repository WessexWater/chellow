package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MeterPaymentTypes implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("meter-payment-types");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public MeterPaymentTypes() {
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
		Element paymentTypesElement = doc.createElement("meter-payment-types");
		source.appendChild(paymentTypesElement);
		for (MeterPaymentType paymentType : (List<MeterPaymentType>) Hiber
				.session()
				.createQuery(
						"from MtcPaymentType paymentType order by paymentType.code")
				.list()) {
			paymentTypesElement.appendChild(paymentType.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public MeterPaymentType getChild(UriPathElement uriId) throws HttpException {
		return MeterPaymentType.getMeterPaymentType(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}
}
