package net.sf.chellow.ui;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.User;

public class Me implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("me");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws HttpException {
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		User user = inv.getUser();
		inv.sendFound(user.getUri());
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
}
