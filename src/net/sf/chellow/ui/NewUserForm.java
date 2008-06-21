package net.sf.chellow.ui;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class NewUserForm implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("new-user-form");
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException, InternalException, HttpException, DeployerException {
		inv.sendOk();
	}

	public void httpPost(Invocation inv) throws InternalException, HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	public void httpDelete(Invocation inv) throws InternalException, DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}

}
