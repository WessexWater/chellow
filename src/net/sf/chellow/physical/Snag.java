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
import java.util.Date;
import java.util.List;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

public class Snag extends PersistentEntity implements Cloneable {
	public static final String SNAG_NEGATIVE = "Negative values";

	public static final String SNAG_ESTIMATED = "Estimated";

	public static final String SNAG_MISSING = "Missing";

	public static final String SNAG_DATA_IGNORED = "Data ignored";

	static public Snag getSnag(Long id) throws InternalException,
			NotFoundException {
		Snag snag = (Snag) Hiber.session().get(Snag.class, id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	static public Snag getSnag(String id) throws InternalException,
			NotFoundException {
		return getSnag(Long.parseLong(id));
	}

	@SuppressWarnings("unchecked")
	public static List<Snag> getCoveredSnags(Site site, Channel channel,
			String description, HhStartDate startDate, HhStartDate finishDate) {
		Query query = null;
		if (finishDate == null) {
			if (channel != null) {
				query = Hiber
						.session()
						.createQuery(
								"from Snag snag where snag.channel = :channel and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.description = :description order by snag.startDate.date")
						.setEntity("channel", channel);
			} else {
				query = Hiber
						.session()
						.createQuery(
								"from Snag snag where snag.site = :site and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.description = :description order by snag.startDate.date")
						.setEntity("site", site);

			}
		} else {
			if (site != null) {
				query = Hiber
						.session()
						.createQuery(
								"from Snag snag where snag.site = :site and snag.startDate.date <= :finishDate and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.description = :description order by snag.startDate.date")
						.setEntity("site", site)
						.setTimestamp("finishDate", finishDate.getDate());
			} else {
				query = Hiber
						.session()
						.createQuery(
								"from Snag snag where snag.channel = :channel and snag.startDate.date <= :finishDate and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.description = :description order by snag.startDate.date")
						.setEntity("channel", channel)
						.setTimestamp("finishDate", finishDate.getDate());
			}
		}
		return (List<Snag>) query
				.setTimestamp("startDate", startDate.getDate())
				.setString("description", description).list();
	}

	public static Snag insertSnag(Site site, Channel channel,
			String description, HhStartDate startDate, HhStartDate finishDate) {
		Snag snag = new Snag(site, channel, description, startDate, finishDate);
		Hiber.session().save(snag);
		return snag;
	}

	@SuppressWarnings("unchecked")
	public static void generalImportSite(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String siteCodeStr = GeneralImport.addField(csvElement,
					"Site Code", values, 0);
			Site site = Site.getSite(siteCodeStr);
			String snagDescription = GeneralImport.addField(csvElement,
					"Snag Description", values, 1);
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 3);
			HhStartDate finishDate = new HhStartDate(finishDateStr);

			for (Snag snag : (List<Snag>) Hiber
					.session()
					.createQuery(
							"from Snag snag where snag.site = :site and snag.description = :description and snag.startDate.date <= :finishDate and (snag.finishDate is null or snag.finishDate.date >= :startDate)")
					.setEntity("site", site)
					.setString("description", snagDescription)
					.setTimestamp("startDate", startDate.getDate())
					.setTimestamp("finishDate", finishDate.getDate()).list()) {
				snag.setIsIgnored(true);
			}
		} else if (action.equals("update")) {
		}
	}

	public static void addSnag(Site site, Channel channel, String description,
			HhStartDate startDate, HhStartDate finishDate) throws HttpException {
		HhStartDate backgroundStart = startDate;
		for (Snag snag : getCoveredSnags(site, channel, description, startDate,
				finishDate)) {
			if (HhStartDate.isBefore(backgroundStart, snag.getStartDate())) {
				insertSnag(site, channel, description, backgroundStart, snag
						.getStartDate().getPrevious());
			}
			backgroundStart = snag.getFinishDate() == null ? null : snag
					.getFinishDate().getNext();
		}
		if (backgroundStart != null
				&& !HhStartDate.isAfter(backgroundStart, finishDate)) {
			insertSnag(site, channel, description, backgroundStart, finishDate);
		}
		Snag prevSnag = null;
		for (Snag snag : getCoveredSnags(site, channel, description,
				startDate.getPrevious(),
				finishDate == null ? null : finishDate.getNext())) {
			if (prevSnag != null
					&& prevSnag.getFinishDate().getNext()
							.equals(snag.getStartDate())
					&& prevSnag.getIsIgnored() == snag.getIsIgnored()) {
				prevSnag.update(prevSnag.getStartDate(), snag.getFinishDate());
				snag.delete();
			} else {
				prevSnag = snag;
			}
		}
	}

	public static void removeSnag(Site site, Channel channel,
			String description, HhStartDate startDate, HhStartDate finishDate)
			throws HttpException {
		for (Snag snag : getCoveredSnags(site, channel, description, startDate,
				finishDate)) {
			boolean outLeft = snag.getStartDate().before(startDate);
			boolean outRight = HhStartDate.isAfter(snag.getFinishDate(),
					finishDate);
			if (outLeft && outRight) {
				insertSnag(site, channel, description, finishDate.getNext(),
						snag.getFinishDate());
				snag.setFinishDate(startDate.getPrevious());
			} else if (outLeft) {
				snag.setFinishDate(startDate.getPrevious());
			} else if (outRight) {
				snag.setStartDate(finishDate.getNext());
			} else {
				snag.delete();
			}
			Hiber.flush();
		}
	}

