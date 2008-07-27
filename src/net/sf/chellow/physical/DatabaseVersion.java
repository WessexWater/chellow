package net.sf.chellow.physical;

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class DatabaseVersion extends PersistentEntity {
	static public void setDatabaseVersion(int version) {
		DatabaseVersion databaseVersion = (DatabaseVersion) Hiber.session()
				.createQuery("from DatabaseVersion").uniqueResult();
		if (databaseVersion == null) {
			databaseVersion = new DatabaseVersion();
			databaseVersion.setVersion(version);
			Hiber.session().save(databaseVersion);
			Hiber.flush();
		} else {
			databaseVersion.setVersion(version);
			Hiber.flush();
		}
	}

	private int version;

	public DatabaseVersion() {
	}

	int getVersion() {
		return version;
	}

	void setVersion(int version) {
		this.version = version;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException, InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	public void httpPost(Invocation inv) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		
	}

	public void httpDelete(Invocation inv) throws InternalException, DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}