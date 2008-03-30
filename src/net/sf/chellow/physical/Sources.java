package net.sf.chellow.physical;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;

import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Sources implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("sources");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);		}
	}

	static public Source getSource(SourceCode code) throws UserException,
			ProgrammerException {
		Source source = (Source) Hiber.session().createQuery(
				"from Source source where source.code.string = :sourceCode")
				.setString("sourceCode", code.toString()).uniqueResult();
		if (source == null) {
			throw UserException.newNotFound();
		}
		return source;
	}

	public Sources() {
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUrlPath() throws ProgrammerException, UserException {
		return Chellow.getUrlableRoot().getUri().resolve(getUriId());
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = (Element) doc.getFirstChild();

		for (Source source : Source.getSources()) {
			sourceElement.appendChild(source.toXML(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public Source getChild(UriPathElement urlId) throws UserException,
			ProgrammerException {
		Source source = (Source) Hiber.session().createQuery(
				"from Source source where source.id = :sourceId").setLong(
				"sourceId", Long.parseLong(urlId.toString())).uniqueResult();
		if (source == null) {
			throw UserException.newNotFound();
		}
		return source;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return Chellow.getUrlableRoot().getUri().resolve(getUri());
	}
}