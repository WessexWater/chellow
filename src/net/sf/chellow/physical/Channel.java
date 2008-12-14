/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.physical;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.sql.Types;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.hhimport.HhDatumRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Channel extends PersistentEntity implements Urlable {
	public static final int IMPORT_KW = 1;
	public static final int EXPORT_KW = 2;
	public static final int IMPORT_KVAR = 3;
	public static final int EXPORT_KVAR = 4;

	private static final long serialVersionUID = 1L;

	// static private HttpMethod[] httpMethods = { HttpMethod.GET };
	/*
	 * public static void addHhData(List<HhDatumRaw> dataRaw) throws
	 * HttpException { Channel channel; HhDatumRaw firstDatum = dataRaw.get(0);
	 * try { channel = (Channel) Hiber .session() .createQuery( "select distinct
	 * channel from MpanCore mpanCore join mpanCore.supply.channels as channel
	 * where channel.isImport = :isImport and channel.isKwh = :isKwh and
	 * mpanCore.dso.code.string || mpanCore.uniquePart.string ||
	 * mpanCore.checkDigit.character = :core") .setBoolean("isImport",
	 * firstDatum.getIsImport().getBoolean()).setBoolean( "isKwh",
	 * firstDatum.getIsKwh().getBoolean()) .setString("core",
	 * firstDatum.getMpanCore().toStringNoSpaces()) .uniqueResult(); } catch
	 * (HibernateException e) { throw new InternalException(e); } if (channel ==
	 * null) { throw new UserException("The MPAN core " +
	 * firstDatum.getMpanCore() + " is not set up in Chellow."); }
	 * channel.addHhDataBlock(dceService, dataRaw); }
	 */
	private SupplyGeneration supplyGeneration;

	private boolean isImport;

	private boolean isKwh;

	public Channel() {
	}

	public Channel(SupplyGeneration supplyGeneration, boolean isImport,
			boolean isKwh) {
		this.supplyGeneration = supplyGeneration;
		this.isImport = isImport;
		this.isKwh = isKwh;
	}

	public SupplyGeneration getSupplyGeneration() {
		return supplyGeneration;
	}

	void setSupplyGeneration(SupplyGeneration supplyGeneration) {
		this.supplyGeneration = supplyGeneration;
	}

	public boolean getIsImport() {
		return isImport;
	}

	void setIsImport(boolean isImport) {
		this.isImport = isImport;
	}

	public boolean getIsKwh() {
		return isKwh;
	}

	void setIsKwh(boolean isKwh) {
		this.isKwh = isKwh;
	}

	/*
	 * @SuppressWarnings("unchecked") public void addHhData(List<HhDatumRaw>
	 * dataRaw) throws HttpException { // long now = System.currentTimeMillis(); //
	 * Debug.print("Starting method: " + (System.currentTimeMillis() - // now));
	 * HhEndDate from = dataRaw.get(0).getEndDate(); HhEndDate to =
	 * dataRaw.get(dataRaw.size() - 1).getEndDate(); List<SupplyGeneration>
	 * supplyGenerations = supply.getGenerations(from, to); for
	 * (SupplyGeneration generation : supplyGenerations) { HhdcContract
	 * actualDceService = generation.getHhdceContract(isImport, isKwh); if
	 * (actualDceService == null) { addChannelSnag(dceService,
	 * ChannelSnag.SNAG_DATA_IGNORED, from, to, false); return; } if
	 * (!dceService.equals(actualDceService)) { throw new UserException
	 * ("Somewhere in the block of hh data between (" + dataRaw.get(0) + ") and (" +
	 * dataRaw.get(dataRaw.size() - 1) + ") and between the dates " +
	 * generation.getStartDate() + " and " + (generation.getFinishDate() == null ?
	 * "ongoing" : generation.getFinishDate()) + " there are one or more data
	 * with a contract that is not the contract under which the data is
	 * provided."); } } if (supply.getGeneration(from) == null) {
	 * addChannelSnag(dceService, ChannelSnag.SNAG_DATA_IGNORED, from, to,
	 * false); return; } if (supply.getGeneration(to) == null) {
	 * addChannelSnag(dceService, ChannelSnag.SNAG_DATA_IGNORED, from, to,
	 * false); return; } List<HhDatum> data = (List<HhDatum>) Hiber .session()
	 * .createQuery( "from HhDatum datum where datum.channel = :channel and " +
	 * "datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate
	 * order by datum.endDate.date") .setEntity("channel",
	 * this).setTimestamp("startDate", from.getDate())
	 * .setTimestamp("finishDate", to.getDate()).list(); if (data.isEmpty()) {
	 * checkForMissingFromLatest(from.getPrevious()); } HhEndDate siteCheckFrom =
	 * null; HhEndDate siteCheckTo = null; HhEndDate notActualFrom = null;
	 * HhEndDate notActualTo = null; HhEndDate resolveMissingFrom = null;
	 * HhEndDate resolveMissingTo = null; HhEndDate prevEndDate = null; int
	 * missing = 0; // Debug.print("Starting to go through each hh: " // +
	 * (System.currentTimeMillis() - now)); HhDatum originalDatum = null; for
	 * (int i = 0; i < dataRaw.size(); i++) { // Debug.print("Start processing
	 * hh: " // + (System.currentTimeMillis() - now)); boolean added = false;
	 * boolean altered = false; HhDatumRaw datumRaw = dataRaw.get(i); HhDatum
	 * datum = null;
	 * 
	 * if (i - missing < data.size()) { datum = data.get(i - missing); if
	 * (!datumRaw.getEndDate().equals(datum.getEndDate())) { datum = null; } }
	 * if (datum == null) { // Debug.print("About to save datum: " // +
	 * (System.currentTimeMillis() - now)); Hiber.session().save(new
	 * HhDatum(this, datumRaw)); // Debug.print("Saved datum: " // +
	 * (System.currentTimeMillis() - now)); added = true; missing++; if
	 * (resolveMissingFrom == null) { resolveMissingFrom =
	 * datumRaw.getEndDate(); } resolveMissingTo = datumRaw.getEndDate(); //
	 * Debug.print("Resolved missing: " // + (System.currentTimeMillis() -
	 * now)); } else if (datumRaw.getValue() != datum.getValue() ||
	 * (datumRaw.getStatus() == null ? datum.getStatus() != null :
	 * !datumRaw.getStatus().equals(datum.getStatus()))) { // Debug.print("About
	 * to update datum: " // + (System.currentTimeMillis() - now));
	 * originalDatum = datum; datum.update(datumRaw.getValue(),
	 * datumRaw.getStatus()); altered = true; } // Debug.print("About to see if
	 * changed: " // + (System.currentTimeMillis() - now)); if (added ||
	 * altered) { if (siteCheckFrom == null) { siteCheckFrom =
	 * datumRaw.getEndDate(); } siteCheckTo = datumRaw.getEndDate(); if
	 * (datumRaw.getValue() < 0) { addChannelSnag(dceService == null ?
	 * getDceService(datumRaw .getEndDate()) : dceService,
	 * ChannelSnag.SNAG_NEGATIVE, datumRaw.getEndDate(), datumRaw.getEndDate(),
	 * false); } else if (altered && originalDatum.getValue() < 0) {
	 * resolveSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw .getEndDate()); } if
	 * (!HhDatumStatus.ACTUAL.equals(datumRaw.getStatus())) { if (notActualFrom ==
	 * null) { notActualFrom = datumRaw.getEndDate(); } notActualTo =
	 * datumRaw.getEndDate(); } else if (altered &&
	 * !originalDatum.getStatus().equals( HhDatumStatus.ACTUAL)) {
	 * resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL, datumRaw .getEndDate()); } } if
	 * (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) { //
	 * Debug.print("About to do site check: " // + (System.currentTimeMillis() -
	 * now)); siteCheck(siteCheckFrom, siteCheckTo, supplyGenerations);
	 * siteCheckFrom = null; siteCheckTo = null; // Debug.print("Finished site
	 * check: " // + (System.currentTimeMillis() - now)); } if (notActualTo !=
	 * null && notActualTo.equals(prevEndDate)) { // Debug.print("Started not
	 * actual: " // + (System.currentTimeMillis() - now));
	 * notActualSnag(notActualFrom, notActualTo, supplyGenerations); //
	 * Debug.print("Finished not actual: " // + (System.currentTimeMillis() -
	 * now)); notActualFrom = null; notActualTo = null; } if (resolveMissingTo !=
	 * null && resolveMissingTo.equals(prevEndDate)) { // Debug.print("Starting
	 * resolvedMissing: " // + (System.currentTimeMillis() - now));
	 * resolveSnag(ChannelSnag.SNAG_MISSING, resolveMissingFrom,
	 * resolveMissingTo); resolveMissingFrom = null; resolveMissingTo = null; //
	 * Debug.print("Finished resolveMissing: " // + (System.currentTimeMillis() -
	 * now)); } prevEndDate = datumRaw.getEndDate(); } if (siteCheckTo != null &&
	 * siteCheckTo.equals(prevEndDate)) { // Debug.print("About to start site
	 * thing: " // + (System.currentTimeMillis() - now));
	 * siteCheck(siteCheckFrom, siteCheckTo, supplyGenerations); //
	 * Debug.print("About to finish site thing: " // +
	 * (System.currentTimeMillis() - now)); } if (notActualTo != null &&
	 * notActualTo.equals(prevEndDate)) { // Debug.print("About to start not
	 * actual: " // + (System.currentTimeMillis() - now));
	 * notActualSnag(notActualFrom, notActualTo, supplyGenerations); //
	 * Debug.print("About to finsih not actual: " // +
	 * (System.currentTimeMillis() - now)); } if (resolveMissingTo != null &&
	 * resolveMissingTo.equals(prevEndDate)) { // Debug.print("About to start
	 * resolvem: " // + (System.currentTimeMillis() - now));
	 * resolveSnag(ChannelSnag.SNAG_MISSING, resolveMissingFrom,
	 * resolveMissingTo); // Debug.print("About to finish resolvem: " // +
	 * (System.currentTimeMillis() - now)); } // Debug.print("Finished method: " +
	 * (System.currentTimeMillis() - // now)); }
	 */
	public void siteCheck(HhEndDate from, HhEndDate to) throws HttpException {
		if (isKwh) {
			// Debug.print("Starting site check: " + (System.currentTimeMillis()
			// - now));
			Site site = supplyGeneration.getSiteSupplyGenerations().iterator()
					.next().getSite();
			HhEndDate checkFrom = from.getDate().after(
					supplyGeneration.getStartDate().getDate()) ? from
					: supplyGeneration.getStartDate();
			HhEndDate checkTo = supplyGeneration.getFinishDate() == null
					|| to.getDate().before(
							supplyGeneration.getFinishDate().getDate()) ? to
					: supplyGeneration.getFinishDate();
			// Debug.print("Got here 1.1.1 " + (System.currentTimeMillis() -
			// now));
			site.hhCheck(checkFrom, checkTo);
			// Debug.print("Got here 1.1.2" + (System.currentTimeMillis() -
			// now));
			// Debug.print("Finishing site check: " +
			// (System.currentTimeMillis() - now));
		}
	}

	/*
	 * private void notActualSnag(HhEndDate from, HhEndDate to, List<SupplyGeneration>
	 * supplyGenerations) throws InternalException, HttpException { for
	 * (SupplyGeneration generation : supplyGenerations) { HhEndDate checkFrom =
	 * from.getDate().after( generation.getStartDate().getDate()) ? from :
	 * generation .getStartDate(); HhEndDate checkTo =
	 * generation.getFinishDate() == null || to.getDate()
	 * .before(generation.getFinishDate().getDate()) ? to :
	 * generation.getFinishDate(); addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL,
	 * checkFrom, checkTo, false); } }
	 */
	public void addChannelSnag(String description, HhEndDate startDate,
			HhEndDate finishDate, boolean isResolved) throws HttpException {
		SnagDateBounded.addChannelSnag(supplyGeneration.getHhdcContract(),
				this, description, startDate, finishDate, isResolved);
	}

	public void resolveSnag(String description, HhEndDate date)
			throws HttpException {
		resolveSnag(description, date, date);
	}

	@SuppressWarnings("unchecked")
	public void resolveSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		for (ChannelSnag snag : (List<ChannelSnag>) Hiber
				.session()
				.createQuery(
						"from ChannelSnag snag where snag.channel = :channel and snag.description = :description and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.dateResolved is null")
				.setEntity("channel", this).setString("description",
						description.toString()).setTimestamp("startDate",
						startDate.getDate()).setTimestamp("finishDate",
						finishDate.getDate()).list()) {
			addChannelSnag(
					description,
					snag.getStartDate().getDate().before(startDate.getDate()) ? startDate
							: snag.getStartDate(),
					snag.getFinishDate().getDate().after(finishDate.getDate()) ? finishDate
							: snag.getFinishDate(), true);
		}
	}

	/*
	 * public void checkForMissingFromBeginning(MonadDate to) throws
	 * ProgrammerException, UserException { checkForMissing(null,
	 * getCheckToDate()); }
	 */
	/*
	 * private HhEndDate getCheckToDate() throws HttpException { HhEndDate
	 * lastSnagDate = (HhEndDate) Hiber .session() .createQuery( "select
	 * snag.finishDate from ChannelSnag snag where snag.channel.supply = :supply
	 * and snag.channel.isKwh = :isKwh and snag.channel.isImport = :isImport and
	 * snag.description = :snagDescription and snag.dateResolved is null order
	 * by snag.finishDate.date desc") .setEntity("supply",
	 * this).setBoolean("isKwh", getIsKwh()).setBoolean("isImport",
	 * getIsImport()).setString("snagDescription",
	 * ChannelSnag.SNAG_MISSING).setMaxResults(1) .uniqueResult(); HhEndDate
	 * finish = null; SupplyGeneration generation = supply.getGenerationLast();
	 * if (generation.getFinishDate() == null) { HhdcContract latestDceService =
	 * generation.getHhdceContract(isImport, isKwh); if (latestDceService ==
	 * null) { finish = HhEndDate.roundDown(new Date()); } else { finish =
	 * HhEndDate.roundDown(new Date(System .currentTimeMillis() - 1000 * 60 * 60 *
	 * 24 * latestDceService.getLag())); Calendar cal = MonadDate.getCalendar();
	 * cal.clear(); cal.setTime(finish.getDate()); cal.set(Calendar.MILLISECOND,
	 * 0); cal.set(Calendar.SECOND, 0); cal.set(Calendar.MINUTE, 0);
	 * cal.set(Calendar.HOUR_OF_DAY, 0); if
	 * (latestDceService.getFrequency().equals( ContractFrequency.DAILY)) {
	 * finish = new HhEndDate(cal.getTime()); } else if
	 * (latestDceService.getFrequency().equals( ContractFrequency.MONTHLY)) {
	 * cal.set(Calendar.DAY_OF_MONTH, 1); finish = new HhEndDate(cal.getTime()); }
	 * else { throw new InternalException("Frequency not recognized."); } } }
	 * else { finish = generation.getFinishDate(); } if (lastSnagDate != null) {
	 * finish = finish.getDate().after(lastSnagDate.getDate()) ? finish :
	 * lastSnagDate; } return finish; }
	 * 
	 * public void checkForMissingFromLatest() throws InternalException,
	 * HttpException { checkForMissingFromLatest(null); }
	 */
	/*
	 * public void checkForMissing() throws ProgrammerException, UserException {
	 * checkForMissing(null, null); }
	 */
	/*
	 * public void checkForMissingFromLatest(HhEndDate to) throws
	 * InternalException, HttpException { /* if (to == null) { to =
	 * getCheckToDate(); if (to == null) { return; } }
	 */
	/*
	 * Date latestDatumDate = (Date) Hiber .session() .createQuery( "select
	 * max(datum.endDate.date) from HhDatum datum where datum.channel =
	 * :channel") .setEntity("channel", this).uniqueResult(); Date
	 * latestMissingDate = (Date) Hiber .session() .createQuery( "select
	 * max(snag.finishDate.date) from ChannelSnag snag where snag.channel =
	 * :channel and snag.description = :description") .setEntity("channel",
	 * this).setString("description", ChannelSnag.SNAG_MISSING).uniqueResult();
	 * HhEndDate latestPresentDate; if (latestDatumDate == null) { if
	 * (latestMissingDate == null) { latestPresentDate =
	 * supply.getGenerationFirst().getStartDate(); } else { latestPresentDate =
	 * new HhEndDate(latestMissingDate); } } else { if (latestMissingDate ==
	 * null) { latestPresentDate = new HhEndDate(latestDatumDate); } else {
	 * latestPresentDate = new HhEndDate(latestMissingDate).getDate() .after(new
	 * HhEndDate(latestDatumDate).getDate()) ? new HhEndDate( latestMissingDate) :
	 * new HhEndDate(latestDatumDate); } } /* latestPresentDate =
	 * latestPresentDate.getNext(); if
	 * (!latestPresentDate.getDate().after(to.getDate())) {
	 * checkForMissing(latestPresentDate, to); }
	 */
	/*
	 * checkForMissing(latestPresentDate.getNext(), to); }
	 */
	/*
	 * public HhdcContract getHhdcContract() throws HttpException { return
	 * (HhdcContract) getSupplyGeneration().getHhdcContract().getContract(); }
	 */

	public void deleteData(HhEndDate from, int days) throws HttpException {
		Calendar cal = MonadDate.getCalendar();
		cal.setTime(from.getDate());
		cal.add(Calendar.DAY_OF_MONTH, days);
		HhEndDate to = new HhEndDate(cal.getTime()).getPrevious();
		long numDeleted = Hiber
				.session()
				.createQuery(
						"delete from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :from and datum.endDate.date <= :to")
				.setEntity("channel", this)
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate()).executeUpdate();
		if (numDeleted == 0) {
			throw new UserException(
					"There aren't any data to delete for this period.");
		}
		supplyGeneration.getSupply().checkForMissing(from, to);
		siteCheck(from, to);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "channel");
		element.setAttribute("is-import", Boolean.toString(isImport));
		element.setAttribute("is-kwh", Boolean.toString(isKwh));
		return element;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("supplyGeneration",
				new XmlTree("supply"))));
		inv.sendOk(doc);
	}

	public HhData getHhDataInstance() {
		return new HhData(this);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		Urlable child = null;
		if (HhData.URI_ID.equals(uriId)) {
			child = new HhData(this);
		}
		return child;
	}

	public MonadUri getUri() throws HttpException {
		return supplyGeneration.getChannelsInstance().getUri().resolve(
				getUriId());
	}

	public String toString() {
		return "Channel id: " + getId() + "is import: " + getIsImport()
				+ " is kWh: " + getIsKwh();
	}

	public void checkForMissing(HhEndDate from, HhEndDate to)
			throws HttpException {
		if (from == null) {
			from = supplyGeneration.getStartDate();
		}
		if (from.getDate().before(supplyGeneration.getStartDate().getDate())) {
			resolveSnag(ChannelSnag.SNAG_MISSING, from, supplyGeneration
					.getStartDate().getPrevious());
			from = supplyGeneration.getStartDate();
		}
		if (to == null) {
			to = getCheckToDate();
		}
		Calendar cal = MonadDate.getCalendar();
		HhEndDate generationEndDate = supplyGeneration.getFinishDate();
		if (generationEndDate != null
				&& to.getDate().after(generationEndDate.getDate())) {
			resolveSnag(ChannelSnag.SNAG_MISSING, generationEndDate.getNext(),
					to);
			to = generationEndDate;
		}
		if (from.getDate().after(to.getDate())) {
			return;
		}
		Query query = Hiber
				.session()
				.createQuery(
						"select count(*) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate")
				.setEntity("channel", this);
		HhEndDate spanStartDate = from;
		HhEndDate spanFinishDate = to;
		boolean finished = false;
		while (!finished) {
			long present = (Long) query.setTimestamp("startDate",
					spanStartDate.getDate()).setTimestamp("finishDate",
					spanFinishDate.getDate()).uniqueResult();
			if (present == 0) {
				addChannelSnag(ChannelSnag.SNAG_MISSING, spanStartDate,
						spanFinishDate, false);
				spanStartDate = HhEndDate.getNext(spanFinishDate);
				spanFinishDate = to;
				if (spanStartDate.getDate().after(spanFinishDate.getDate())) {
					finished = true;
				}
			} else {
				long shouldBe = (long) (spanFinishDate.getDate().getTime()
						- spanStartDate.getDate().getTime() + 1000 * 60 * 30)
						/ (1000 * 60 * 30);
				if (present == shouldBe) {
					spanStartDate = HhEndDate.getNext(spanFinishDate);
					spanFinishDate = to;
					if (spanStartDate.getDate().after(spanFinishDate.getDate())) {
						finished = true;
					}
				} else {
					spanFinishDate = new HhEndDate(new Date(HhEndDate
							.roundDown(cal,
									spanStartDate.getDate().getTime()
											+ (spanFinishDate.getDate()
													.getTime() - spanStartDate
													.getDate().getTime()) / 2)));
				}
			}
		}
	}

	private HhEndDate getCheckToDate() throws HttpException {
		HhEndDate lastSnagDate = (HhEndDate) Hiber
				.session()
				.createQuery(
						"select snag.finishDate from ChannelSnag snag where snag.channel = :channel and snag.channel.isKwh = :isKwh and snag.channel.isImport = :isImport and snag.description = :snagDescription and snag.dateResolved is null order by snag.finishDate.date desc")
				.setEntity("channel", this).setBoolean("isKwh", isKwh)
				.setBoolean("isImport", isImport).setString("snagDescription",
						ChannelSnag.SNAG_MISSING).setMaxResults(1)
				.uniqueResult();
		HhEndDate finish = null;
		if (supplyGeneration.getFinishDate() == null) {
			HhdcContract latestHhdcContract = supplyGeneration
					.getHhdcContract();
			finish = HhEndDate.roundDown(new Date(System.currentTimeMillis()
					- 1000 * 60 * 60 * 24 * latestHhdcContract.getLag()));
			Calendar cal = MonadDate.getCalendar();
			cal.clear();
			cal.setTime(finish.getDate());
			cal.set(Calendar.MILLISECOND, 0);
			cal.set(Calendar.SECOND, 0);
			cal.set(Calendar.MINUTE, 0);
			cal.set(Calendar.HOUR_OF_DAY, 0);
			if (latestHhdcContract.getFrequency().equals(
					HhdcContract.FREQUENCY_DAILY)) {
				finish = new HhEndDate(cal.getTime());
			} else if (latestHhdcContract.getFrequency().equals(
					HhdcContract.FREQUENCY_MONTHLY)) {
				cal.set(Calendar.DAY_OF_MONTH, 1);
				finish = new HhEndDate(cal.getTime());
			} else {
				throw new InternalException("Frequency not recognized.");
			}
		} else {
			finish = supplyGeneration.getFinishDate();
		}
		if (lastSnagDate != null) {
			finish = finish.getDate().after(lastSnagDate.getDate()) ? finish
					: lastSnagDate;
		}
		return finish;
	}

	public void checkForMissingFromLatest(HhEndDate to) throws HttpException {
		/*
		 * if (to == null) { to = getCheckToDate(); if (to == null) { return; } }
		 */
		Date latestDatumDate = (Date) Hiber
				.session()
				.createQuery(
						"select max(datum.endDate.date) from HhDatum datum where datum.channel = :channel")
				.setEntity("channel", this).uniqueResult();
		Date latestMissingDate = (Date) Hiber
				.session()
				.createQuery(
						"select max(snag.finishDate.date) from ChannelSnag snag where snag.channel = :channel and snag.description = :description")
				.setEntity("channel", this).setString("description",
						ChannelSnag.SNAG_MISSING).uniqueResult();
		HhEndDate latestPresentDate;
		if (latestDatumDate == null) {
			if (latestMissingDate == null) {
				latestPresentDate = supplyGeneration.getStartDate();
			} else {
				latestPresentDate = new HhEndDate(latestMissingDate);
			}
		} else {
			if (latestMissingDate == null) {
				latestPresentDate = new HhEndDate(latestDatumDate);
			} else {
				latestPresentDate = new HhEndDate(latestMissingDate).getDate()
						.after(new HhEndDate(latestDatumDate).getDate()) ? new HhEndDate(
						latestMissingDate)
						: new HhEndDate(latestDatumDate);
			}
		}
		/*
		 * latestPresentDate = latestPresentDate.getNext(); if
		 * (!latestPresentDate.getDate().after(to.getDate())) {
		 * checkForMissing(latestPresentDate, to); }
		 */
		checkForMissing(latestPresentDate.getNext(), to);
	}

	@SuppressWarnings( { "unchecked", "deprecation" })
	public void addHhData(List<HhDatumRaw> dataRaw) throws HttpException {
		//long now = System.currentTimeMillis();
		HhDatumRaw firstRawDatum = dataRaw.get(0);
		HhDatumRaw lastRawDatum = dataRaw.get(dataRaw.size() - 1);
		//Debug.print("First dr = " + firstRawDatum + " cond dr " + lastRawDatum);
		List<HhDatum> data = (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and "
								+ "datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate order by datum.endDate.date")
				.setEntity("channel", this).setTimestamp("startDate",
						firstRawDatum.getEndDate().getDate()).setTimestamp(
						"finishDate", lastRawDatum.getEndDate().getDate())
				.list();
		if (data.isEmpty()) {
			//Debug.print("Starting to check for missing from latest: "
			// + (System.currentTimeMillis() - now));
			checkForMissingFromLatest(firstRawDatum.getEndDate().getPrevious());
		}
		HhEndDate siteCheckFrom = null;
		HhEndDate siteCheckTo = null;
		HhEndDate notActualFrom = null;
		HhEndDate notActualTo = null;
		HhEndDate resolveMissingFrom = null;
		HhEndDate resolveMissingTo = null;
		HhEndDate lastAdditionDate = null;
		HhEndDate prevEndDate = null;
		int missing = 0;
		HhDatum originalDatum = null;
		Connection con = Hiber.session().connection();
		PreparedStatement stmt;
		try {
			stmt = con
					.prepareStatement("INSERT INTO hh_datum VALUES (nextval('hh_datum_id_sequence'), ?, ?, ?, ?)");
		} catch (SQLException e1) {
			throw new InternalException(e1);
		}
		int batchSize = 0;
		for (int i = 0; i < dataRaw.size(); i++) {
			 //Debug.print("Start processing hh: " + (System.currentTimeMillis() - now));
			boolean added = false;
			boolean altered = false;
			HhDatumRaw datumRaw = dataRaw.get(i);
			HhDatum datum = null;

			if (i - missing < data.size()) {
				datum = data.get(i - missing);
				if (!datumRaw.getEndDate().equals(datum.getEndDate())) {
					datum = null;
				}
			}
			if (datum == null) {
				 //Debug.print("About to save datum: "
				 //+ (System.currentTimeMillis() - now));
				try {
					stmt.setLong(1, getId());

					stmt.setTimestamp(2, new Timestamp(datumRaw.getEndDate()
							.getDate().getTime()));
					stmt.setFloat(3, datumRaw.getValue());
					Character status = datumRaw.getStatus();
					if (status == null) {
						stmt.setNull(4, Types.CHAR);
					} else {
						stmt.setString(4, datumRaw.getStatus().toString());
					}
					stmt.addBatch();
					batchSize++;
				} catch (SQLException e) {
					throw new InternalException(e);
				}
				 //Debug.print("Saved datum: "
				 //+ (System.currentTimeMillis() - now));
				 Hiber.flush();
				lastAdditionDate = datumRaw.getEndDate();
				added = true;
				missing++;
				if (resolveMissingFrom == null) {
					resolveMissingFrom = datumRaw.getEndDate();
				}
				resolveMissingTo = datumRaw.getEndDate();
				 //Debug.print("Resolved missing: "
				 //+ (System.currentTimeMillis() - now));
			} else if (datumRaw.getValue() != datum.getValue()
					|| (datumRaw.getStatus() == null ? datum.getStatus() != null
							: !datumRaw.getStatus().equals(datum.getStatus()))) {
				 //Debug.print("About to update datum: " + datum + " with " + datumRaw + " "
				 //+ (System.currentTimeMillis() - now));
				originalDatum = datum;
				datum.update(datumRaw.getValue(), datumRaw.getStatus());
				Hiber.flush();
				altered = true;
			}
			 //Debug.print("About to see if changed: "
		 //+ (System.currentTimeMillis() - now));
			if (added || altered) {
				if (siteCheckFrom == null) {
					siteCheckFrom = datumRaw.getEndDate();
				}
				siteCheckTo = datumRaw.getEndDate();
				if (datumRaw.getValue() < 0) {
					addChannelSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw
							.getEndDate(), datumRaw.getEndDate(), false);
				} else if (altered && originalDatum.getValue() < 0) {
					resolveSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw
							.getEndDate());
				}
				if (!HhDatum.ACTUAL.equals(datumRaw.getStatus())) {
					if (notActualFrom == null) {
						notActualFrom = datumRaw.getEndDate();
					}
					notActualTo = datumRaw.getEndDate();
				} else if (altered
						&& !originalDatum.getStatus().equals(HhDatum.ACTUAL)) {
					resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL, datumRaw
							.getEndDate());
				}
			}
			if (lastAdditionDate != null
					&& (lastAdditionDate.equals(prevEndDate) || batchSize > 100)) {
				 //Debug.print("About to execute batch "
				 //+ (System.currentTimeMillis() - now));
				try {
					stmt.executeBatch();
					 //Debug.print("Added  lines.");
					batchSize = 0;
				} catch (SQLException e) {
					throw new InternalException(e);
				}
				lastAdditionDate = null;
			}
			if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
				 //Debug.print("About to do site check: "
				 //+ (System.currentTimeMillis() - now));
				siteCheck(siteCheckFrom, siteCheckTo);
				siteCheckFrom = null;
				siteCheckTo = null;
				 //Debug.print("Finished site check: "
				// + (System.currentTimeMillis() - now));
			}
			if (notActualTo != null && notActualTo.equals(prevEndDate)) {
				 //Debug.print("Started not actual: "
				 //+ (System.currentTimeMillis() - now));
				addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL, notActualFrom,
						notActualTo, false);
				 //Debug.print("Finished not actual: "
				 //+ (System.currentTimeMillis() - now));
				notActualFrom = null;
				notActualTo = null;
			}
			if (resolveMissingTo != null
					&& resolveMissingTo.equals(prevEndDate)) {
				 //Debug.print("Starting resolvedMissing: "
				 //+ (System.currentTimeMillis() - now));
				resolveSnag(ChannelSnag.SNAG_MISSING, resolveMissingFrom,
						resolveMissingTo);
				resolveMissingFrom = null;
				resolveMissingTo = null;
				 //Debug.print("Finished resolveMissing: "
				 //+ (System.currentTimeMillis() - now));
			}
			prevEndDate = datumRaw.getEndDate();
		}
		if (lastAdditionDate != null && lastAdditionDate.equals(prevEndDate)) {
			 //Debug.print("About to execute batch 2: "
			 //+ (System.currentTimeMillis() - now));
			try {
				stmt.executeBatch();
			} catch (SQLException e) {
				throw new InternalException(e);
			}
			lastAdditionDate = null;
		}
		if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
			 //Debug.print("About to start site thing 2: "
			 //+ (System.currentTimeMillis() - now));
			siteCheck(siteCheckFrom, siteCheckTo);
			 //Debug.print("About to finish site thing 2: "
			 //+ (System.currentTimeMillis() - now));
		}
		if (notActualTo != null && notActualTo.equals(prevEndDate)) {
			 //Debug.print("About to start not actual 2: "
			 //+ (System.currentTimeMillis() - now));
			addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL, notActualFrom,
					notActualTo, false);
			 //Debug.print("About to finsih not actual 2: "
			 //+ (System.currentTimeMillis() - now));
		}
		if (resolveMissingTo != null && resolveMissingTo.equals(prevEndDate)) {
			 //Debug.print("About to start resolvem 2: "
			 //+ (System.currentTimeMillis() - now));
			resolveSnag(ChannelSnag.SNAG_MISSING, resolveMissingFrom,
					resolveMissingTo);
			 //Debug.print("About to finish resolvem 2: "
			 //+ (System.currentTimeMillis() - now));
		}
		// Debug.print("Finished method 2: " + (System.currentTimeMillis() -
		 //now));
	}

	@SuppressWarnings("unchecked")
	public void onSupplyGenerationChange() throws HttpException {
		List<ChannelSnag> snags = (List<ChannelSnag>) Hiber
				.session()
				.createQuery(
						"from ChannelSnag snag where snag.channel = :channel and snag.startDate.date < snag.channel.supplyGeneration.startDate.date")
				.setEntity("channel", this).list();
		if (!snags.isEmpty()) {
			HhEndDate startDate = snags.get(0).getStartDate();
			HhEndDate finishDate = supplyGeneration.getStartDate()
					.getPrevious();
			resolveSnag(ChannelSnag.SNAG_MISSING, startDate, finishDate);
			resolveSnag(ChannelSnag.SNAG_DATA_IGNORED, startDate, finishDate);
			resolveSnag(ChannelSnag.SNAG_NEGATIVE, startDate, finishDate);
			resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL, startDate, finishDate);
		}
		if (supplyGeneration.getFinishDate() != null) {
			snags = (List<ChannelSnag>) Hiber
					.session()
					.createQuery(
							"from ChannelSnag snag where snag.channel = :channel and snag.finishDate.date > snag.channel.supplyGeneration.finishDate.date")
					.setEntity("channel", this).list();
			if (!snags.isEmpty()) {
				HhEndDate startDate = supplyGeneration.getFinishDate()
						.getNext();
				HhEndDate finishDate = snags.get(snags.size() - 1)
						.getFinishDate();
				resolveSnag(ChannelSnag.SNAG_MISSING, startDate, finishDate);
				resolveSnag(ChannelSnag.SNAG_DATA_IGNORED, startDate,
						finishDate);
				resolveSnag(ChannelSnag.SNAG_NEGATIVE, startDate, finishDate);
				resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL, startDate, finishDate);
			}
		}
	}
}