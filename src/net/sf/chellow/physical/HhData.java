package net.sf.chellow.physical;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import net.sf.chellow.hhimport.HhDatumRaw;
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

import org.hibernate.ScrollableResults;
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
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(MonadDate.getHoursXml(doc));
		Calendar cal = MonadDate.getCalendar();
		HhEndDate generationStartDate = channel.getSupplyGeneration()
				.getStartDate();
		HhEndDate generationFinishDate = channel.getSupplyGeneration()
				.getFinishDate();
		HhEndDate defaultDate = generationFinishDate;
		if (defaultDate == null) {
			defaultDate = HhEndDate.roundDown(new Date());
		}
		if (inv.hasParameter("year")) {
			int year = inv.getInteger("year");
			int month = inv.getInteger("month");
			if (!inv.isValid()) {
				throw new UserException(doc);
			}
			cal.set(Calendar.YEAR, year);
			cal.set(Calendar.MONTH, month - 1);
		} else {
			cal.setTime(defaultDate.getDate());
		}
		cal.set(Calendar.DAY_OF_MONTH, 1);
		cal.set(Calendar.HOUR, 0);
		cal.set(Calendar.MINUTE, 30);
		cal.set(Calendar.SECOND, 0);
		cal.set(Calendar.MILLISECOND, 0);
		Date startDate;
		try {
			startDate = cal.getTime();
		} catch (IllegalArgumentException e) {
			throw new UserException(doc, "Invalid date. " + e.getMessage());
		}
		source.appendChild(defaultDate.toXml(doc));
		cal.add(Calendar.MONTH, 1);
		cal.add(Calendar.MINUTE, -30);
		Date finishDate = cal.getTime();
		if ((generationFinishDate != null && generationFinishDate.getDate()
				.before(startDate))
				|| generationStartDate.getDate().after(finishDate)) {
			throw new UserException(doc,
					"This month doesn't overlap with the generation.");
		}
		ScrollableResults hhData = Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :from and datum.endDate.date <= :to order by datum.endDate.date")
				.setEntity("channel", channel).setDate("from", startDate)
				.setDate("to", finishDate).scroll();
		while (hhData.next()) {
			HhDatum datum = (HhDatum) hhData.get(0);
			hhDataElement.appendChild(datum.toXml(doc));
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			Date deleteFrom = inv.getDate("delete-from");
			int days = inv.getInteger("days");
			try {
				Calendar cal = MonadDate.getCalendar();
				cal.setTime(deleteFrom);
				cal.add(Calendar.DAY_OF_MONTH, days);
				HhEndDate to = new HhEndDate(cal.getTime()).getPrevious();
				channel.deleteData(new HhEndDate(deleteFrom).getNext(), to);
				Hiber.commit();
			} catch (HttpException e) {
				e.setDocument(doc(inv));
				throw e;
			}
			Document doc = doc(inv);
			Element docElement = doc.getDocumentElement();
			docElement.appendChild(new MonadMessage(
					"HH data deleted successfully.").toXml(doc));
			inv.sendOk(doc);
		} else if (inv.hasParameter("insert")) {
			Date endDate = inv.getDateTime("end");
			BigDecimal value = inv.getBigDecimal("value");
			Character status = inv.getCharacter("status");
			if (!inv.isValid()) {
				throw new UserException(doc(inv));
			}
			HhEndDate hhEndDate = new HhEndDate(endDate);
			if (Hiber
					.session()
					.createQuery(
							"from HhDatum datum where datum.channel = :channel and datum.endDate.date = :endDate").setEntity("channel", channel).setTimestamp("endDate", hhEndDate.getDate())
					.uniqueResult() != null) {
				throw new UserException(doc(inv),
						"There's already an HH datum with this time.");
			}
			List<HhDatumRaw> data = new ArrayList<HhDatumRaw>();
			data.add(new HhDatumRaw(channel.getSupplyGeneration().getMpans()
					.iterator().next().getCore().toString(), channel
					.getIsImport(), channel.getIsKwh(), hhEndDate,
					value, status));
			HhDatum.insert(data.iterator(), Arrays
					.asList(new Boolean[] { Boolean.FALSE }));
		}
		inv.sendOk(doc(inv));
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
