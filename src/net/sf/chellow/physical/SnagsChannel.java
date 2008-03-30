package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.billing.DceService;
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


import org.hibernate.ScrollMode;
import org.hibernate.ScrollableResults;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class SnagsChannel implements Urlable, XmlDescriber {
	static private final int PAGE_SIZE = 20;

	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("snags-channel");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);		}
	}

	DceService dceService;

	public SnagsChannel(DceService dceService) {
		this.dceService = dceService;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return dceService.getUri().resolve(getUriId()).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element snagsElement = (Element) toXML(doc);
		source.appendChild(snagsElement);
		snagsElement.appendChild(dceService.getXML(new XmlTree("provider",
				new XmlTree("organization")), doc));
		List<SnagChannel> snagsChannel = (List<SnagChannel>) Hiber
				.session()
				.createQuery(
						"from SnagChannel snag where snag.dateResolved is null and snag.service = :service order by snag.channel.supply.id, snag.channel.isImport, snag.channel.isKwh, snag.description, snag.startDate.date")
				.setEntity("service", dceService).setMaxResults(PAGE_SIZE)
				.list();
		for (SnagChannel snag : snagsChannel) {
			snagsElement.appendChild(snag.getXML(new XmlTree("channel",
					new XmlTree("supply")), doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXML(doc));
		inv.sendOk(doc);
	}

	@SuppressWarnings("unchecked")
	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		if (inv.hasParameter("ignore")) {
			MonadDate ignoreDate = inv.getMonadDate("ignore-date");
			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from SnagChannel snag where dceService = :dceService and snag.finishDate < :ignoreDate")
					.setEntity("dceService", dceService).setTimestamp(
							"ignoreDate", ignoreDate.getDate()).scroll(
							ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				SnagChannel snag = (SnagChannel) snags.get(0);
				snag.resolve(true);
				Hiber.session().flush();
				Hiber.session().clear();
			}
			Hiber.close();
			inv.sendSeeOther(getUri());
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

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		return doc.createElement("snags-channel");
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

}
