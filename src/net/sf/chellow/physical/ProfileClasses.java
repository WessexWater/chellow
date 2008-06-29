package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class ProfileClasses implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("profile-classes");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public ProfileClasses() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.getUrlableRoot().getUri().resolve(getUrlId())
				.append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		for (Pc profileClass : (List<Pc>) Hiber
				.session()
				.createQuery(
						"from ProfileClass profileClass order by profileClass.code")
				.list()) {
			source.appendChild(profileClass.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Pc getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		return Pc.getProfileClass(Long.parseLong(uriId.getString()));
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}
}
