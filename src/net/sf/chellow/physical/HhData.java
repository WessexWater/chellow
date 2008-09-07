package net.sf.chellow.physical;

import java.util.Calendar;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhData extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("hh-data");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Channel channel;

	HhData(Channel channel) {
		this.channel = channel;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return channel.getUri().resolve(getUriId());
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(doc(inv));
	}

	@SuppressWarnings("unchecked")
	private Document doc(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element hhDataElement = toXml(doc);
		source.appendChild(hhDataElement);
		Element channelElement = channel.toXml(doc);
		hhDataElement.appendChild(channelElement);
		Element supplyGenerationElement = channel.getSupplyGeneration().toXml(
				doc);
		channelElement.appendChild(supplyGenerationElement);
		Element supplyElement = channel.getSupplyGeneration().getSupply()
				.toXml(doc);
		supplyGenerationElement.appendChild(supplyElement);
		supplyElement.appendChild(channel.getSupplyGeneration().getSupply()
				.getOrganization().toXml(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		Calendar cal = GregorianCalendar.getInstance(TimeZone
				.getTimeZone("GMT"), Locale.UK);
		if (inv.hasParameter("hh-finish-date-year")) {
			Date hhFinishDate = inv.getDate("hh-finish-date");
			if (!inv.isValid()) {
				throw new UserException(doc);
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
			hhDataElement.appendChild(hhDatum.toXml(doc));
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		// delete hh data
		Date deleteFrom = inv.getDate("delete-from");
		int days = inv.getInteger("days");
		try {
			channel.deleteData(new HhEndDate(deleteFrom).getNext(), days);
			Hiber.commit();
		} catch (HttpException e) {
			e.setDocument(doc(inv));
			throw e;
		}
		Document doc = doc(inv);
		Element docElement = doc.getDocumentElement();
		docElement
				.appendChild(new MonadMessage("HH data deleted successfully.")
						.toXml(doc));
		inv.sendOk(doc);
	}

	public HhDatum getChild(UriPathElement uriId) throws HttpException {
		HhDatum hhDatum = (HhDatum) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.id = :datumId")
				.setEntity("channel", channel).setLong("datumId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (hhDatum == null) {
			throw new NotFoundException();
		}
		return hhDatum;
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("hh-data");
	}
}
