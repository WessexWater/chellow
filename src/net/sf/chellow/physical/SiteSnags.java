package net.sf.chellow.physical;

import java.util.List;

import net.sf.chellow.billing.DceService;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
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

public class SiteSnags implements Urlable, XmlDescriber {
	static private final int PAGE_SIZE = 20;

	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("site-snags");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	DceService dceService;

	public SiteSnags(DceService dceService) {
		this.dceService = dceService;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return dceService.getUri().resolve(getUriId()).append("/");
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element snagsElement = (Element) toXml(doc);
		source.appendChild(snagsElement);
		snagsElement.appendChild(dceService.toXml(doc, new XmlTree("provider",
						new XmlTree("organization"))));
		for (SiteSnag snag : (List<SiteSnag>) Hiber
				.session()
				.createQuery(
						"from SiteSnag snag where snag.dateResolved is null and snag.service = :service order by snag.site.code.string, snag.description, snag.startDate.date")
				.setEntity("service", dceService).setMaxResults(PAGE_SIZE)
				.list()) {
			snagsElement.appendChild(snag.toXml(doc, new XmlTree("site")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	@SuppressWarnings("unchecked")
	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		if (inv.hasParameter("ignore")) {
			MonadDate ignoreDate = inv.getMonadDate("ignore-date");

			ScrollableResults snags = Hiber
					.session()
					.createQuery(
							"from SiteSnag snag where snag.service = :service and snag.finishDate < :ignoreDate")
					.setEntity("service", dceService).setTimestamp(
							"ignoreDate", ignoreDate.getDate()).scroll(
							ScrollMode.FORWARD_ONLY);
			while (snags.next()) {
				SiteSnag snag = (SiteSnag) snags.get(0);
				snag.resolve(true);
				Hiber.session().flush();
				Hiber.session().clear();
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public Urlable getChild(UriPathElement urlId) throws InternalException,
			HttpException {
		return Snag.getSnag(urlId.getString());
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getMonadUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		return doc.createElement("site-snags");
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