	@SuppressWarnings("unchecked")
	public static void generalImportChannel(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String mpanCore = GeneralImport.addField(csvElement, "MPAN Core",
					values, 0);
			mpanCore = Era.normalizeMpanCore(mpanCore);
			String isImportStr = GeneralImport.addField(csvElement,
					"Is Import?", values, 1);
			boolean isImport = Boolean.parseBoolean(isImportStr);
			String isKwhStr = GeneralImport.addField(csvElement, "Is Kwh?",
					values, 2);
			boolean isKwh = Boolean.parseBoolean(isKwhStr);
			String snagDescription = GeneralImport.addField(csvElement,
					"Snag Description", values, 3);
			String startStr = GeneralImport.addField(csvElement, "From",
					values, 4);
			HhStartDate startDate = new HhStartDate(startStr);
			Era anEra = Era.getEra(mpanCore, startDate);
			Supply supply = anEra.getSupply();
			String finishStr = GeneralImport.addField(csvElement, "To", values,
					5);
			HhStartDate finishDate = null;
			if (finishStr.length() > 0) {
				finishDate = new HhStartDate(finishStr);
			}
			for (Era era : supply.getEras(startDate, finishDate)) {
				Query channelQuery = null;
				if (finishDate == null) {
					channelQuery = Hiber
							.session()
							.createQuery(
									"from Snag snag where snag.channel.era = :era and snag.channel.isImport = :isImport and snag.channel.isKwh = :isKwh and snag.isIgnored is false and snag.description = :description and (snag.finishDate is null or snag.finishDate.date >= :startDate)");
				} else {
					channelQuery = Hiber
							.session()
							.createQuery(
									"from Snag snag where snag.channel.era = :era and snag.channel.isImport = :isImport and snag.channel.isKwh = :isKwh and snag.isIgnored is false and snag.description = :description and snag.startDate.date <= :finishDate and (snag.finishDate is null or snag.finishDate.date >= :startDate)")
							.setTimestamp("finishDate", finishDate.getDate());
				}
				for (Snag snag : (List<Snag>) channelQuery
						.setEntity("era", era).setBoolean("isImport", isImport)
						.setBoolean("isKwh", isKwh)
						.setString("description", snagDescription)
						.setTimestamp("startDate", startDate.getDate()).list()) {
					snag.setIsIgnored(true);
				}
			}
		} else if (action.equals("update")) {
		}
	}

	private Date dateCreated;

	private boolean isIgnored;

	private String description;

	private HhStartDate startDate;

	private HhStartDate finishDate;

	private Site site;

	private Channel channel;

	public Snag() {
	}

	public Snag(Site site, Channel channel, String description,
			HhStartDate startDate, HhStartDate finishDate)
			throws InternalException {
		if (site == null && channel == null) {
			throw new UserException("The site and channel can't both be null.");
		}
		if (site != null && channel != null) {
			throw new UserException(
					"The site and channel can't both be present.");
		}
		this.site = site;
		this.channel = channel;

		setDateCreated(new Date());
		this.description = description;
		this.isIgnored = false;
		update(startDate, finishDate);
	}

	public Date getDateCreated() {
		return dateCreated;
	}

	void setDateCreated(Date dateCreated) {
		this.dateCreated = dateCreated;
	}

	public boolean getIsIgnored() {
		return isIgnored;
	}

	public void setIsIgnored(boolean isIgnored) {
		this.isIgnored = isIgnored;

	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public Site getSite() {
		return site;
	}

	void setSite(Site site) {
		this.site = site;
	}

	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}

	public void update(HhStartDate startDate, HhStartDate finishDate)
			throws InternalException {
		if (startDate == null) {
			throw new UserException("The snag start date can't be null.");
		}
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new InternalException(
					"Start date can't be after finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
	}

	public String toString() {
		return "Site " + site + " channel " + channel + " description "
				+ description + "Start date: " + startDate + " finish date: "
				+ finishDate;
	}

	public Element toXml(Document doc) throws HttpException {
		String elementName = null;
		if (this.site != null) {
			elementName = "site-snag";
		} else {
			elementName = "channel-snag";
		}
		Element element = super.toXml(doc, elementName);
		element.appendChild(MonadDate.toXML(dateCreated, "created", doc));
		element.setAttribute("is-ignored", Boolean.toString(isIgnored));
		element.setAttribute("description", description);
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		return element;
	}

	public MonadUri getEditUri() throws HttpException {
		if (this.site != null) {
			return Chellow.SITE_SNAGS_INSTANCE.getEditUri().resolve(getUriId())
					.append("/");
		} else {
			return null;
		}
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void delete() {
		Hiber.session().delete(this);
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		if (site == null) {
			sourceElement.appendChild(toXml(doc,
					new XmlTree("channel", new XmlTree("era", new XmlTree(
							"supply").put("hhdcContract")))));
		} else {
			sourceElement.appendChild(toXml(doc, new XmlTree("site")));
		}
		return doc;
	}
}
