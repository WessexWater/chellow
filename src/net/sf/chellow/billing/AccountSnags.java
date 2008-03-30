package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Snag;

import org.hibernate.ScrollMode;
import org.hibernate.ScrollableResults;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class AccountSnags implements Urlable, XmlDescriber {
	static private final int PAGE_SIZE = 20;

	public static final UriPathElement URI_ID;
	
	static {
		try {
			URI_ID = new UriPathElement("account-snags");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	Service service;

	public AccountSnags(Service service) {
		this.service = service;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return service.getUri().resolve(getUriId()).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element snagsElement = toXML(doc);
		source.appendChild(snagsElement);
		if (service instanceof SupplierService) {
			snagsElement.appendChild(service.getXML(new XmlTree("provider",
					new XmlTree("organization")), doc));
		}
		for (AccountSnag snag : (List<AccountSnag>) Hiber
				.session()
				.createQuery(
						"from AccountSnag snag where snag.dateResolved.date is null and snag.service = :service order by snag.account.reference, snag.description, snag.startDate.date")
				.setEntity("service", service).setMaxResults(PAGE_SIZE).list()) {
			snagsElement.appendChild(snag.getXML(new XmlTree("account"), doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXML(doc));
		return doc;
	}

	@SuppressWarnings("unchecked")
	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		if (inv.hasParameter("ignore")) {
			MonadDate ignoreDate = inv.getMonadDate("ignore-date");

			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from AccountSnag snag where snag.service = :service and snag.finishDate < :ignoreDate")
					.setEntity("service", service).setTimestamp("ignoreDate",
							ignoreDate.getDate()).scroll(
							ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				AccountSnag snag = (AccountSnag) snags.get(0);
				snag.resolve(true);
				Hiber.session().flush();
				Hiber.session().clear();
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public Urlable getChild(UriPathElement urlId) throws ProgrammerException,
			UserException {
		return Snag.getSnag(urlId.getString());
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getMonadUri() throws ProgrammerException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		return doc.createElement("account-snags");
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

}
