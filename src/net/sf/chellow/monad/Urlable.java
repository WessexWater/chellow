package net.sf.chellow.monad;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public interface Urlable {
	// public UriPathElement setUriId(UriPathElement uriId) throws
	// ProgrammerException;

	public Urlable getChild(UriPathElement uriId) throws HttpException;

	public MonadUri getUri() throws HttpException;

	public void httpGet(Invocation inv) throws HttpException;

	public void httpPost(Invocation inv) throws HttpException;

	public void httpDelete(Invocation inv) throws HttpException;
}
