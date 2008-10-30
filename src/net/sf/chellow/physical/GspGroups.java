package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class GspGroups extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("gsp-groups");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public GspGroups() {
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element goupsElement = doc.createElement("gsp-groups");

		source.appendChild(goupsElement);
		for (GspGroup type : (List<GspGroup>) Hiber
				.session()
				.createQuery(
						"from GspGroup group order by group.code")
				.list()) {
			goupsElement.appendChild(type.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public MonadUri getUri() throws HttpException {
		return new MonadUri("/").resolve(getUriId()).append("/");
	}

	public GspGroup getChild(UriPathElement uriId) throws HttpException {
		try {
			return GspGroup.getGspGroup(Long.parseLong(uriId.toString()));
		} catch (NumberFormatException e) {
			throw new NotFoundException();
		}
	}

	public UriPathElement getUriId() throws InternalException {
		return URI_ID;
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
}