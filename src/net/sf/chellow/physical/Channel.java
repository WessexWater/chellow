/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
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

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.util.List;

import net.sf.chellow.hhimport.HhDatumRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Channel extends PersistentEntity {
	private static final long serialVersionUID = 1L;

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

	public void siteCheck(HhEndDate from, HhEndDate to) throws HttpException {
		if (isKwh) {
			Site site = supplyGeneration.getSiteSupplyGenerations().iterator()
					.next().getSite();
			HhEndDate checkFrom = from.getDate().after(
					supplyGeneration.getStartDate().getDate()) ? from
					: supplyGeneration.getStartDate();
			HhEndDate checkTo = supplyGeneration.getFinishDate() == null
					|| to.getDate().before(
							supplyGeneration.getFinishDate().getDate()) ? to
					: supplyGeneration.getFinishDate();
			site.hhCheck(checkFrom, checkTo);
		}
	}

	public ChannelSnags snagsInstance() {
		return new ChannelSnags(this);
	}

	public void addSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		SnagDateBounded
				.addChannelSnag(this, description, startDate, finishDate);
	}

	void deleteSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		SnagDateBounded.deleteChannelSnag(this, description, startDate,
				finishDate);
	}

	public void deleteSnag(String description, HhEndDate date)
			throws HttpException {
		deleteSnag(description, date, date);
	}

	public void deleteData(HhEndDate from, HhEndDate to) throws HttpException {
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
		addSnag(ChannelSnag.SNAG_MISSING, from, to);
		siteCheck(from, to);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "channel");
		element.setAttribute("is-import", Boolean.toString(isImport));
		element.setAttribute("is-kwh", Boolean.toString(isKwh));
		return element;
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("supplyGeneration",
				new XmlTree("supply"))));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		try {
			if (inv.hasParameter("delete")) {
				supplyGeneration.deleteChannel(isImport, isKwh);
				Hiber.commit();
				inv.sendSeeOther(supplyGeneration.getChannelsInstance()
						.getUri());
			}
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public HhData getHhDataInstance() {
		return new HhData(this);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (HhData.URI_ID.equals(uriId)) {
			return new HhData(this);
		} else if (ChannelSnags.URI_ID.equals(uriId)) {
			return snagsInstance();
		} else {
			return null;
		}
	}

	public MonadUri getUri() throws HttpException {
		return supplyGeneration.getChannelsInstance().getUri().resolve(
				getUriId()).append("/");
	}

	public String toString() {
		return "Channel id: " + getId() + "is import: " + getIsImport()
				+ " is kWh: " + getIsKwh();
	}

	
	

	
/*	
	public void checkForMissing(HhEndDate from, HhEndDate to)
			throws HttpException {
		if (from == null) {
			from = supplyGeneration.getStartDate();
		}
		if (from.getDate().before(supplyGeneration.getStartDate().getDate())) {
			deleteSnag(ChannelSnag.SNAG_MISSING, from, supplyGeneration
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
			deleteSnag(ChannelSnag.SNAG_MISSING, generationEndDate.getNext(),
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
				// Debug.print("Adding a snag.");
				addChannelSnag(ChannelSnag.SNAG_MISSING, spanStartDate,
						spanFinishDate);
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
*/
	/*
	private HhEndDate getCheckToDate() throws HttpException {
		HhEndDate lastSnagDate = (HhEndDate) Hiber
				.session()
				.createQuery(
						"select snag.finishDate from ChannelSnag snag where snag.channel = :channel and snag.channel.isKwh = :isKwh and snag.channel.isImport = :isImport and snag.description = :snagDescription order by snag.finishDate.date desc")
				.setEntity("channel", this).setBoolean("isKwh", isKwh)
				.setBoolean("isImport", isImport).setString("snagDescription",
						ChannelSnag.SNAG_MISSING).setMaxResults(1)
				.uniqueResult();
		HhEndDate finish = null;
		if (supplyGeneration.getFinishDate() == null) {
			HhdcContract latestHhdcContract = HhdcContract
					.getHhdcContract(supplyGeneration.getHhdcAccount()
							.getContract().getId());
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
	*/
/*
	public void checkForMissingFromLatest(HhEndDate to) throws HttpException {
		/*
		 * if (to == null) { to = getCheckToDate(); if (to == null) { return; }
		 * }
		 */
	/*
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
		*/
		/*
		 * latestPresentDate = latestPresentDate.getNext(); if
		 * (!latestPresentDate.getDate().after(to.getDate())) {
		 * checkForMissing(latestPresentDate, to); }
		 */
	/*
		checkForMissing(latestPresentDate.getNext(), to);
	}
	*/

	@SuppressWarnings( { "unchecked", "deprecation" })
	public void addHhData(List<HhDatumRaw> dataRaw) throws HttpException {
		// long now = System.currentTimeMillis();
		HhDatumRaw firstRawDatum = dataRaw.get(0);
		HhDatumRaw lastRawDatum = dataRaw.get(dataRaw.size() - 1);
		// Debug.print("First dr = " + firstRawDatum + " cond dr " +
		// lastRawDatum);
		List<HhDatum> data = (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and "
								+ "datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate order by datum.endDate.date")
				.setEntity("channel", this).setTimestamp("startDate",
						firstRawDatum.getEndDate().getDate()).setTimestamp(
						"finishDate", lastRawDatum.getEndDate().getDate())
				.list();
		//if (data.isEmpty()) {
			// Debug.print("Starting to check for missing from latest: "
			// + (System.currentTimeMillis() - now));
		//	checkForMissingFromLatest(firstRawDatum.getEndDate().getPrevious());
		//}
		HhEndDate siteCheckFrom = null;
		HhEndDate siteCheckTo = null;
		HhEndDate notActualFrom = null;
		HhEndDate notActualTo = null;
		HhEndDate deleteMissingFrom = null;
		HhEndDate deleteMissingTo = null;
		HhEndDate lastAdditionDate = null;
		HhEndDate prevEndDate = null;
		int missing = 0;
		BigDecimal originalDatumValue = new BigDecimal(0);
		char originalDatumStatus = Character.UNASSIGNED;
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
			// Debug.print("Start processing hh: " + (System.currentTimeMillis()
			// - now));
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
				// Debug.print("About to save datum: "
				// + (System.currentTimeMillis() - now));
				try {
					stmt.setLong(1, getId());

					stmt.setTimestamp(2, new Timestamp(datumRaw.getEndDate()
							.getDate().getTime()));
					stmt.setBigDecimal(3, datumRaw.getValue());
					stmt.setString(4, Character.toString(datumRaw.getStatus()));
					stmt.addBatch();
					batchSize++;
				} catch (SQLException e) {
					throw new InternalException(e);
				}
				// Debug.print("Saved datum: "
				// + (System.currentTimeMillis() - now));
				Hiber.flush();
				lastAdditionDate = datumRaw.getEndDate();
				added = true;
				missing++;
				if (deleteMissingFrom == null) {
					deleteMissingFrom = datumRaw.getEndDate();
				}
				deleteMissingTo = datumRaw.getEndDate();
				// Debug.print("Resolved missing: "
				// + (System.currentTimeMillis() - now));
			} else if (datumRaw.getValue().doubleValue() != datum.getValue()
					.doubleValue()
					|| datumRaw.getStatus() != datum.getStatus()) {
				// Debug.print("About to update datum: " + datum + " with " +
				// datumRaw + " "
				// + (System.currentTimeMillis() - now));
				originalDatumValue = datum.getValue();
				originalDatumStatus = datum.getStatus();
				datum.update(datumRaw.getValue(), datumRaw.getStatus());
				Hiber.flush();
				altered = true;
			}
			// Debug.print("About to see if changed: "
			// + (System.currentTimeMillis() - now));
			if (added || altered) {
				if (siteCheckFrom == null) {
					siteCheckFrom = datumRaw.getEndDate();
				}
				siteCheckTo = datumRaw.getEndDate();
				if (datumRaw.getValue().doubleValue() < 0) {
					addSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw
							.getEndDate(), datumRaw.getEndDate());
				} else if (altered && originalDatumValue.doubleValue() < 0) {
					deleteSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw.getEndDate());
				}
				if (HhDatum.ACTUAL != datumRaw.getStatus()) {
					if (notActualFrom == null) {
						notActualFrom = datumRaw.getEndDate();
					}
					notActualTo = datumRaw.getEndDate();
				} else if (altered && originalDatumStatus != HhDatum.ACTUAL) {
					deleteSnag(ChannelSnag.SNAG_ESTIMATED, datumRaw
							.getEndDate());
				}
			}
			if (lastAdditionDate != null
					&& (lastAdditionDate.equals(prevEndDate) || batchSize > 100)) {
				// Debug.print("About to execute batch "
				// + (System.currentTimeMillis() - now));
				try {
					stmt.executeBatch();
					// Debug.print("Added  lines.");
					batchSize = 0;
				} catch (SQLException e) {
					throw new InternalException(e);
				}
				lastAdditionDate = null;
			}
			if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
				// Debug.print("About to do site check: "
				// + (System.currentTimeMillis() - now));
				siteCheck(siteCheckFrom, siteCheckTo);
				siteCheckFrom = null;
				siteCheckTo = null;
				// Debug.print("Finished site check: "
				// + (System.currentTimeMillis() - now));
			}
			if (notActualTo != null && notActualTo.equals(prevEndDate)) {
				// Debug.print("Started not actual: "
				// + (System.currentTimeMillis() - now));
				addSnag(ChannelSnag.SNAG_ESTIMATED, notActualFrom,
						notActualTo);
				// Debug.print("Finished not actual: "
				// + (System.currentTimeMillis() - now));
				notActualFrom = null;
				notActualTo = null;
			}
			if (deleteMissingTo != null && deleteMissingTo.equals(prevEndDate)) {
				// Debug.print("Starting resolvedMissing: "
				// + (System.currentTimeMillis() - now));
				deleteSnag(ChannelSnag.SNAG_MISSING, deleteMissingFrom,
						deleteMissingTo);
				deleteMissingFrom = null;
				deleteMissingTo = null;
				// Debug.print("Finished resolveMissing: "
				// + (System.currentTimeMillis() - now));
			}
			prevEndDate = datumRaw.getEndDate();
		}
		if (lastAdditionDate != null && lastAdditionDate.equals(prevEndDate)) {
			// Debug.print("About to execute batch 2: "
			// + (System.currentTimeMillis() - now));
			try {
				stmt.executeBatch();
			} catch (SQLException e) {
				throw new InternalException(e);
			}
			lastAdditionDate = null;
		}
		if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
			// Debug.print("About to start site thing 2: "
			// + (System.currentTimeMillis() - now));
			siteCheck(siteCheckFrom, siteCheckTo);
			// Debug.print("About to finish site thing 2: "
			// + (System.currentTimeMillis() - now));
		}
		if (notActualTo != null && notActualTo.equals(prevEndDate)) {
			// Debug.print("About to start not actual 2: "
			// + (System.currentTimeMillis() - now));
			addSnag(ChannelSnag.SNAG_ESTIMATED, notActualFrom,
					notActualTo);
			// Debug.print("About to finsih not actual 2: "
			// + (System.currentTimeMillis() - now));
		}
		if (deleteMissingTo != null && deleteMissingTo.equals(prevEndDate)) {
			// Debug.print("About to start resolvem 2: "
			// + (System.currentTimeMillis() - now));
			deleteSnag(ChannelSnag.SNAG_MISSING, deleteMissingFrom,
					deleteMissingTo);
			// Debug.print("About to finish resolvem 2: "
			// + (System.currentTimeMillis() - now));
		}
		// Debug.print("Finished method 2: " + (System.currentTimeMillis() -
		// now));
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
			deleteSnag(ChannelSnag.SNAG_MISSING, startDate, finishDate);
			deleteSnag(ChannelSnag.SNAG_DATA_IGNORED, startDate, finishDate);
			deleteSnag(ChannelSnag.SNAG_NEGATIVE, startDate, finishDate);
			deleteSnag(ChannelSnag.SNAG_ESTIMATED, startDate, finishDate);
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
				deleteSnag(ChannelSnag.SNAG_MISSING, startDate, finishDate);
				deleteSnag(ChannelSnag.SNAG_DATA_IGNORED, startDate, finishDate);
				deleteSnag(ChannelSnag.SNAG_NEGATIVE, startDate, finishDate);
				deleteSnag(ChannelSnag.SNAG_ESTIMATED, startDate, finishDate);
			}
		}
		//find date of first datum
		HhDatum firstDatum = (HhDatum) Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel order by datum.endDate.date").setEntity("contract", this).setMaxResults(1).uniqueResult();
		if (firstDatum == null) {
			addSnag(ChannelSnag.SNAG_MISSING, supplyGeneration.getStartDate(), supplyGeneration.getFinishDate());
		} else {
			if (firstDatum.getEndDate().getDate().after(supplyGeneration.getStartDate().getDate())){
			addSnag(ChannelSnag.SNAG_MISSING, supplyGeneration.getStartDate(), firstDatum.getEndDate().getPrevious());
			}
			HhDatum lastDatum = (HhDatum) Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel order by datum.endDate.date desc").setEntity("contract", this).setMaxResults(1).uniqueResult();
			if (supplyGeneration.getFinishDate() == null || lastDatum.getEndDate().getDate().before(supplyGeneration.getFinishDate().getDate())) {
				addSnag(ChannelSnag.SNAG_MISSING, lastDatum.getEndDate().getNext(), supplyGeneration.getFinishDate());
			}
		}
	}
}
