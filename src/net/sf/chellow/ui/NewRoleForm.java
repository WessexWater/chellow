package net.sf.chellow.ui;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class NewRoleForm implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("new-role-form");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);		}
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException, UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException, ProgrammerException, UserException, DeployerException {
		inv.sendOk();
	}

	public void httpPost(Invocation inv) throws ProgrammerException, UserException, DesignerException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	public void httpDelete(Invocation inv) throws ProgrammerException, DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub
		
	}

}
