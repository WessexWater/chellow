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
import net.sf.chellow.billing.DceService;
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.billing.Service;
import net.sf.chellow.billing.SupplierService;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.Criteria;
import org.hibernate.HibernateException;
import org.hibernate.Query;
import org.hibernate.criterion.Restrictions;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Supply extends PersistentEntity implements Urlable {
	/*
	 * static public Supply getSupply(MonadLong id) throws ProgrammerException,
	 * UserException { return getSupply(id.getLong()); }
	 */
	static public Supply getSupply(Long id) throws ProgrammerException,
			UserException {
		try {
			Supply supply = (Supply) Hiber.session().get(Supply.class, id);
			if (supply == null) {
				throw UserException.newOk("There is no supply with that id.");
			}
			return supply;
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	public static Supply getSupply(MpanCoreRaw core)
			throws ProgrammerException, UserException {
		Supply supply;
		try {
			supply = (Supply) Hiber
					.session()
					.createQuery(
							"select distinct mpan.supplyGeneration.supply from Mpan mpan where mpan.dso.code.string || mpan.uniquePart.string || mpan.checkDigit.character = :core")
					.setString("core", core.toStringNoSpaces()).uniqueResult();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
		if (supply == null) {
			throw UserException.newOk("The MPAN core " + core
					+ " is not set up in Chellow.");
		}
		return supply;
	}

	private SupplyName name;

	private Source source;

	private Set<SupplyGeneration> generations;

	private Set<Channel> channels;

	private Set<MpanCore> mpanCores;

	private Set<Meter> meters;

	public Supply() throws ProgrammerException {
		setTypeName("supply");
	}

	Supply(SupplyName name, Source source) throws ProgrammerException,
			UserException {
		this();
		setChannels(new HashSet<Channel>());
		setGenerations(new HashSet<SupplyGeneration>());
		update(name, source);
		setMpanCores(new HashSet<MpanCore>());
		setMeters(new HashSet<Meter>());
	}

	public Set<Channel> getChannels() {
		return channels;
	}

	void setChannels(Set<Channel> channels) {
		this.channels = channels;
	}

	public void update(SupplyName name, Source source)
			throws ProgrammerException {
		if (name == null) {
			throw new ProgrammerException("The supply name "
					+ "cannot be null.");
		}
		setName(name);
		setSource(source);
	}

	public SupplyName getName() {
		return name;
	}

	protected void setName(SupplyName name) throws ProgrammerException {
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

	public boolean hasMpanCoreRaw(MpanCoreRaw mpanCoreRaw)
			throws ProgrammerException, UserException {
		boolean hasMpanCoreRaw = false;
		for (MpanCore mpanCore : mpanCores) {
			if (mpanCore.getCore().equals(mpanCoreRaw)) {
				hasMpanCoreRaw = true;
				break;
			}
		}
		return hasMpanCoreRaw;
	}

	public MpanCore addMpanCore(MpanCoreRaw mpanCoreRaw) throws UserException,
			ProgrammerException {
		MpanCore mpanCore = new MpanCore(this, mpanCoreRaw);
		try {
			Hiber.session().save(mpanCore);
			mpanCores.add(mpanCore);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw UserException
					.newInvalidParameter("This MPAN core already exists.");
		}
		return mpanCore;
	}

	public Meter insertMeter(String meterSerialNumber) throws UserException,
			ProgrammerException {
		Meter meter = new Meter(this, meterSerialNumber);
		try {
			Hiber.session().save(meter);
			meters.add(meter);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw UserException
					.newInvalidParameter("This meter already exists.");
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

	public MpanCore getMpanCore(MpanCoreRaw core) throws ProgrammerException {
		MpanCore mpanCore = (MpanCore) Hiber
				.session()
				.createQuery(
						"from MpanCore mpanCore where mpanCore.supply = :supply and mpanCore.dso.code.string || mpanCore.uniquePart.string || mpanCore.checkDigit.character = :core")
				.setEntity("supply", this).setString("core",
						core.toStringNoSpaces()).uniqueResult();
		if (mpanCore == null) {
			throw new ProgrammerException("Mpan isn't attached to this supply.");
		}
		return mpanCore;
	}

	public SupplyGeneration addGeneration(HhEndDate finishDate)
			throws UserException, ProgrammerException, DesignerException {
		if (finishDate != null
				&& finishDate.getDate().before(
						getGenerationFirst().getStartDate().getDate())) {
			throw UserException
					.newOk("You can't add a generation before the first generation.");
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
					null, null, null, null, null, false, false, false, false,
					null, existingExportMpan.getMpanTop(), existingExportMpan
							.getMpanCore(), existingExportMpan.getDceService(),
					existingExportMpan.getSupplierAccount(), existingExportMpan
							.getSupplierService(), existingExportMpan
							.getHasImportKwh(), existingExportMpan
							.getHasImportKvarh(), existingExportMpan
							.getHasExportKwh(), existingExportMpan
							.getHasExportKvarh(), existingExportMpan
							.getAgreedSupplyCapacity(), finishDate);
		} else if (existingExportMpan == null) {
			newSupplyGeneration = addGeneration(existingSiteMap, existingMeter,
					existingImportMpan.getMpanTop(), existingImportMpan
							.getMpanCore(), existingImportMpan.getDceService(),
					existingImportMpan.getSupplierAccount(), existingImportMpan
							.getSupplierService(), existingImportMpan
							.getHasImportKwh(), existingImportMpan
							.getHasImportKvarh(), existingImportMpan
							.getHasExportKwh(), existingImportMpan
							.getHasExportKvarh(), existingImportMpan
							.getAgreedSupplyCapacity(), null, null, null, null,
					null, false, false, false, false, null, finishDate);
		} else {
			newSupplyGeneration = addGeneration(existingSiteMap, existingMeter,
					existingImportMpan.getMpanTop(), existingImportMpan
							.getMpanCore(), existingImportMpan.getDceService(),
					existingImportMpan.getSupplierAccount(), existingImportMpan
							.getSupplierService(), existingImportMpan
							.getHasImportKwh(), existingImportMpan
							.getHasImportKvarh(), existingImportMpan
							.getHasExportKwh(), existingImportMpan
							.getHasExportKvarh(), existingImportMpan
							.getAgreedSupplyCapacity(), existingExportMpan
							.getMpanTop(), existingExportMpan.getMpanCore(),
					existingExportMpan.getDceService(), existingExportMpan
							.getSupplierAccount(), existingExportMpan
							.getSupplierService(), existingExportMpan
							.getHasImportKwh(), existingExportMpan
							.getHasImportKvarh(), existingExportMpan
							.getHasExportKwh(), existingExportMpan
							.getHasExportKvarh(), existingExportMpan
							.getAgreedSupplyCapacity(), finishDate);
		}
		return newSupplyGeneration;
	}

	public SupplyGeneration addGeneration(Map<Site, Boolean> existingSiteMap,
			Meter meter, MpanRaw importMpanRaw, DceService importContractDce,
			Account importAccountSupplier,
			SupplierService importContractSupplier, boolean importHasImportKwh,
			boolean importHasImportKvarh, boolean importHasExportKwh,
			boolean importHasExportKvarh, Integer importAgreedSupplyCapacity,
			MpanRaw exportMpanRaw, DceService exportContractDce,
			Account exportAccountSupplier,
			SupplierService exportContractSupplier, boolean exportHasImportKwh,
			boolean exportHasImportKvarh, boolean exportHasExportKwh,
			boolean exportHasExportKvarh, Integer exportAgreedSupplyCapacity,
			HhEndDate finishDate) throws ProgrammerException, UserException,
			DesignerException {
		Organization organization = existingSiteMap.keySet().iterator().next()
				.getOrganization();
		MpanTop importMpanTop = importMpanRaw == null ? null : importMpanRaw
				.getMpanTop();
		MpanCore importMpanCore = importMpanRaw == null ? null : importMpanRaw
				.getMpanCore(organization);
		MpanTop exportMpanTop = exportMpanRaw == null ? null : exportMpanRaw
				.getMpanTop();
		MpanCore exportMpanCore = exportMpanRaw == null ? null : exportMpanRaw
				.getMpanCore(organization);
		return addGeneration(existingSiteMap, meter, importMpanTop,
				importMpanCore, importContractDce, importAccountSupplier,
				importContractSupplier, importHasImportKwh,
				importHasImportKvarh, importHasExportKwh, importHasExportKvarh,
				importAgreedSupplyCapacity, exportMpanTop, exportMpanCore,
				exportContractDce, exportAccountSupplier,
				exportContractSupplier, exportHasImportKwh,
				exportHasImportKvarh, exportHasExportKwh, exportHasExportKvarh,
				exportAgreedSupplyCapacity, finishDate);
	}

	public SupplyGeneration addGeneration(Map<Site, Boolean> siteMap,
			Meter meter, MpanTop importMpanTop, MpanCore importMpanCore,
			DceService importContractDce, Account importAccountSupplier,
			SupplierService importContractSupplier, boolean importHasImportKwh,
			boolean importHasImportKvarh, boolean importHasExportKwh,
			boolean importHasExportKvarh, Integer importAgreedSupplyCapacity,
			MpanTop exportMpanTop, MpanCore exportMpanCore,
			DceService exportContractDce, Account exportAccountSupplier,
			SupplierService exportContractSupplier, boolean exportHasImportKwh,
			boolean exportHasImportKvarh, boolean exportHasExportKwh,
			boolean exportHasExportKvarh, Integer exportAgreedSupplyCapacity,
			HhEndDate finishDate) throws ProgrammerException, UserException,
			DesignerException {
		if (getGenerationFinishing(finishDate) != null) {
			throw UserException
					.newOk("There's already a supply generation with this finish date.");
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
				throw UserException
						.newOk("You can't add a generation before the start of the supply.");
			}
			supplyGeneration = new SupplyGeneration(this, existingGeneration
					.getStartDate(), finishDate, meter);
			existingGeneration.setStartDate(HhEndDate.getNext(finishDate));
			generations.add(supplyGeneration);
		}
		Hiber.flush();
		if (importMpanCore == null && exportMpanCore == null) {
			throw UserException
					.newOk("A supply generation must have at least one MPAN.");
		}
		supplyGeneration.addOrUpdateMpans(importMpanTop, importMpanCore,
				importContractDce, importAccountSupplier,
				importContractSupplier, importHasImportKwh,
				importHasImportKvarh, importHasExportKwh, importHasExportKvarh,
				importAgreedSupplyCapacity, exportMpanTop, exportMpanCore,
				exportContractDce, exportAccountSupplier,
				exportContractSupplier, exportHasImportKwh,
				exportHasImportKvarh, exportHasExportKwh, exportHasExportKvarh,
				exportAgreedSupplyCapacity);
		for (Map.Entry<Site, Boolean> entry : siteMap.entrySet()) {
			supplyGeneration.attachSite(entry.getKey(), entry.getValue());
		}
		supplyGeneration.setMeter(meter);
		return supplyGeneration;
	}

	public void checkForMissingFromLatest() throws ProgrammerException,
			UserException {
		for (Channel channel : channels) {
			channel.checkForMissingFromLatest(null);
		}
	}

	/*
	 * public void checkForMissing() throws ProgrammerException, UserException {
	 * for (Channel channel : channels) { channel.checkForMissing(); } }
	 */

	public void checkForMissing(HhEndDate from, HhEndDate to)
			throws ProgrammerException, UserException {
		for (Channel channel : channels) {
			channel.checkForMissing(from, to);
		}
	}

	public Source getSource() {
		return source;
	}

	protected void setSource(Source source) {
		this.source = source;
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttributeNode((Attr) name.toXML(doc));
		for (Channel channel : channels) {
			element.appendChild(channel.toXML(doc));
		}
		return element;
	}

	public SupplyGeneration getGenerationFirst() {
		// return generations.iterator().next();
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply.id = :id order by generation.startDate.date")
				.setLong("id", getId()).setMaxResults(1).uniqueResult();
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
			throws ProgrammerException, UserException {
		if (getGenerations().size() == 1) {
			throw UserException
					.newInvalidParameter("You can't delete the last generation dude.");
		}
		SupplyGeneration previousGeneration = getGenerationPrevious(generation);
		SupplyGeneration nextGeneration = getGenerationNext(generation);
		getGenerations().remove(generation);
		generation.getMpans().clear();
		Hiber.session().delete(generation);
		if (previousGeneration == null) {
			nextGeneration.update(generation.getStartDate(), nextGeneration
					.getFinishDate(), nextGeneration.getMeter());
		} else {
			previousGeneration.update(previousGeneration.getStartDate(),
					generation.getFinishDate(), previousGeneration.getMeter());
		}
		checkAfterUpdate(true, generation.getStartDate(), generation
				.getFinishDate());
	}

	@SuppressWarnings("unchecked")
	public void checkAfterUpdate(boolean checkData, HhEndDate from, HhEndDate to)
			throws ProgrammerException, UserException {
		Hiber.flush();
		Date supplyStartDate = getGenerationFirst().getStartDate().getDate();
		Date supplyFinishDate = getGenerationLast().getFinishDate() == null ? null
				: getGenerationLast().getFinishDate().getDate();
		if (checkData) {
			// Check that there aren't any data without contracts.
			if (from.getDate().before(supplyStartDate)
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.supply  = :supply and datum.endDate.date < :date")
							.setEntity("supply", this).setTimestamp("date",
									supplyStartDate).uniqueResult()) > 0) {
				throw UserException
						.newInvalidParameter("There are half-hourly data before the start of the updated supply.");
			}
			if (supplyFinishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.supply  = :supply and datum.endDate.date > :date")
							.setEntity("supply", this).setTimestamp("date",
									supplyFinishDate).uniqueResult()) > 0) {
				throw UserException
						.newInvalidParameter("There are half-hourly data after the end of the updated supply.");
			}
			Query query = Hiber
					.session()
					.createQuery(
							"select count(*) from HhDatum datum where datum.channel  = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate");
			for (SupplyGeneration generation : getGenerations(from, to)) {
				for (Channel channel : getChannels()) {
					if (generation.getDceService(channel.getIsImport(), channel
							.getIsKwh()) == null) {
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
								throw UserException
										.newInvalidParameter("There are half-hourly data in "
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
								throw UserException
										.newInvalidParameter("There are half-hourly data without a contract, associated with the channel "
												+ channel.getId()
												+ " and supply generation '"
												+ generation.getId() + "' .");
							}
						}
					}
				}
			}
			if (from.getDate().before(supplyStartDate)) {
				for (SnagChannel snag : (List<SnagChannel>) Hiber
						.session()
						.createQuery(
								"from SnagChannel snag where snag.channel.supply  = :supply and snag.finishDate.date >= :startDate and snag.startDate.date <= :finishDate")
						.setEntity("supply", this).setTimestamp("startDate",
								from.getDate()).setTimestamp(
								"finishDate",
								new HhEndDate(supplyStartDate).getPrevious()
										.getDate()).list()) {
					snag.resolve(false);
				}
			}
			if (supplyFinishDate != null) {
				for (SnagChannel snag : (List<SnagChannel>) Hiber
						.session()
						.createQuery(
								"from SnagChannel snag where snag.channel.supply  = :supply and snag.finishDate.date >= :startDate")
						.setEntity("supply", this).setTimestamp("startDate",
								from.getDate()).list()) {
					snag.resolve(false);
				}
			}
			for (SupplyGeneration generation : getGenerations(from, to)) {
				for (Channel channel : getChannels()) {
					DceService contractDce = generation.getDceService(channel
							.getIsImport(), channel.getIsKwh());
					HhEndDate generationFinishDate = generation.getFinishDate();
					for (SnagChannel snag : (List<SnagChannel>) (generationFinishDate == null ? Hiber
							.session()
							.createQuery(
									"from SnagChannel snag where snag.channel  = :channel and snag.finishDate.date >= :startDate")
							.setEntity("channel", channel).setTimestamp(
									"startDate",
									generation.getStartDate().getDate()).list()
							: Hiber
									.session()
									.createQuery(
											"from SnagChannel snag where snag.channel  = :channel and snag.finishDate.date >= :startDate and snag.startDate.date <= :finishDate")
									.setEntity("channel", channel)
									.setTimestamp("startDate",
											generation.getStartDate().getDate())
									.setTimestamp(
											"finishDate",
											generation.getFinishDate()
													.getDate()).list())) {
						if (!snag.getService().equals(contractDce)) {
							snag.resolve(false);
						}
					}
				}
			}
			checkForMissing(from, to);
		}
		if (from.getDate().before(supplyStartDate)
				&& ((Long) Hiber
						.session()
						.createQuery(
								"select count(*) from RegisterRead read where read.mpan.supplyGeneration.supply  = :supply and read.presentDate.date < :date")
						.setEntity("supply", this).setTimestamp("date",
								supplyStartDate).uniqueResult()) > 0) {
			throw UserException
					.newInvalidParameter("There are register reads before the start of the updated supply.");
		}
		if (supplyFinishDate != null
				&& ((Long) Hiber
						.session()
						.createQuery(
								"select count(*) from RegisterRead read where read.mpan.supplyGeneration.supply  = :supply and read.presentDate.date > :date")
						.setEntity("supply", this).setTimestamp("date",
								supplyFinishDate).uniqueResult()) > 0) {
			throw UserException
					.newInvalidParameter("There are register reads after the end of the updated supply.");
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
					Mpan targetMpan = read.getMpan().getMpanTop()
							.getLineLossFactor().getIsImport() ? targetGeneration
							.getImportMpan()
							: targetGeneration.getExportMpan();
					if (targetMpan == null) {
						throw UserException
								.newInvalidParameter("There's no MPAN for the meter read to move to.");
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
			throws ProgrammerException, UserException {
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply.id = :id and generation.finishDate.date = :generationFinishDate")
				.setLong("id", getId()).setTimestamp("generationFinishDate",
						generation.getStartDate().getPrevious().getDate())
				.uniqueResult();
	}

	public SupplyGeneration getGenerationNext(SupplyGeneration generation)
			throws ProgrammerException, UserException {
		if (generation.getFinishDate() == null) {
			return null;
		}
		return (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply.id = :id and generation.startDate.date = :generationStartDate")
				.setLong("id", getId()).setTimestamp("generationStartDate",
						generation.getFinishDate().getNext().getDate())
				.uniqueResult();
	}

	public Channel getChannel(boolean isImport, boolean isKwh) {
		Channel channel = null;
		for (Channel candidateChannel : channels) {
			if (candidateChannel.getIsImport() == isImport
					&& candidateChannel.getIsKwh() == isKwh) {
				channel = candidateChannel;
				break;
			}
		}
		return channel;
	}

	private void addSourcesXML(Element element) throws ProgrammerException,
			UserException {
		for (Source source : Source.getSources()) {
			element.appendChild(source.toXML(element.getOwnerDocument()));
		}
	}

	private Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element supplyElement = (Element) getXML(new XmlTree("generations",
				new XmlTree("mpans", new XmlTree("mpanCore").put("mpanTop",
						new XmlTree("lineLossFactor", new XmlTree(
								"voltageLevel"))))).put("mpanCores"), doc);
		source.appendChild(supplyElement);
		supplyElement.appendChild(getOrganization().toXML(doc));
		addSourcesXML(source);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXML(doc));
		return doc;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		try {
			if (inv.hasParameter("delete")) {
				Document doc = document();
				Element source = doc.getDocumentElement();

				source.appendChild(toXML(doc));
				Organization organization = getOrganization();
				organization.deleteSupply(this);
				Hiber.commit();
				source
						.appendChild(new VFMessage(
								"Supply deleted successfully.").toXML(doc));
				inv.sendSeeOther(organization.getUri());
			} else {
				SupplyName name = inv.getValidatable(SupplyName.class, "name");
				Long sourceId = inv.getLong("source-id");
				if (!inv.isValid()) {
					throw UserException.newInvalidParameter(document());
				}
				update(name, Source.getSource(sourceId));
				Hiber.commit();
				inv.sendOk(document());
			}
		} catch (UserException e) {
			e.setDocument(document());
			throw e;
		}
	}

	public void httpGet(Invocation inv) throws ProgrammerException,
			DesignerException, DeployerException, UserException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
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

	public Channels getChannelsInstance() {
		return new Channels(this);
	}

	public void httpPostSupplyGeneration(Invocation inv)
			throws DesignerException, ProgrammerException, UserException,
			DeployerException {
		Boolean isOngoing = inv.getBoolean("isOngoing");
		HhEndDate finishDate = null;
		if (!isOngoing) {
			finishDate = HhEndDate.roundDown(inv.getDate("finishDate"));
		}
		addGeneration(finishDate);
		Hiber.commit();
		inv.sendOk(document());
	}

	public Channel getChannel(UriPathElement urlId) throws UserException,
			ProgrammerException {
		Channel channel = (Channel) Hiber
				.session()
				.createQuery(
						"from Channel channel where channel.supply = :supply and channel.id = :channelId")
				.setEntity("supply", this).setLong("channelId",
						Long.parseLong(urlId.getString())).uniqueResult();
		if (channel == null) {
			throw UserException.newNotFound();
		}
		return channel;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		Urlable urlable = null;
		if (SupplyGenerations.URI_ID.equals(uriId)) {
			urlable = new SupplyGenerations(this);
		}
		if (Channels.URI_ID.equals(uriId)) {
			urlable = new Channels(this);
		}
		return urlable;
	}

	public Organization getOrganization() {
		return getGenerations().iterator().next().getSiteSupplyGenerations()
				.iterator().next().getSite().getOrganization();
	}

	void insertChannel(boolean isImport, boolean isKwh) {
		Channel channel = new Channel(this, isImport, isKwh);
		Hiber.session().save(channel);
		Hiber.flush();
		channels.add(channel);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Supply) {
			isEqual = getId().equals(((Supply) obj).getId());
		}
		return isEqual;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public RegisterRead insertRegisterRead(RegisterReadRaw rawRegisterRead,
			Invoice invoice, Service service) throws UserException,
			ProgrammerException {
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

	Meter getMeter(String meterSerialNumber) throws UserException,
			ProgrammerException {
		Meter meter = findMeter(meterSerialNumber);
		if (meter == null) {
			throw UserException
					.newInvalidParameter("There isn't a meter with serial number "
							+ meterSerialNumber
							+ " attached to supply "
							+ getId() + ".");
		}
		return meter;
	}
}