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

import java.util.Calendar;
import java.util.Date;
import java.util.List;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.data08.HhDatumRaw;
// import net.sf.chellow.monad.bo.Debug;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.types.MonadBoolean;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Channel extends PersistentEntity implements Urlable {
	private static final long serialVersionUID = 1L;

	static private HttpMethod[] httpMethods = { HttpMethod.GET };

	public static void addHhData(HhdcContract dceService, List<HhDatumRaw> dataRaw)
			throws InternalException, HttpException {
		Channel channel;
		HhDatumRaw firstDatum = dataRaw.get(0);
		try {
			channel = (Channel) Hiber
					.session()
					.createQuery(
							"select distinct channel from MpanCore mpanCore join mpanCore.supply.channels as channel where channel.isImport = :isImport and channel.isKwh = :isKwh and mpanCore.dso.code.string || mpanCore.uniquePart.string || mpanCore.checkDigit.character = :core")
					.setBoolean("isImport",
							firstDatum.getIsImport().getBoolean()).setBoolean(
							"isKwh", firstDatum.getIsKwh().getBoolean())
					.setString("core",
							firstDatum.getMpanCore().toStringNoSpaces())
					.uniqueResult();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
		if (channel == null) {
			throw new UserException("The MPAN core "
					+ firstDatum.getMpanCore() + " is not set up in Chellow.");
		}
		channel.addHhDataBlock(dceService, dataRaw);
	}

	private Supply supply;

	private boolean isImport;

	private boolean isKwh;

	public Channel() {
		setTypeName("channel");
	}

	public Channel(Supply supply, boolean isImport, boolean isKwh) {
		this.supply = supply;
		this.isImport = isImport;
		this.isKwh = isKwh;
	}

	public Supply getSupply() {
		return supply;
	}

	void setSupply(Supply supply) {
		this.supply = supply;
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

	@SuppressWarnings("unchecked")
	private void addHhDataBlock(HhdcContract dceService, List<HhDatumRaw> dataRaw)
			throws InternalException, HttpException {
		// long now = System.currentTimeMillis();
		// Debug.print("Starting method: " + (System.currentTimeMillis() -
		// now));
		HhEndDate from = dataRaw.get(0).getEndDate();
		HhEndDate to = dataRaw.get(dataRaw.size() - 1).getEndDate();
		List<SupplyGeneration> supplyGenerations = supply.getGenerations(from,
				to);
		for (SupplyGeneration generation : supplyGenerations) {
			HhdcContract actualDceService = generation.getHhdceContract(isImport,
					isKwh);
			if (actualDceService == null) {
				addChannelSnag(dceService, ChannelSnag.SNAG_DATA_IGNORED, from,
						to, false);
				return;
			}
			if (!dceService.equals(actualDceService)) {
				throw new UserException
						("Somewhere in the block of hh data between ("
								+ dataRaw.get(0)
								+ ") and ("
								+ dataRaw.get(dataRaw.size() - 1)
								+ ") and between the dates "
								+ generation.getStartDate()
								+ " and "
								+ (generation.getFinishDate() == null ? "ongoing"
										: generation.getFinishDate())
								+ " there are one or more data with a contract that is not the contract under which the data is provided.");
			}
		}
		if (supply.getGeneration(from) == null) {
			addChannelSnag(dceService, ChannelSnag.SNAG_DATA_IGNORED, from, to,
					false);
			return;
		}
		if (supply.getGeneration(to) == null) {
			addChannelSnag(dceService, ChannelSnag.SNAG_DATA_IGNORED, from, to,
					false);
			return;
		}
		List<HhDatum> data = (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and "
								+ "datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate order by datum.endDate.date")
				.setEntity("channel", this).setTimestamp("startDate",
						from.getDate())
				.setTimestamp("finishDate", to.getDate()).list();
		if (data.isEmpty()) {
			checkForMissingFromLatest(from.getPrevious());
		}
		HhEndDate siteCheckFrom = null;
		HhEndDate siteCheckTo = null;
		HhEndDate notActualFrom = null;
		HhEndDate notActualTo = null;
		HhEndDate resolveMissingFrom = null;
		HhEndDate resolveMissingTo = null;
		HhEndDate prevEndDate = null;
		int missing = 0;
		// Debug.print("Starting to go through each hh: "
		// + (System.currentTimeMillis() - now));
		HhDatum originalDatum = null;
		for (int i = 0; i < dataRaw.size(); i++) {
			// Debug.print("Start processing hh: "
			// + (System.currentTimeMillis() - now));
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
				Hiber.session().save(new HhDatum(this, datumRaw));
				// Debug.print("Saved datum: "
				// + (System.currentTimeMillis() - now));
				added = true;
				missing++;
				if (resolveMissingFrom == null) {
					resolveMissingFrom = datumRaw.getEndDate();
				}
				resolveMissingTo = datumRaw.getEndDate();
				// Debug.print("Resolved missing: "
				// + (System.currentTimeMillis() - now));
			} else if (datumRaw.getValue() != datum.getValue()
					|| (datumRaw.getStatus() == null ? datum.getStatus() != null
							: !datumRaw.getStatus().equals(datum.getStatus()))) {
				// Debug.print("About to update datum: "
				// + (System.currentTimeMillis() - now));
				originalDatum = datum;
				datum.update(datumRaw.getValue(), datumRaw.getStatus());
				altered = true;
			}
			// Debug.print("About to see if changed: "
			// + (System.currentTimeMillis() - now));
			if (added || altered) {
				if (siteCheckFrom == null) {
					siteCheckFrom = datumRaw.getEndDate();
				}
				siteCheckTo = datumRaw.getEndDate();
				if (datumRaw.getValue() < 0) {
					addChannelSnag(dceService == null ? getDceService(datumRaw
							.getEndDate()) : dceService,
							ChannelSnag.SNAG_NEGATIVE, datumRaw.getEndDate(),
							datumRaw.getEndDate(), false);
				} else if (altered && originalDatum.getValue() < 0) {
					resolveSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw
							.getEndDate());
				}
				if (!HhDatumStatus.ACTUAL.equals(datumRaw.getStatus())) {
					if (notActualFrom == null) {
						notActualFrom = datumRaw.getEndDate();
					}
					notActualTo = datumRaw.getEndDate();
				} else if (altered
						&& !originalDatum.getStatus().equals(
								HhDatumStatus.ACTUAL)) {
					resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL, datumRaw
							.getEndDate());
				}
			}
			if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
				// Debug.print("About to do site check: "
				// + (System.currentTimeMillis() - now));
				siteCheck(siteCheckFrom, siteCheckTo, supplyGenerations);
				siteCheckFrom = null;
				siteCheckTo = null;
				// Debug.print("Finished site check: "
				// + (System.currentTimeMillis() - now));
			}
			if (notActualTo != null && notActualTo.equals(prevEndDate)) {
				// Debug.print("Started not actual: "
				// + (System.currentTimeMillis() - now));
				notActualSnag(notActualFrom, notActualTo, supplyGenerations);
				// Debug.print("Finished not actual: "
				// + (System.currentTimeMillis() - now));
				notActualFrom = null;
				notActualTo = null;
			}
			if (resolveMissingTo != null
					&& resolveMissingTo.equals(prevEndDate)) {
				// Debug.print("Starting resolvedMissing: "
				// + (System.currentTimeMillis() - now));
				resolveSnag(ChannelSnag.SNAG_MISSING, resolveMissingFrom,
						resolveMissingTo);
				resolveMissingFrom = null;
				resolveMissingTo = null;
				// Debug.print("Finished resolveMissing: "
				// + (System.currentTimeMillis() - now));
			}
			prevEndDate = datumRaw.getEndDate();
		}
		if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
			// Debug.print("About to start site thing: "
			// + (System.currentTimeMillis() - now));
			siteCheck(siteCheckFrom, siteCheckTo, supplyGenerations);
			// Debug.print("About to finish site thing: "
			// + (System.currentTimeMillis() - now));
		}
		if (notActualTo != null && notActualTo.equals(prevEndDate)) {
			// Debug.print("About to start not actual: "
			// + (System.currentTimeMillis() - now));
			notActualSnag(notActualFrom, notActualTo, supplyGenerations);
			// Debug.print("About to finsih not actual: "
			// + (System.currentTimeMillis() - now));
		}
		if (resolveMissingTo != null && resolveMissingTo.equals(prevEndDate)) {
			// Debug.print("About to start resolvem: "
			// + (System.currentTimeMillis() - now));
			resolveSnag(ChannelSnag.SNAG_MISSING, resolveMissingFrom,
					resolveMissingTo);
			// Debug.print("About to finish resolvem: "
			// + (System.currentTimeMillis() - now));
		}
		// Debug.print("Finished method: " + (System.currentTimeMillis() -
		// now));
	}

	private void siteCheck(HhEndDate from, HhEndDate to,
			List<SupplyGeneration> supplyGenerations)
			throws InternalException, HttpException {
		// long now = System.currentTimeMillis();
		if (isKwh) {
			// Debug.print("Starting site check: " + (System.currentTimeMillis()
			// - now));
			for (SupplyGeneration generation : supplyGenerations) {
				Site site = generation.getSiteSupplyGenerations().iterator()
						.next().getSite();
				HhEndDate checkFrom = from.getDate().after(
						generation.getStartDate().getDate()) ? from
						: generation.getStartDate();
				HhEndDate checkTo = generation.getFinishDate() == null
						|| to.getDate().before(
								generation.getFinishDate().getDate()) ? to
						: generation.getFinishDate();
				// Debug.print("Got here 1.1.1 " + (System.currentTimeMillis() -
				// now));
				site.hhCheck(checkFrom, checkTo);
				// Debug.print("Got here 1.1.2" + (System.currentTimeMillis() -
				// now));
			}
			// Debug.print("Finishing site check: " +
			// (System.currentTimeMillis() - now));
		}
	}

	private void notActualSnag(HhEndDate from, HhEndDate to,
			List<SupplyGeneration> supplyGenerations)
			throws InternalException, HttpException {
		for (SupplyGeneration generation : supplyGenerations) {
			HhEndDate checkFrom = from.getDate().after(
					generation.getStartDate().getDate()) ? from : generation
					.getStartDate();
			HhEndDate checkTo = generation.getFinishDate() == null
					|| to.getDate()
							.before(generation.getFinishDate().getDate()) ? to
					: generation.getFinishDate();
			addChannelSnag(generation.getHhdceContract(isImport, isKwh),
					ChannelSnag.SNAG_NOT_ACTUAL, checkFrom, checkTo, false);
		}
	}

	private void addChannelSnag(HhdcContract dceService, String description,
			HhEndDate startDate, HhEndDate finishDate, boolean isResolved)
			throws InternalException, HttpException {
		SnagDateBounded.addChannelSnag(dceService, this, description,
				startDate, finishDate, isResolved);
	}

	private void resolveSnag(String description, HhEndDate date)
			throws InternalException, HttpException {
		resolveSnag(description, date, date);
	}

	@SuppressWarnings("unchecked")
	private void resolveSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws InternalException, HttpException {
		for (ChannelSnag snag : (List<ChannelSnag>) Hiber
				.session()
				.createQuery(
						"from ChannelSnag snag where snag.channel = :channel and snag.description = :description and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.dateResolved is null")
				.setEntity("channel", this).setString("description",
						description.toString()).setTimestamp("startDate",
						startDate.getDate()).setTimestamp("finishDate",
						finishDate.getDate()).list()) {
			addChannelSnag(snag.getService(), description, snag.getStartDate()
					.getDate().before(startDate.getDate()) ? startDate : snag
					.getStartDate(), snag.getFinishDate().getDate().after(
					finishDate.getDate()) ? finishDate : snag.getFinishDate(),
					true);
		}
	}

	/*
	 * public void checkForMissingFromBeginning(MonadDate to) throws
	 * ProgrammerException, UserException { checkForMissing(null,
	 * getCheckToDate()); }
	 */

	private HhEndDate getCheckToDate() throws InternalException,
			HttpException {
		HhEndDate lastSnagDate = (HhEndDate) Hiber
				.session()
				.createQuery(
						"select snag.finishDate from ChannelSnag snag where snag.channel = :channel and snag.description = :snagDescription and snag.dateResolved is null order by snag.finishDate.date desc")
				.setEntity("channel", this).setString("snagDescription",
						ChannelSnag.SNAG_MISSING).setMaxResults(1)
				.uniqueResult();
		HhEndDate finish = null;
		SupplyGeneration generation = supply.getGenerationLast();
		if (generation.getFinishDate() == null) {
			HhdcContract latestDceService = generation.getHhdceContract(isImport,
					isKwh);
			if (latestDceService == null) {
				finish = HhEndDate.roundDown(new Date());
			} else {
				finish = HhEndDate.roundDown(new Date(System
						.currentTimeMillis()
						- 1000 * 60 * 60 * 24 * latestDceService.getLag()));
				Calendar cal = MonadDate.getCalendar();
				cal.clear();
				cal.setTime(finish.getDate());
				cal.set(Calendar.MILLISECOND, 0);
				cal.set(Calendar.SECOND, 0);
				cal.set(Calendar.MINUTE, 0);
				cal.set(Calendar.HOUR_OF_DAY, 0);
				if (latestDceService.getFrequency().equals(
						ContractFrequency.DAILY)) {
					finish = new HhEndDate(cal.getTime());
				} else if (latestDceService.getFrequency().equals(
						ContractFrequency.MONTHLY)) {
					cal.set(Calendar.DAY_OF_MONTH, 1);
					finish = new HhEndDate(cal.getTime());
				} else {
					throw new InternalException("Frequency not recognized.");
				}
			}
		} else {
			finish = generation.getFinishDate();
		}
		if (lastSnagDate != null) {
			finish = finish.getDate().after(lastSnagDate.getDate()) ? finish
					: lastSnagDate;
		}
		return finish;
	}

	public void checkForMissingFromLatest() throws InternalException,
			HttpException {
		checkForMissingFromLatest(null);
	}

	/*
	 * public void checkForMissing() throws ProgrammerException, UserException {
	 * checkForMissing(null, null); }
	 */
	public void checkForMissingFromLatest(HhEndDate to)
			throws InternalException, HttpException {
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
				latestPresentDate = supply.getGenerationFirst().getStartDate();
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

	@SuppressWarnings("unchecked")
	public void checkForMissing(HhEndDate from, HhEndDate to)
			throws InternalException, HttpException {
		if (from == null) {
			from = supply.getGenerationFirst().getStartDate();
		}
		if (from.getDate().before(
				supply.getGenerationFirst().getStartDate().getDate())) {
			resolveSnag(ChannelSnag.SNAG_MISSING, from, supply
					.getGenerationFirst().getStartDate().getPrevious());
			from = supply.getGenerationFirst().getStartDate();
		}
		if (to == null) {
			to = getCheckToDate();
		}
		Calendar cal = MonadDate.getCalendar();
		HhEndDate lastGenerationDate = supply.getGenerationLast()
				.getFinishDate();
		if (lastGenerationDate != null
				&& to.getDate().after(lastGenerationDate.getDate())) {
			resolveSnag(ChannelSnag.SNAG_MISSING, lastGenerationDate.getNext(),
					to);
			to = lastGenerationDate;
		}
		if (from.getDate().after(to.getDate())) {
			return;
		}
		Query query = Hiber
				.session()
				.createQuery(
						"select count(*) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate")
				.setEntity("channel", this);
		List<SupplyGeneration> generations = supply.getGenerations(from, to);
		for (int i = 0; i < generations.size(); i++) {
			HhdcContract contractDce = generations.get(i).getHhdceContract(isImport,
					isKwh);
			HhEndDate generationStartDate = i == 0 ? from : generations.get(i)
					.getStartDate();
			HhEndDate generationFinishDate = i == generations.size() - 1 ? to
					: generations.get(i).getFinishDate();
			if (contractDce == null) {
				resolveSnag(ChannelSnag.SNAG_MISSING, generationStartDate,
						generationFinishDate);
			} else {
				HhEndDate spanStartDate = generationStartDate;
				HhEndDate spanFinishDate = generationFinishDate;

				boolean finished = false;
				while (!finished) {
					long present = (Long) query.setTimestamp("startDate",
							spanStartDate.getDate()).setTimestamp("finishDate",
							spanFinishDate.getDate()).uniqueResult();
					if (present == 0) {
						addChannelSnag(contractDce, ChannelSnag.SNAG_MISSING,
								spanStartDate, spanFinishDate, false);
						spanStartDate = HhEndDate.getNext(spanFinishDate);
						spanFinishDate = generationFinishDate;
						if (spanStartDate.getDate().after(
								spanFinishDate.getDate())) {
							finished = true;
						}
					} else {
						long shouldBe = (long) (spanFinishDate.getDate()
								.getTime()
								- spanStartDate.getDate().getTime() + 1000 * 60 * 30)
								/ (1000 * 60 * 30);
						if (present == shouldBe) {
							spanStartDate = HhEndDate.getNext(spanFinishDate);
							spanFinishDate = generationFinishDate;
							if (spanStartDate.getDate().after(
									spanFinishDate.getDate())) {
								finished = true;
							}
						} else {
							spanFinishDate = new HhEndDate(new Date(HhEndDate
									.roundDown(cal, spanStartDate.getDate()
											.getTime()
											+ (spanFinishDate.getDate()
													.getTime() - spanStartDate
													.getDate().getTime()) / 2)));
						}
					}
				}
			}
		}
	}

	private HhdcContract getDceService(HhEndDate date) throws HttpException {
		return supply.getGeneration(date).getHhdceContract(isImport, isKwh);
	}

	public void deleteData(HhEndDate from, int days)
			throws InternalException, HttpException {
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
			throw new UserException
					("There aren't any data to delete for this period.");
		}
		checkForMissing(from, to);
		this.siteCheck(from, to, supply.getGenerations(from, to));
	}

	@SuppressWarnings("unchecked")
	public List<HhDatum> getHhData(HhEndDate from, HhEndDate to) {
		return (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :from and datum.endDate.date <= :to order by datum.endDate.date")
				.setEntity("channel", this)
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate()).list();
	}

	public Element toXml(Document doc) throws InternalException,
			HttpException {
		Element element = (Element) super.toXml(doc);
		element.setAttributeNode(MonadBoolean.toXml(doc, "is-import",
				isImport));
		element.setAttributeNode(MonadBoolean
				.toXml(doc, "is-kwh", isKwh));
		return element;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element channelElement = toXml(doc);
		source.appendChild(channelElement);
		Element supplyElement = getSupply().toXml(doc);
		supplyElement.appendChild(supply.getOrganization().toXml(doc));
		channelElement.appendChild(supplyElement);
		supplyElement.appendChild(getSupply().getOrganization().toXml(doc));
		inv.sendOk(doc);
	}

	public HhData getHhDataInstance() {
		return new HhData(this);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {

	}

	public Urlable getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		Urlable child = null;
		if (HhData.URI_ID.equals(uriId)) {
			child = new HhData(this);
		}
		return child;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		inv.sendMethodNotAllowed(httpMethods);
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return supply.getChannelsInstance().getUri().resolve(getUriId());
	}

	public String toString() {
		return "Channel id: " + getId() + "is import: " + getIsImport()
				+ " is kWh: " + getIsKwh();
	}
}