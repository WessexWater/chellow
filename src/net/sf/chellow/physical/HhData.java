/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/
package net.sf.chellow.physical;

import java.net.URI;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
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

	public MonadUri getEditUri() throws HttpException {
		return channel.getEditUri().resolve(getUriId()).append("/");
	}

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
		Element eraElement = channel.getEra().toXml(doc);
		channelElement.appendChild(eraElement);
		Element supplyElement = channel.getEra().getSupply().toXml(doc);
		eraElement.appendChild(supplyElement);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(MonadDate.getHoursXml(doc));
		Calendar cal = MonadDate.getCalendar();
		HhStartDate eraStartDate = channel.getEra().getStartDate();
		HhStartDate eraFinishDate = channel.getEra().getFinishDate();
		HhStartDate defaultDate = eraFinishDate;
		if (defaultDate == null) {
			defaultDate = HhStartDate.roundDown(new Date());
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
		if ((eraFinishDate != null && eraFinishDate.getDate()
				.before(startDate))
				|| eraStartDate.getDate().after(finishDate)) {
			throw new UserException(doc,
					"This month doesn't overlap with the era.");
		}
		for (HhDatum datum : (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.startDate.date >= :from and datum.startDate.date <= :to order by datum.startDate.date")
				.setEntity("channel", channel).setDate("from", startDate)
				.setDate("to", finishDate).list()) {
			hhDataElement.appendChild(datum.toXml(doc));
		}
		return doc;
	}


	public HhDatum getChild(UriPathElement uriId) throws HttpException {
		HhDatum hhDatum = (HhDatum) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.id = :datumId")
				.setEntity("channel", channel)
				.setLong("datumId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (hhDatum == null) {
			throw new NotFoundException();
		}
		return hhDatum;
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("hh-data");
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}