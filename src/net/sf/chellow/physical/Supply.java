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

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.billing.Service;
import net.sf.chellow.data08.HhDatumRaw;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.Criteria;
import org.hibernate.HibernateException;
import org.hibernate.criterion.Restrictions;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Supply extends PersistentEntity {
	static public Supply getSupply(Long id) throws HttpException {
		Supply supply = (Supply) Hiber.session().get(Supply.class, id);
		if (supply == null) {
			throw new UserException("There is no supply with that id.");
		}
		return supply;
	}

	public static Supply getSupply(MpanCoreRaw core) throws HttpException {
		Supply supply;
		try {
			supply = (Supply) Hiber
					.session()
					.createQuery(
							"select distinct mpan.supplyGeneration.supply from Mpan mpan where mpan.dso.code.string || mpan.uniquePart.string || mpan.checkDigit.character = :core")
					.setString("core", core.toStringNoSpaces()).uniqueResult();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
		if (supply == null) {
			throw new UserException("The MPAN core " + core
					+ " is not set up in Chellow.");
		}
		return supply;
	}
	
	private Organization organization;

	private String name;

	private Source source;

	private Set<SupplyGeneration> generations;

	private Set<MpanCore> mpanCores;

	private Set<Meter> meters;

	public Supply() {
	}

	Supply(Organization organization, String name, Source source) throws HttpException {
		setOrganization(organization);
		setGenerations(new HashSet<SupplyGeneration>());
		update(name, source);
		setMpanCores(new HashSet<MpanCore>());
		setMeters(new HashSet<Meter>());
	}

	public void update(String name, Source source) throws InternalException {
		if (name == null) {
			throw new InternalException("The supply name " + "cannot be null.");
		}
		setName(name);
		setSource(source);
	}
	
	public Organization getOrganization() {
		return organization;
	}
	
	void setOrganization(Organization organization) {
		this.organization = organization;
	}

	public String getName() {
		return name;
	}

	protected void setName(String name) {
		this.name = name;
	}

	public Set<SupplyGeneration> getGenerations() {
		return generations;
	}

	void setGenerations(Set<SupplyGeneration> generations) {
		this.generations = generations;
	}

	public Set<MpanCore> getMpanCores() {
		return mpanCores;
	}

	void setMpanCores(Set<MpanCore> mpanCores) {
		this.mpanCores = mpanCores;
	}

	public Set<Meter> getMeters() {
		return meters;
	}

	void setMeters(Set<Meter> meters) {
		this.meters = meters;
	}

	public boolean hasMpanCoreRaw(MpanCoreRaw mpanCoreRaw) throws HttpException {
		boolean hasMpanCoreRaw = false;
		for (MpanCore mpanCore : mpanCores) {
			if (mpanCore.getCore().equals(mpanCoreRaw)) {
				hasMpanCoreRaw = true;
				break;
			}
		}
		return hasMpanCoreRaw;
	}

	public MpanCore addMpanCore(MpanCoreRaw mpanCoreRaw) throws HttpException {
		MpanCore mpanCore = new MpanCore(this, mpanCoreRaw);
		try {
			Hiber.session().save(mpanCore);
			mpanCores.add(mpanCore);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException("This MPAN core already exists.");
		}
		return mpanCore;
	}

	public Meter insertMeter(String meterSerialNumber) throws HttpException {
		Meter meter = new Meter(this, meterSerialNumber);
		try {
			Hiber.session().save(meter);
			meters.add(meter);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException("This meter already exists.");
		}
		return meter;
	}

	public SupplyGeneration getGenerationOngoing() {
		SupplyGeneration generation = null;

		if (getId() == null) {
			if (!getGenerations().isEmpty()) {
				generation = getGenerations().iterator().next();
			}
		} else {
			generation = (SupplyGeneration) Hiber
					.session()
					.createQuery(
							"from SupplyGeneration generation where generation.supply.id = :id and generation.finishDate is null")
					.setLong("id", getId()).uniqueResult();
		}
		return generation;
	}

	public SupplyGeneration getGenerationLast() {
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply.id = :id order by generation.finishDate.date desc")
				.setLong("id", getId()).setMaxResults(1).list().get(0);
	}

	public SupplyGeneration getGenerationFinishing(HhEndDate finishDate) {
		Criteria criteria = Hiber.session().createCriteria(
				SupplyGeneration.class);
		if (finishDate == null) {
			criteria.add(Restrictions.isNull("finishDate.date"));
		} else {
			criteria.add(Restrictions.eq("finishDate.date", finishDate
					.getDate()));
		}
		criteria.createCriteria("supply").add(Restrictions.eq("id", getId()));
		return (SupplyGeneration) criteria.uniqueResult();
	}

	@SuppressWarnings("unchecked")
	public List<SupplyGeneration> getGenerations(HhEndDate from, HhEndDate to) {
		List<SupplyGeneration> generations = null;
		if (to == null) {
			generations = (List<SupplyGeneration>) Hiber
					.session()
					.createQuery(
							"from SupplyGeneration generation where generation.supply = :supply and (generation.finishDate.date >= :fromDate or generation.finishDate.date is null) order by generation.finishDate.date")
					.setEntity("supply", this).setTimestamp("fromDate",
							from.getDate()).list();
		} else {
			generations = (List<SupplyGeneration>) Hiber
					.session()
					.createQuery(
							"from SupplyGeneration generation where generation.supply = :supply and generation.startDate.date <= :toDate and (generation.finishDate.date >= :fromDate or generation.finishDate.date is null) order by generation.finishDate.date")
					.setEntity("supply", this).setTimestamp("fromDate",
							from.getDate())
					.setTimestamp("toDate", to.getDate()).list();
		}
		return generations;
	}

	public MpanCore getMpanCore(MpanCoreRaw core) throws InternalException {
		MpanCore mpanCore = (MpanCore) Hiber
				.session()
				.createQuery(
						"from MpanCore mpanCore where mpanCore.supply = :supply and mpanCore.dso.code.string || mpanCore.uniquePart.string || mpanCore.checkDigit.character = :core")
				.setEntity("supply", this).setString("core",
						core.toStringNoSpaces()).uniqueResult();
		if (mpanCore == null) {
			throw new InternalException("Mpan isn't attached to this supply.");
		}
		return mpanCore;
	}

	public SupplyGeneration addGeneration(HhEndDate finishDate)
			throws HttpException {
		if (finishDate != null
				&& finishDate.getDate().before(
						getGenerationFirst().getStartDate().getDate())) {
			throw new UserException(
					"You can't add a generation before the first generation.");
		}
		SupplyGeneration existingGeneration = getGeneration(finishDate);
		if (existingGeneration == null) {
			existingGeneration = getGenerationLast();
		}
		Mpan existingImportMpan = existingGeneration.getImportMpan();
		Mpan existingExportMpan = existingGeneration.getExportMpan();
		SupplyGeneration newSupplyGeneration;
		Map<Site, Boolean> existingSiteMap = new HashMap<Site, Boolean>();
		Meter existingMeter = existingGeneration.getMeter();
		for (SiteSupplyGeneration siteSupplyGeneration : existingGeneration
				.getSiteSupplyGenerations()) {
			existingSiteMap.put(siteSupplyGeneration.getSite(),
					siteSupplyGeneration.getIsPhysical());
		}
		if (existingImportMpan == null) {
			newSupplyGeneration = addGeneration(existingSiteMap, existingMeter,
					null, null, null, null, false, false, false, false, null,
					existingExportMpan.getMpanRaw(), existingExportMpan
							.getMpanTop().getSsc(),
					existingExportMpan.getHhdcAccount(), existingExportMpan
							.getSupplierAccount(), existingExportMpan
							.getHasImportKwh(), existingExportMpan
							.getHasImportKvarh(), existingExportMpan
							.getHasExportKwh(), existingExportMpan
							.getHasExportKvarh(), existingExportMpan
							.getAgreedSupplyCapacity(), finishDate);
		} else if (existingExportMpan == null) {
			newSupplyGeneration = addGeneration(existingSiteMap, existingMeter,
					existingImportMpan.getMpanRaw(), existingImportMpan
							.getMpanTop().getSsc(),
					existingImportMpan.getHhdcAccount(), existingImportMpan
							.getSupplierAccount(), existingImportMpan
							.getHasImportKwh(), existingImportMpan
							.getHasImportKvarh(), existingImportMpan
							.getHasExportKwh(), existingImportMpan
							.getHasExportKvarh(), existingImportMpan
							.getAgreedSupplyCapacity(), null, null, null, null,
					false, false, false, false, null, finishDate);
		} else {
			newSupplyGeneration = addGeneration(existingSiteMap, existingMeter,
					existingImportMpan.getMpanRaw(), existingImportMpan
							.getMpanTop().getSsc(),
					existingImportMpan.getHhdcAccount(), existingImportMpan
							.getSupplierAccount(), existingImportMpan
							.getHasImportKwh(), existingImportMpan
							.getHasImportKvarh(), existingImportMpan
							.getHasExportKwh(), existingImportMpan
							.getHasExportKvarh(), existingImportMpan
							.getAgreedSupplyCapacity(), existingExportMpan
							.getMpanRaw(), existingExportMpan.getMpanTop().getSsc(),
					existingExportMpan.getHhdcAccount(), existingExportMpan
							.getSupplierAccount(), existingExportMpan
							.getHasImportKwh(), existingExportMpan
							.getHasImportKvarh(), existingExportMpan
							.getHasExportKwh(), existingExportMpan
							.getHasExportKvarh(), existingExportMpan
							.getAgreedSupplyCapacity(), finishDate);
		}
		return newSupplyGeneration;
	}
/*
	public SupplyGeneration addGeneration(Map<Site, Boolean> existingSiteMap,
			Meter meter, MpanRaw importMpanRaw, Ssc importSsc,
			Account importHhdceAccount, Account importSupplierAccount,
			boolean importHasImportKwh, boolean importHasImportKvarh,
			boolean importHasExportKwh, boolean importHasExportKvarh,
			Integer importAgreedSupplyCapacity, MpanRaw exportMpanRaw,
			Ssc exportSsc, Account exportHhdceAccount,
			Account exportSupplierAccount, boolean exportHasImportKwh,
			boolean exportHasImportKvarh, boolean exportHasExportKwh,
			boolean exportHasExportKvarh, Integer exportAgreedSupplyCapacity,
			HhEndDate finishDate) throws HttpException {
		Organization organization = existingSiteMap.keySet().iterator().next()
				.getOrganization();
		MpanTop importMpanTop = importMpanRaw == null ? null : importMpanRaw
				.getMpanTop(importSsc, finishDate == null ? new Date()
						: finishDate.getDate());
		MpanCore importMpanCore = importMpanRaw == null ? null : importMpanRaw
				.getMpanCore(organization);
		MpanTop exportMpanTop = exportMpanRaw == null ? null : exportMpanRaw
				.getMpanTop(exportSsc, finishDate == null ? new Date()
						: finishDate.getDate());
		MpanCore exportMpanCore = exportMpanRaw == null ? null : exportMpanRaw
				.getMpanCore(organization);
		return addGeneration(existingSiteMap, meter, importMpanTop,
				importMpanCore, importHhdceAccount, importSupplierAccount,
				importHasImportKwh, importHasImportKvarh, importHasExportKwh,
				importHasExportKvarh, importAgreedSupplyCapacity,
				exportMpanTop, exportMpanCore, exportHhdceAccount,
				exportSupplierAccount, exportHasImportKwh,
				exportHasImportKvarh, exportHasExportKwh, exportHasExportKvarh,
				exportAgreedSupplyCapacity, finishDate);
	}
*/
	public SupplyGeneration addGeneration(Map<Site, Boolean> siteMap,
			Meter meter, MpanRaw importMpanRaw, Ssc importSsc,
			Account importHhdceAccount, Account importAccountSupplier,
			boolean importHasImportKwh, boolean importHasImportKvarh,
			boolean importHasExportKwh, boolean importHasExportKvarh,
			Integer importAgreedSupplyCapacity, MpanRaw exportMpanRaw,
			Ssc exportSsc, Account exportHhdceAccount,
			Account exportSupplierAccount, boolean exportHasImportKwh,
			boolean exportHasImportKvarh, boolean exportHasExportKwh,
			boolean exportHasExportKvarh, Integer exportAgreedSupplyCapacity,
			HhEndDate finishDate) throws HttpException {
		if (getGenerationFinishing(finishDate) != null) {
			throw new UserException(
					"There's already a supply generation with this finish date.");
		}
		SupplyGeneration supplyGeneration = null;
		if (generations.isEmpty()) {
			supplyGeneration = new SupplyGeneration(this,
					finishDate == null ? HhEndDate.roundUp(new Date())
							: finishDate, finishDate, meter);
			generations.add(supplyGeneration);
		} else {
			SupplyGeneration existingGeneration = getGeneration(finishDate);
			if (existingGeneration == null) {
				throw new UserException(
						"You can't add a generation before the start of the supply.");
			}
			supplyGeneration = new SupplyGeneration(this, existingGeneration
					.getStartDate(), finishDate, meter);
			existingGeneration.setStartDate(HhEndDate.getNext(finishDate));
			generations.add(supplyGeneration);
		}
		Hiber.flush();
		supplyGeneration.addOrUpdateMpans(importMpanRaw, importSsc,
				importHhdceAccount, importAccountSupplier, importHasImportKwh,
				importHasImportKvarh, importHasExportKwh, importHasExportKvarh,
				importAgreedSupplyCapacity, exportMpanRaw, exportSsc,
				exportHhdceAccount, exportSupplierAccount, exportHasImportKwh,
				exportHasImportKvarh, exportHasExportKwh, exportHasExportKvarh,
				exportAgreedSupplyCapacity);
		for (Map.Entry<Site, Boolean> entry : siteMap.entrySet()) {
			supplyGeneration.attachSite(entry.getKey(), entry.getValue());
		}
		supplyGeneration.setMeter(meter);
		return supplyGeneration;
	}
	
	/*
	private HhEndDate getCheckToDate(boolean isImport, boolean isKwh)
	throws HttpException {
HhEndDate lastSnagDate = (HhEndDate) Hiber
		.session()
		.createQuery(
				"select snag.finishDate from ChannelSnag snag where snag.channel.supplyGeneration.supply = :supply and snag.channel.isKwh = :isKwh and snag.channel.isImport = :isImport and snag.description = :snagDescription and snag.dateResolved is null order by snag.finishDate.date desc")
		.setEntity("supply", this).setBoolean("isKwh", isKwh)
		.setBoolean("isImport", isImport).setString("snagDescription",
				ChannelSnag.SNAG_MISSING).setMaxResults(1)
		.uniqueResult();
HhEndDate finish = null;
SupplyGeneration generation = getGenerationLast();
if (generation.getFinishDate() == null) {
	HhdcContract latestHhdcContract = generation.getHhdcContract();
	if (latestHhdcContract == null) {
		finish = HhEndDate.roundDown(new Date());
	} else {
		finish = HhEndDate.roundDown(new Date(System
				.currentTimeMillis()
				- 1000 * 60 * 60 * 24 * latestHhdcContract.getLag()));
		Calendar cal = MonadDate.getCalendar();
		cal.clear();
		cal.setTime(finish.getDate());
		cal.set(Calendar.MILLISECOND, 0);
		cal.set(Calendar.SECOND, 0);
		cal.set(Calendar.MINUTE, 0);
		cal.set(Calendar.HOUR_OF_DAY, 0);
		if (latestHhdcContract.getFrequency().equals(
				ContractFrequency.DAILY)) {
			finish = new HhEndDate(cal.getTime());
		} else if (latestHhdcContract.getFrequency().equals(
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

*/

	public void checkForMissing(HhEndDate from, HhEndDate to)
			throws HttpException {
		for (SupplyGeneration supplyGeneration : getGenerations(from, to)) {
			supplyGeneration.checkForMissing(from, to);
		}
		/*
		checkForMissing(from, to, true, true);
		checkForMissing(from, to, true, false);
		checkForMissing(from, to, false, true);
		checkForMissing(from, to, false, false);
		*/
	}


	/*
	 * public void checkForMissing() throws ProgrammerException, UserException {
	 * for (Channel channel : channels) { channel.checkForMissing(); } }
	 */
	/*
	 * public void checkForMissing(HhEndDate from, HhEndDate to) HttpException {
	 * for (Channel channel : channels) { channel.checkForMissing(from, to); } }
	 */
	public Source getSource() {
		return source;
	}

	protected void setSource(Source source) {
		this.source = source;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supply");
		element.setAttribute("name", name);
		return element;
	}

	public SupplyGeneration getGenerationFirst() {
		// return generations.iterator().next();
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply order by generation.startDate.date")
				.setEntity("supply", this).setMaxResults(1).uniqueResult();
	}

	public SupplyGeneration getGeneration(HhEndDate date) {
		if (date == null) {
			return getGenerationFinishing(null);
		} else {
			return (SupplyGeneration) Hiber
					.session()
					.createQuery(
							"from SupplyGeneration generation where generation.supply = :supply and generation.startDate.date <= :date and (generation.finishDate.date >= :date or generation.finishDate.date is null)")
					.setEntity("supply", this).setTimestamp("date",
							date.getDate()).uniqueResult();
		}
	}

	public void deleteGeneration(SupplyGeneration generation)
			throws HttpException {
		if (getGenerations().size() == 1) {
			throw new UserException(
					"The only way to delete the last generation is to delete the entire supply.");
		}
		SupplyGeneration previousGeneration = getGenerationPrevious(generation);
		SupplyGeneration nextGeneration = getGenerationNext(generation);
		getGenerations().remove(generation);
		generation.deleteMpans();
		Hiber.session().delete(generation);
		if (previousGeneration == null) {
			nextGeneration.update(generation.getStartDate(), nextGeneration
					.getFinishDate(), nextGeneration.getMeter());
		} else {
			previousGeneration.update(previousGeneration.getStartDate(),
					generation.getFinishDate(), previousGeneration.getMeter());
		}
		checkAfterUpdate(generation.getStartDate(), generation
				.getFinishDate());
	}

	@SuppressWarnings("unchecked")
	public void checkAfterUpdate(HhEndDate from, HhEndDate to)
			throws HttpException {
		Hiber.flush();
		Date supplyStartDate = getGenerationFirst().getStartDate().getDate();
		Date supplyFinishDate = getGenerationLast().getFinishDate() == null ? null
				: getGenerationLast().getFinishDate().getDate();
		/*
		if (checkData) {
			// Check that there aren't any data without contracts.
			if (from.getDate().before(supplyStartDate)
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.supply  = :supply and datum.endDate.date < :date")
							.setEntity("supply", this).setTimestamp("date",
									supplyStartDate).uniqueResult()) > 0) {
				throw new UserException(
						"There are half-hourly data before the start of the updated supply.");
			}
			if (supplyFinishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.supply  = :supply and datum.endDate.date > :date")
							.setEntity("supply", this).setTimestamp("date",
									supplyFinishDate).uniqueResult()) > 0) {
				throw new UserException(
						"There are half-hourly data after the end of the updated supply.");
			}
			Query query = Hiber
					.session()
					.createQuery(
							"select count(*) from HhDatum datum where datum.channel  = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate");
			for (SupplyGeneration generation : getGenerations(from, to)) {
				for (Channel channel : generation.getChannels()) {
					if (generation.getHhdcContract() == null) {
						HhEndDate generationFinishDate = generation
								.getFinishDate();
						if (generationFinishDate == null) {
							if (((Long) Hiber
									.session()
									.createQuery(
											"select count(*) from HhDatum datum where datum.channel  = :channel and datum.endDate.date >= :startDate")
									.setEntity("channel", channel)
									.setTimestamp("startDate",
											generation.getStartDate().getDate())
									.uniqueResult()) > 0) {
								throw new UserException(
										"There are half-hourly data in "
												+ channel
												+ " and generation "
												+ generation
												+ " without a contract with the updated supply.");
							}
						} else {
							if (((Long) query
									.setEntity("channel", channel)
									.setTimestamp("startDate",
											generation.getStartDate().getDate())
									.setTimestamp(
											"finishDate",
											generation.getFinishDate()
													.getDate()).uniqueResult()) > 0) {
								throw new UserException(
										"There are half-hourly data without a contract, associated with the channel "
												+ channel.getId()
												+ " and supply generation '"
												+ generation.getId() + "' .");
							}
						}
					}
				}
			}
			if (from.getDate().before(supplyStartDate)) {
				for (ChannelSnag snag : (List<ChannelSnag>) Hiber
						.session()
						.createQuery(
								"from ChannelSnag snag where snag.channel.supply  = :supply and snag.finishDate.date >= :startDate and snag.startDate.date <= :finishDate")
						.setEntity("supply", this).setTimestamp("startDate",
								from.getDate()).setTimestamp(
								"finishDate",
								new HhEndDate(supplyStartDate).getPrevious()
										.getDate()).list()) {
					snag.resolve(false);
				}
			}
			if (supplyFinishDate != null) {
				for (ChannelSnag snag : (List<ChannelSnag>) Hiber
						.session()
						.createQuery(
								"from ChannelSnag snag where snag.channel.supply  = :supply and snag.finishDate.date >= :startDate")
						.setEntity("supply", this).setTimestamp("startDate",
								from.getDate()).list()) {
					snag.resolve(false);
				}
			}
			for (SupplyGeneration generation : getGenerations(from, to)) {
				for (Channel channel : generation.getChannels()) {
					HhdcContract hhdcContract = generation.getHhdcContract();
					HhEndDate generationFinishDate = generation.getFinishDate();
					for (ChannelSnag snag : (List<ChannelSnag>) (generationFinishDate == null ? Hiber
							.session()
							.createQuery(
									"from ChannelSnag snag where snag.channel  = :channel and snag.finishDate.date >= :startDate")
							.setEntity("channel", channel).setTimestamp(
									"startDate",
									generation.getStartDate().getDate()).list()
							: Hiber
									.session()
									.createQuery(
											"from ChannelSnag snag where snag.channel  = :channel and snag.finishDate.date >= :startDate and snag.startDate.date <= :finishDate")
									.setEntity("channel", channel)
									.setTimestamp("startDate",
											generation.getStartDate().getDate())
									.setTimestamp(
											"finishDate",
											generation.getFinishDate()
													.getDate()).list())) {
						if (!snag.getContract().equals(hhdcContract)) {
							snag.resolve(false);
						}
					}
				}
			}
			checkForMissing(from, to);
		}
*/
		// HH data

		if (from.getDate().before(supplyStartDate)
				&& ((Long) Hiber
						.session()
						.createQuery(
								"select count(*) from HhDatum datum where datum.channel.supplyGeneration.supply  = :supply and datum.endDate.date < :date")
						.setEntity("supply", this).setTimestamp("date",
								supplyStartDate).uniqueResult()) > 0) {
			throw new UserException(
					"There are HH data before the start of the updated supply.");
		}
		if (supplyFinishDate != null
				&& ((Long) Hiber
						.session()
						.createQuery(
								"select count(*) from HhDatum datum where datum.channel.supplyGeneration.supply  = :supply and datum.endDate.date > :date")
						.setEntity("supply", this).setTimestamp("date",
								supplyFinishDate).uniqueResult()) > 0) {
			throw new UserException(
					"There are HH data after the end of the updated supply.");
		}
		for (SupplyGeneration generation : getGenerations(from, to)) {
			for (HhDatum datum : (List<HhDatum>) Hiber
					.session()
					.createQuery(
							"from HhDatum datum where datum.channel.supplyGeneration = :supplyGeneration and (datum.endDate.date < datum.channel.supplyGeneration.startDate.date or (datum.channel.supplyGeneration.finishDate.date is not null and datum.endDate.date < datum.channel.supplyGeneration.finishDate.date))")
					.setEntity("supplyGeneration", generation).list()) {
				Channel channel = datum.getChannel();
				HhEndDate endDate = datum.getEndDate();
				Channel targetChannel = getGeneration(endDate).getChannel(
						channel.getIsImport(), channel.getIsKwh());
				if (targetChannel == null) {
					throw new UserException(
							"There is no channel for the HH datum: "
									+ datum.toString() + " to move to.");
				}
				datum.setChannel(targetChannel);
				if (datum.getValue() < 0) {
					targetChannel.addChannelSnag(ChannelSnag.SNAG_NEGATIVE,
							endDate, endDate, false);
				}
				if (!datum.getStatus().equals(HhDatumRaw.ACTUAL)) {
					targetChannel.addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL,
							endDate, endDate, false);
				}
				channel.resolveSnag(ChannelSnag.SNAG_NEGATIVE, endDate);
				channel.resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL, endDate);
			}
		}
		checkForMissing(from, to);
		for (SupplyGeneration generation : getGenerations(from, to)) {
			for (ChannelSnag snag : (List<ChannelSnag>) Hiber
					.session()
					.createQuery(
							"from ChannelSnag snag where snag.channel.supplyGeneration = :supplyGeneration and (snag.finishDate.date < snag.channel.supplyGeneration.startDate.date or (snag.channel.supplyGeneration.finishDate.date is not null and snag.startDate.date > snag.channel.supplyGeneration.finishDate.date))")
					.setEntity("supplyGeneration", generation).list()) {
				ChannelSnag.deleteChannelSnag(snag);
			}
		}
		// Register reads

		if (from.getDate().before(supplyStartDate)
				&& ((Long) Hiber
						.session()
						.createQuery(
								"select count(*) from RegisterRead read where read.mpan.supplyGeneration.supply  = :supply and read.presentDate.date < :date")
						.setEntity("supply", this).setTimestamp("date",
								supplyStartDate).uniqueResult()) > 0) {
			throw new UserException(
					"There are register reads before the start of the updated supply.");
		}
		if (supplyFinishDate != null
				&& ((Long) Hiber
						.session()
						.createQuery(
								"select count(*) from RegisterRead read where read.mpan.supplyGeneration.supply  = :supply and read.presentDate.date > :date")
						.setEntity("supply", this).setTimestamp("date",
								supplyFinishDate).uniqueResult()) > 0) {
			throw new UserException(
					"There are register reads after the end of the updated supply.");
		}
		for (SupplyGeneration generation : getGenerations(from, to)) {
			for (RegisterRead read : (List<RegisterRead>) Hiber
					.session()
					.createQuery(
							"from RegisterRead read where read.mpan.supplyGeneration = :supplyGeneration")
					.setEntity("supplyGeneration", generation).list()) {
				if (read.getPresentDate().getDate().before(
						generation.getStartDate().getDate())
						|| (generation.getFinishDate() != null && read
								.getPresentDate().getDate().after(
										generation.getFinishDate().getDate()))) {
					SupplyGeneration targetGeneration = getGeneration(read
							.getPresentDate());
					Mpan targetMpan = read.getMpan().getMpanTop().getLlfc()
							.getIsImport() ? targetGeneration.getImportMpan()
							: targetGeneration.getExportMpan();
					if (targetMpan == null) {
						throw new UserException(
								"There's no MPAN for the meter read to move to.");
					}
					read.setMpan(targetMpan);
				}
			}
		}
		// check doesn't have superfluous meters
		List<Meter> metersToRemove = new ArrayList<Meter>();
		for (Meter meter : meters) {
			if ((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from SupplyGeneration generation where generation.meter = :meter")
					.setEntity("meter", meter).uniqueResult() == 0) {
				metersToRemove.add(meter);
			}
		}
		for (Meter meterToRemove : metersToRemove) {
			meters.remove(meterToRemove);
		}
	}

	public SupplyGeneration getGenerationPrevious(SupplyGeneration generation)
			throws HttpException {
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply and generation.finishDate.date = :generationFinishDate")
				.setEntity("supply", this).setTimestamp("generationFinishDate",
						generation.getStartDate().getPrevious().getDate())
				.uniqueResult();
	}

	public SupplyGeneration getGenerationNext(SupplyGeneration generation)
			throws HttpException {
		if (generation.getFinishDate() == null) {
			return null;
		}
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply and generation.startDate.date = :generationStartDate")
				.setEntity("supply", this).setTimestamp("generationStartDate",
						generation.getFinishDate().getNext().getDate())
				.uniqueResult();
	}

	private void addSourcesXML(Element element) throws HttpException {
		for (Source source : Source.getSources()) {
			element.appendChild(source.toXml(element.getOwnerDocument()));
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element supplyElement = (Element) toXml(doc, new XmlTree("generations",
				new XmlTree("mpans", new XmlTree("mpanCore").put("mpanTop",
						new XmlTree("llfc", new XmlTree("voltageLevel")))))
				.put("mpanCores"));
		source.appendChild(supplyElement);
		supplyElement.appendChild(getOrganization().toXml(doc));
		addSourcesXML(source);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		try {
			if (inv.hasParameter("delete")) {
				Document doc = document();
				Element source = doc.getDocumentElement();

				source.appendChild(toXml(doc));
				Organization org = getOrganization();
				delete(this);
				Hiber.commit();
				source.appendChild(new MonadMessage(
						"Supply deleted successfully.").toXml(doc));
				inv.sendSeeOther(org.getUri());
			} else {
				String name = inv.getString("name");
				Long sourceId = inv.getLong("source-id");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				update(name, Source.getSource(sourceId));
				Hiber.commit();
				inv.sendOk(document());
			}
		} catch (HttpException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws HttpException {
		return getOrganization().suppliesInstance().getUrlPath().resolve(
				getUriId()).append("/");
	}

	/*
	 * public SupplyGeneration findSupplyGeneration(MonadLong generationId) {
	 * return (SupplyGeneration) Hiber .session() .createQuery( "from
	 * SupplyGeneration generation where generation.supply = :supply and
	 * generation.id = :generationId") .setEntity("supply",
	 * this).setLong("generationId", generationId.getLong()).uniqueResult(); }
	 */
	public SupplyGenerations getSupplyGenerationsInstance() {
		return new SupplyGenerations(this);
	}

	public void httpPostSupplyGeneration(Invocation inv) throws HttpException {
		Boolean isOngoing = inv.getBoolean("isOngoing");
		HhEndDate finishDate = null;
		if (!isOngoing) {
			finishDate = HhEndDate.roundDown(inv.getDate("finishDate"));
		}
		addGeneration(finishDate);
		Hiber.commit();
		inv.sendOk(document());
	}

	/*
	 * public Channel getChannel(UriPathElement urlId) throws HttpException {
	 * Channel channel = (Channel) Hiber .session() .createQuery( "from Channel
	 * channel where channel.supply = :supply and channel.id = :channelId")
	 * .setEntity("supply", this).setLong("channelId",
	 * Long.parseLong(urlId.getString())).uniqueResult(); if (channel == null) {
	 * throw new NotFoundException(); } return channel; }
	 */
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (SupplyGenerations.URI_ID.equals(uriId)) {
			return new SupplyGenerations(this);
		} else {
			throw new NotFoundException();
		}
	}
/*
	@SuppressWarnings("unchecked")
	public void addHhData(HhdcContract contract, List<HhDatumRaw> dataRaw)
			throws HttpException {
		// long now = System.currentTimeMillis();
		// Debug.print("Starting method: " + (System.currentTimeMillis() -
		// now));

		HhEndDate from = dataRaw.get(0).getEndDate();
		HhEndDate to = dataRaw.get(dataRaw.size() - 1).getEndDate();
		boolean isImport = dataRaw.get(0).getIsImport();
		boolean isKwh = dataRaw.get(0).getIsKwh();
		if (getGeneration(from) == null) {
			throw new UserException("HH data has been ignored from "
					+ dataRaw.toString() + " to " + to + ".");
		}
		if (getGeneration(to) == null) {
			throw new UserException("HH data has been ignored from "
					+ dataRaw.toString() + " to " + to + ".");
		}
		List<SupplyGeneration> supplyGenerations = getGenerations(from, to);
		for (SupplyGeneration generation : supplyGenerations) {
			Channel channel = generation.getChannel(isImport, isKwh);
			HhdcContract actualHhdcContract = generation.getHhdcContract();
			if (channel == null) {
				throw new UserException("HH data has been ignored from "
						+ dataRaw.toString() + " to " + to + ".");
			}
			if (!contract.equals(actualHhdcContract)) {
				throw new UserException(
						"Somewhere in the block of hh data between ("
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
			List<HhDatum> data = (List<HhDatum>) Hiber
					.session()
					.createQuery(
							"from HhDatum datum where datum.channel = :channel and "
									+ "datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate order by datum.endDate.date")
					.setEntity("channel", channel).setTimestamp("startDate",
							generation.getStartDate().getDate()).setTimestamp(
							"finishDate", generation.getFinishDate().getDate())
					.list();
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
					Hiber.session().save(new HhDatum(channel, datumRaw));
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
								: !datumRaw.getStatus().equals(
										datum.getStatus()))) {
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
						channel.addChannelSnag(ChannelSnag.SNAG_NEGATIVE,
								datumRaw.getEndDate(), datumRaw.getEndDate(),
								false);
					} else if (altered && originalDatum.getValue() < 0) {
						channel.resolveSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw
								.getEndDate());
					}
					if (!HhDatumRaw.ACTUAL.equals(datumRaw.getStatus())) {
						if (notActualFrom == null) {
							notActualFrom = datumRaw.getEndDate();
						}
						notActualTo = datumRaw.getEndDate();
					} else if (altered
							&& !originalDatum.getStatus().equals(
									HhDatumRaw.ACTUAL)) {
						channel.resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL,
								datumRaw.getEndDate());
					}
				}
				if (siteCheckTo != null && siteCheckTo.equals(prevEndDate)) {
					// Debug.print("About to do site check: "
					// + (System.currentTimeMillis() - now));
					channel.siteCheck(siteCheckFrom, siteCheckTo);
					siteCheckFrom = null;
					siteCheckTo = null;
					// Debug.print("Finished site check: "
					// + (System.currentTimeMillis() - now));
				}
				if (notActualTo != null && notActualTo.equals(prevEndDate)) {
					// Debug.print("Started not actual: "
					// + (System.currentTimeMillis() - now));
					channel.addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL,
							notActualFrom, notActualTo, false);
					// notActualSnag(notActualFrom, notActualTo,
					// supplyGenerations);
					// Debug.print("Finished not actual: "
					// + (System.currentTimeMillis() - now));
					notActualFrom = null;
					notActualTo = null;
				}
				if (resolveMissingTo != null
						&& resolveMissingTo.equals(prevEndDate)) {
					// Debug.print("Starting resolvedMissing: "
					// + (System.currentTimeMillis() - now));
					channel.resolveSnag(ChannelSnag.SNAG_MISSING,
							resolveMissingFrom, resolveMissingTo);
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
				channel.siteCheck(siteCheckFrom, siteCheckTo);
				// Debug.print("About to finish site thing: "
				// + (System.currentTimeMillis() - now));
			}
			if (notActualTo != null && notActualTo.equals(prevEndDate)) {
				// Debug.print("About to start not actual: "
				// + (System.currentTimeMillis() - now));
				channel.addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL,
						notActualFrom, notActualTo, false);
				// channel.notActualSnag(notActualFrom, notActualTo,
				// supplyGenerations);
				// Debug.print("About to finsih not actual: "
				// + (System.currentTimeMillis() - now));
			}
			if (resolveMissingTo != null
					&& resolveMissingTo.equals(prevEndDate)) {
				// Debug.print("About to start resolvem: "
				// + (System.currentTimeMillis() - now));
				channel.resolveSnag(ChannelSnag.SNAG_MISSING,
						resolveMissingFrom, resolveMissingTo);
				// Debug.print("About to finish resolvem: "
				// + (System.currentTimeMillis() - now));
			}
			// Debug.print("Finished method: " + (System.currentTimeMillis() -
			// now));
		}
	}

*/
	/*
	@SuppressWarnings("unchecked")
	public void addHhData(HhdcContract contract, List<HhDatumRaw> dataRaw)
			throws HttpException {
		// long now = System.currentTimeMillis();
		// Debug.print("Starting method: " + (System.currentTimeMillis() -
		// now));

		HhEndDate from = dataRaw.get(0).getEndDate();
		HhEndDate to = dataRaw.get(dataRaw.size() - 1).getEndDate();
		/*
		boolean isImport = dataRaw.get(0).getIsImport();
		boolean isKwh = dataRaw.get(0).getIsKwh();
	
		if (getGeneration(from) == null) {
			throw new UserException("HH data has been ignored from "
					+ dataRaw.toString() + " to " + to + ".");
		}
		if (getGeneration(to) == null) {
			throw new UserException("HH data has been ignored from "
					+ dataRaw.toString() + " to " + to + ".");
		}
		List<SupplyGeneration> supplyGenerations = getGenerations(from, to);
		for (SupplyGeneration generation : supplyGenerations) {
			Channel channel = generation.getChannel(isImport, isKwh);
			HhdcContract actualHhdcContract = generation.getHhdcContract();
			if (channel == null) {
				throw new UserException("HH data has been ignored from "
						+ dataRaw.toString() + " to " + to + ".");
			}
			if (!contract.equals(actualHhdcContract)) {
				throw new UserException(
						"Somewhere in the block of hh data between ("
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
			List<HhDatum> data = (List<HhDatum>) Hiber
					.session()
					.createQuery(
							"from HhDatum datum where datum.channel = :channel and "
									+ "datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate order by datum.endDate.date")
					.setEntity("channel", channel).setTimestamp("startDate",
							generation.getStartDate().getDate()).setTimestamp(
							"finishDate", generation.getFinishDate().getDate())
					.list();
			if (data.isEmpty()) {
				checkForMissingFromLatest(from.getPrevious());
			}
			
			
			
			
	*/		
			
	/*		
			boolean isImport = dataRaw.get(0).getIsImport();
			boolean isKwh = dataRaw.get(0).getIsKwh();
			SupplyGeneration supplyGeneration = getGeneration(from);
			Channel channel = supplyGeneration.getChannel(isImport, isKwh);
			if (supplyGeneration == null) {
				throw new UserException("HH data has been ignored from "
						+ dataRaw.toString() + " to " + to + ".");
			}
			if (getGeneration(to) == null) {
				throw new UserException("HH data has been ignored from "
						+ dataRaw.toString() + " to " + to + ".");
			}			
			HhEndDate siteCheckFrom = null;
			HhEndDate siteCheckTo = null;
			HhEndDate notActualFrom = null;
			HhEndDate notActualTo = null;
			HhEndDate resolveMissingFrom = null;
			HhEndDate resolveMissingTo = null;
			HhEndDate prevEndDate = null;
			Channel prevChannel = null;
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
					Hiber.session().save(new HhDatum(channel, datumRaw));
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
								: !datumRaw.getStatus().equals(
										datum.getStatus()))) {
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
						channel.addChannelSnag(ChannelSnag.SNAG_NEGATIVE,
								datumRaw.getEndDate(), datumRaw.getEndDate(),
								false);
					} else if (altered && originalDatum.getValue() < 0) {
						channel.resolveSnag(ChannelSnag.SNAG_NEGATIVE, datumRaw
								.getEndDate());
					}
					if (!HhDatumRaw.ACTUAL.equals(datumRaw.getStatus())) {
						if (notActualFrom == null) {
							notActualFrom = datumRaw.getEndDate();
						}
						notActualTo = datumRaw.getEndDate();
					} else if (altered
							&& !originalDatum.getStatus().equals(
									HhDatumRaw.ACTUAL)) {
						channel.resolveSnag(ChannelSnag.SNAG_NOT_ACTUAL,
								datumRaw.getEndDate());
					}
				}
				if (siteCheckTo != null && siteCheckTo.equals(prevEndDate) || channel.equals(prevChannel)) {
					// Debug.print("About to do site check: "
					// + (System.currentTimeMillis() - now));
					channel.siteCheck(siteCheckFrom, siteCheckTo);
					siteCheckFrom = null;
					siteCheckTo = null;
					// Debug.print("Finished site check: "
					// + (System.currentTimeMillis() - now));
				}
				if (notActualTo != null && notActualTo.equals(prevEndDate)) {
					// Debug.print("Started not actual: "
					// + (System.currentTimeMillis() - now));
					channel.addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL,
							notActualFrom, notActualTo, false);
					// notActualSnag(notActualFrom, notActualTo,
					// supplyGenerations);
					// Debug.print("Finished not actual: "
					// + (System.currentTimeMillis() - now));
					notActualFrom = null;
					notActualTo = null;
				}
				if (resolveMissingTo != null
						&& resolveMissingTo.equals(prevEndDate)) {
					// Debug.print("Starting resolvedMissing: "
					// + (System.currentTimeMillis() - now));
					channel.resolveSnag(ChannelSnag.SNAG_MISSING,
							resolveMissingFrom, resolveMissingTo);
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
				channel.siteCheck(siteCheckFrom, siteCheckTo);
				// Debug.print("About to finish site thing: "
				// + (System.currentTimeMillis() - now));
			}
			if (notActualTo != null && notActualTo.equals(prevEndDate)) {
				// Debug.print("About to start not actual: "
				// + (System.currentTimeMillis() - now));
				channel.addChannelSnag(ChannelSnag.SNAG_NOT_ACTUAL,
						notActualFrom, notActualTo, false);
				// channel.notActualSnag(notActualFrom, notActualTo,
				// supplyGenerations);
				// Debug.print("About to finsih not actual: "
				// + (System.currentTimeMillis() - now));
			}
			if (resolveMissingTo != null
					&& resolveMissingTo.equals(prevEndDate)) {
				// Debug.print("About to start resolvem: "
				// + (System.currentTimeMillis() - now));
				channel.resolveSnag(ChannelSnag.SNAG_MISSING,
						resolveMissingFrom, resolveMissingTo);
				// Debug.print("About to finish resolvem: "
				// + (System.currentTimeMillis() - now));
			}
			// Debug.print("Finished method: " + (System.currentTimeMillis() -
			// now));
		}
	}
*/

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Supply) {
			isEqual = getId().equals(((Supply) obj).getId());
		}
		return isEqual;
	}

	public RegisterRead insertRegisterRead(RegisterReadRaw rawRegisterRead,
			Invoice invoice, Service service) throws HttpException {
		SupplyGeneration supplyGeneration = this.getGeneration(rawRegisterRead
				.getPresentDate());
		return supplyGeneration.insertRegisterRead(rawRegisterRead, invoice);
	}

	public Meter findMeter(String meterSerialNumber) {
		return (Meter) Hiber
				.session()
				.createQuery(
						"from Meter meter where meter.supply = :supply and meter.serialNumber = :meterSerialNumber")
				.setEntity("supply", this).setString("meterSerialNumber",
						meterSerialNumber).uniqueResult();
	}

	Meter getMeter(String meterSerialNumber) throws HttpException,
			InternalException {
		Meter meter = findMeter(meterSerialNumber);
		if (meter == null) {
			throw new UserException("There isn't a meter with serial number "
					+ meterSerialNumber + " attached to supply " + getId()
					+ ".");
		}
		return meter;
	}

	@SuppressWarnings("unchecked")
	public void delete(Supply supply) throws HttpException {
		long numInvoiceMpans = (Long) Hiber
				.session()
				.createQuery(
						"select count(*) from InvoiceMpan invoiceMpan where invoiceMpan.mpan.supplyGeneration.supply = :supply")
				.setEntity("supply", this).uniqueResult();
		if (numInvoiceMpans > 0) {
			throw new UserException(
					"One can't delete a supply if there are still invoices attached to its MPANs.");
		}
		/*
		 * long reads = (Long) Hiber .session() .createQuery( "select count(*)
		 * from RegisterRead read where read.mpan.supplyGeneration.supply =
		 * :supply") .setEntity("supply", this).uniqueResult(); if (reads > 0) {
		 * throw UserException .newInvalidParameter("One can't delete a supply
		 * if there are still register reads attached to its MPANs."); }
		 */
		for (SupplyGeneration generation : getGenerations()) {
			generation.delete();
		}
		// delete all the snags
		for (ChannelSnag snag : (List<ChannelSnag>) Hiber
				.session()
				.createQuery(
						"from ChannelSnag snag where snag.channel.supply = :supply")
				.setEntity("supply", this).list()) {
			Hiber.session().delete(snag);
			Hiber.flush();
		}
		mpanCores.clear();
		// Hiber.session().createQuery("delete from ChannelSnag snag where
		// snag.channel.supply = :supply").setEntity("supply",
		// supply).executeUpdate();
		Hiber.session().delete(this);
		Hiber.flush();
	}

	public void siteCheck(HhEndDate from, HhEndDate to) throws HttpException {
		// long now = System.currentTimeMillis();
		for (SupplyGeneration generation : generations) {
			generation.getChannel(true, true).siteCheck(from, to);
			generation.getChannel(false, true).siteCheck(from, to);
		}
	}

	@SuppressWarnings("unchecked")
	public List<HhDatum> getHhData(boolean isImport, boolean isKwh,
			HhEndDate from, HhEndDate to) {
		return (List<HhDatum>) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.endDate.date >= :from and datum.endDate.date <= :to order by datum.endDate.date")
				.setEntity("supply", this).setBoolean("isImport", isImport)
				.setBoolean("isKwh", isKwh)
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate()).list();
	}
}