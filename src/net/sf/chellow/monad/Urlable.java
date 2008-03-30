package net.sf.chellow.monad;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public interface Urlable {
	//public UriPathElement setUriId(UriPathElement uriId) throws ProgrammerException;

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException;

	public MonadUri getUri() throws ProgrammerException, UserException;

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException;

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException;

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException;
}
