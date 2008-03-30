package net.sf.chellow.physical;

import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class HhData implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("hh-data");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	Channel channel;

	HhData(Channel channel) {
		this.channel = channel;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return channel.getUri().resolve(getUriId());
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(doc(inv));
	}

	@SuppressWarnings("unchecked")
	private Document doc(Invocation inv) throws ProgrammerException,
			UserException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element hhDataElement = toXML(doc);
		source.appendChild(hhDataElement);
		Element channelElement = channel.toXML(doc);
		hhDataElement.appendChild(channelElement);
		Element supplyElement = channel.getSupply().toXML(doc);
		channelElement.appendChild(supplyElement);
		supplyElement.appendChild(channel.getSupply().getOrganization().toXML(
				doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXML(doc));
		Calendar cal = GregorianCalendar.getInstance(TimeZone
				.getTimeZone("GMT"), Locale.UK);
		if (inv.hasParameter("hh-finish-date-year")) {
			Date hhFinishDate = inv.getDate("hh-finish-date");
			if (!inv.isValid()) {
				throw UserException.newInvalidParameter(doc);
			}
			cal.setTime(hhFinishDate);
			cal.add(Calendar.DAY_OF_MONTH, 1);
		} else {
			cal.set(Calendar.HOUR, 0);
			cal.set(Calendar.MINUTE, 0);
			cal.set(Calendar.SECOND, 0);
			cal.set(Calendar.MILLISECOND, 0);
		}
		for (HhDatum hhDatum : (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.endDate.date <= :to order by datum.endDate.date")
				.setEntity("channel", channel).setDate("to", cal.getTime())
				.setMaxResults(48).list()) {
			hhDataElement.appendChild(hhDatum.toXML(doc));
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		// delete hh data
		Date deleteFrom = inv.getDate("delete-from");
		int days = inv.getInteger("days");
		try {
			channel.deleteData(new HhEndDate(deleteFrom).getNext(), days);
			Hiber.commit();
		} catch (UserException e) {
			e.setDocument(doc(inv));
			throw e;
		}
		Document doc = doc(inv);
		Element docElement = doc.getDocumentElement();
		docElement.appendChild(new VFMessage("HH data deleted successfully.")
				.toXML(doc));
		inv.sendOk(doc);
	}

	public HhDatum getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		HhDatum hhDatum = (HhDatum) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.id = :datumId")
				.setEntity("channel", channel).setLong("datumId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (hhDatum == null) {
			throw UserException.newNotFound();
		}
		return hhDatum;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		return doc.createElement("hh-data");
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}
