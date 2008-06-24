package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MarketRoles implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("market-roles");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public MarketRoles() {
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element rolesElement = doc.createElement("market-roles");

		source.appendChild(rolesElement);
		for (MarketRole role : (List<MarketRole>) Hiber
				.session()
				.createQuery(
						"from MarketRole role order by role.code")
				.list()) {
			rolesElement.appendChild(role.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public MonadUri getUri() throws InternalException, UserException {
		return new MonadUri("/").resolve(getUriId()).append("/");
	}

	public MarketRole getChild(UriPathElement uriId) throws HttpException {
		try {
			return MarketRole.getMarketRole(Long.parseLong(uriId.toString()));
		} catch (NumberFormatException e) {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public UriPathElement getUriId() throws InternalException {
		return URI_ID;
	}
}
