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

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.AccountSnag;
import net.sf.chellow.billing.Bill;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.Debug;
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
import net.sf.chellow.physical.MpanCore.MpanCoreRaw;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.Criteria;
import org.hibernate.Query;
import org.hibernate.ScrollableResults;
import org.hibernate.criterion.Restrictions;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Supply extends PersistentEntity {
	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String siteCode = GeneralImport.addField(csvElement, "Site Code",
					values, 0);
			Site site = Site.getSite(siteCode);
			String sourceCode = GeneralImport.addField(csvElement,
					"Source Code", values, 1);
			Source source = Source.getSource(sourceCode);
			String generatorTypeCode = GeneralImport.addField(csvElement,
					"Generator Type", values, 2);
			GeneratorType generatorType = null;
			if (source.getCode().equals(Source.GENERATOR_CODE)
					|| source.getCode().equals(Source.GENERATOR_NETWORK_CODE)) {
				generatorType = GeneratorType
						.getGeneratorType(generatorTypeCode);
			}
			String supplyName = GeneralImport.addField(csvElement,
					"Supply Name", values, 3);
			String gspGroupCode = GeneralImport.addField(csvElement,
					"GSP Group", values, 4);
			GspGroup gspGroup = GspGroup.getGspGroup(gspGroupCode);
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 5);
			HhEndDate startDate = HhEndDate.roundUp(new MonadDate(startDateStr)
					.getDate());
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values, 6);
			HhEndDate finishDate = finishDateStr.trim().length() > 0 ? HhEndDate
					.roundUp(new MonadDate(finishDateStr).getDate())
					: null;
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has import kWh", values, 7);
			boolean hasImportKwh = Boolean.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has import kVArh", values, 8);
			boolean hasImportKvarh = Boolean.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has export kWh", values, 9);
			boolean hasExportKwh = Boolean.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has export kVArh", values, 10);
			boolean hasExportKvarh = Boolean.parseBoolean(hasExportKvarhStr);
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 11);
			HhdcContract hhdcContract = hhdcContractName.length() == 0 ? null
					: HhdcContract.getHhdcContract(hhdcContractName);
			String hhdcAccountReference = GeneralImport.addField(csvElement,
					"HHDC Account", values, 12);
			Account hhdcAccount = null;
			if (hhdcContract != null) {
				hhdcAccount = hhdcContract.getAccount(hhdcAccountReference);
			}
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 13);
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values, 14);
			Integer importAgreedSupplyCapacity = null;
			SupplierContract importSupplierContract = null;
			Account importSupplierAccount = null;
			Ssc importSsc = null;
			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values, 15);
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values, 16);
			String importSupplierContractName = GeneralImport.addField(
					csvElement, "Import supplier contract name", values, 17);
			String importSupplierAccountReference = GeneralImport
					.addField(csvElement, "Import supplier account reference",
							values, 18);
			if (importMpanStr != null && importMpanStr.length() != 0) {
				importSsc = importSscCode.trim().length() == 0 ? null : Ssc
						.getSsc(importSscCode);
				try {
					importAgreedSupplyCapacity = new Integer(
							importAgreedSupplyCapacityStr);
				} catch (NumberFormatException e) {
					throw new UserException(
							"The import supply capacity must be an integer."
									+ e.getMessage());
				}
				importSupplierContract = SupplierContract
						.getSupplierContract(importSupplierContractName);
				importSupplierAccount = importSupplierContract
						.getAccount(importSupplierAccountReference);
			}
			SupplierContract exportSupplierContract = null;
			Account exportAccountSupplier = null;
			Integer exportAgreedSupplyCapacity = null;
			Ssc exportSsc = null;
			String exportMpanStr = null;
			if (values.length > 19) {
				exportMpanStr = GeneralImport.addField(csvElement,
						"Export MPAN", values, 19);
				if (exportMpanStr != null && exportMpanStr.trim().length() != 0) {
					String exportSscCode = GeneralImport.addField(csvElement,
							"Export SSC", values, 20);
					exportSsc = exportSscCode.trim().length() == 0 ? null : Ssc
							.getSsc(exportSscCode);
					String exportAgreedSupplyCapacityStr = GeneralImport
							.addField(csvElement,
									"Export Agreed Supply Capacity", values, 21);
					try {
						exportAgreedSupplyCapacity = new Integer(
								exportAgreedSupplyCapacityStr);
					} catch (NumberFormatException e) {
						throw new UserException(
								"The export agreed supply capacity must be an integer."
										+ e.getMessage());
					}
					String exportSupplierContractName = GeneralImport.addField(
							csvElement, "Export supplier contract name",
							values, 22);
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractName);
					String exportSupplierAccountReference = GeneralImport
							.addField(csvElement,
									"Export supplier account reference",
									values, 23);
					exportAccountSupplier = exportSupplierContract
							.getAccount(exportSupplierAccountReference);
				}
			}
			Supply supply = site.insertSupply(source, generatorType,
					supplyName, startDate, finishDate, gspGroup, hhdcAccount,
					meterSerialNumber, importMpanStr, importSsc,
					importSupplierAccount, importAgreedSupplyCapacity,
					exportMpanStr, exportSsc, exportAccountSupplier,
					exportAgreedSupplyCapacity);
			Hiber.flush();
			SupplyGeneration generation = supply.getGenerationFirst();
			if (hasImportKwh) {
				generation.insertChannel(true, true);
			}
			if (hasImportKvarh) {
				generation.insertChannel(true, false);
			}
			if (hasExportKwh) {
				generation.insertChannel(false, true);
			}
			if (hasExportKvarh) {
				generation.insertChannel(false, false);
			}
		} else if (action.equals("update")) {
			if (values.length < 5) {
				throw new UserException(
						"There aren't enough fields in this row");
			}
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values, 0);
			String sourceCode = GeneralImport.addField(csvElement,
					"Source Code", values, 1);
			String generatorType = GeneralImport.addField(csvElement,
					"Generator Type", values, 2);
			String gspGroupCode = GeneralImport.addField(csvElement,
					"GSP Group", values, 3);
			String supplyName = GeneralImport.addField(csvElement,
					"Supply Name", values, 4);
			Supply supply = MpanCore.getMpanCore(mpanCoreStr).getSupply();
			supply.update(supplyName.equals(GeneralImport.NO_CHANGE) ? supply
					.getName() : supplyName, sourceCode
					.equals(GeneralImport.NO_CHANGE) ? supply.getSource()
					: Source.getSource(sourceCode), generatorType
					.equals(GeneralImport.NO_CHANGE) ? supply
					.getGeneratorType() : GeneratorType
					.getGeneratorType(generatorType), gspGroupCode
					.equals(GeneralImport.NO_CHANGE) ? supply.getGspGroup()
					: GspGroup.getGspGroup(gspGroupCode));
		}
	}

	static public Supply getSupply(Long id) throws HttpException {
		Supply supply = (Supply) Hiber.session().get(Supply.class, id);
		if (supply == null) {
			throw new UserException("There is no supply with that id.");
		}
		return supply;
	}

	public static Supply getSupply(MpanCoreRaw core) throws HttpException {
		Supply supply = (Supply) Hiber
				.session()
				.createQuery(
						"select distinct mpan.supplyGeneration.supply from Mpan mpan where mpan.dso.code.string || mpan.uniquePart.string || mpan.checkDigit.character = :core")
				.setString("core", core.toStringNoSpaces()).uniqueResult();
		if (supply == null) {
			throw new UserException("The MPAN core " + core
					+ " is not set up in Chellow.");
		}
		return supply;
	}

	private String name;

	private Source source;

	private GeneratorType generatorType;

	private GspGroup gspGroup;

	private Set<SupplyGeneration> generations;

	private Set<MpanCore> mpanCores;

	private Set<Meter> meters;

	public Supply() {
	}

	Supply(String name, Source source, GeneratorType generatorType,
			GspGroup gspGroup) throws HttpException {
		setGenerations(new HashSet<SupplyGeneration>());
		update(name, source, generatorType, gspGroup);
		setMpanCores(new HashSet<MpanCore>());
		setMeters(new HashSet<Meter>());
	}

	public void update(String name, Source source, GeneratorType generatorType,
			GspGroup gspGroup) throws HttpException {
		if (name == null) {
			throw new InternalException("The supply name " + "cannot be null.");
		}
		setName(name);
		setSource(source);
		if ((source.getCode().equals(Source.GENERATOR_CODE) || source.getCode()
				.equals(Source.GENERATOR_NETWORK_CODE))
				&& generatorType == null) {
			throw new UserException(
					"If the source is 'gen' or 'gen-net', there must be a generator type.");
		}
		setGeneratorType(generatorType);
		setGspGroup(gspGroup);
	}

	public String getName() {
		return name;
	}

	protected void setName(String name) {
		this.name = name;
	}

	public GeneratorType getGeneratorType() {
		return generatorType;
	}

	protected void setGeneratorType(GeneratorType generatorType) {
		this.generatorType = generatorType;
	}

	public GspGroup getGspGroup() {
		return gspGroup;
	}

	void setGspGroup(GspGroup gspGroup) {
		this.gspGroup = gspGroup;
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

	public MpanCore addMpanCore(String mpanCore) throws HttpException {
		MpanCore core = new MpanCore(this, mpanCore);
		try {
			Hiber.session().save(core);
			mpanCores.add(core);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException("This MPAN core already exists.");
		}
		return core;
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

	public SupplyGeneration insertGeneration(HhEndDate startDate)
			throws HttpException {
		SupplyGeneration existingGeneration = getGeneration(startDate);
		if (existingGeneration == null) {
			throw new UserException(
					"You can't add a generation before the first generation, or after the last.");
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
			newSupplyGeneration = insertGeneration(existingSiteMap, startDate,
					existingGeneration.getHhdcAccount(), existingMeter
							.getSerialNumber(), null, null, null, null,
					existingExportMpan.toString(), existingExportMpan.getSsc(),
					existingExportMpan.getSupplierAccount(), existingExportMpan
							.getAgreedSupplyCapacity());
		} else if (existingExportMpan == null) {
			newSupplyGeneration = insertGeneration(existingSiteMap, startDate,
					existingGeneration.getHhdcAccount(),
					existingMeter == null ? "" : existingMeter
							.getSerialNumber(), existingImportMpan.toString(),
					existingImportMpan.getSsc(), existingImportMpan
							.getSupplierAccount(), existingImportMpan
							.getAgreedSupplyCapacity(), null, null, null, null);
		} else {
			newSupplyGeneration = insertGeneration(existingSiteMap, startDate,
					existingGeneration.getHhdcAccount(),
					existingMeter == null ? "" : existingMeter
							.getSerialNumber(), existingImportMpan.toString(),
					existingImportMpan.getSsc(), existingImportMpan
							.getSupplierAccount(), existingImportMpan
							.getAgreedSupplyCapacity(), existingExportMpan
							.toString(), existingExportMpan.getSsc(),
					existingExportMpan.getSupplierAccount(), existingExportMpan
							.getAgreedSupplyCapacity());
		}
		return newSupplyGeneration;
	}

	public SupplyGeneration insertGeneration(Map<Site, Boolean> siteMap,
			HhEndDate startDate, Account hhdcAccount, String meterSerialNumber,
			String importMpanStr, Ssc importSsc, Account importSupplierAccount,
			Integer importAgreedSupplyCapacity, String exportMpanStr,
			Ssc exportSsc, Account exportSupplierAccount,
			Integer exportAgreedSupplyCapacity) throws HttpException {
		Debug.print("inserting new genertaion");
		Meter meter = null;
		if (meterSerialNumber.trim().length() != 0) {
			meter = findMeter(meterSerialNumber);
			if (meter == null) {
				meter = insertMeter(meterSerialNumber);
			}
		}
		SupplyGeneration supplyGeneration = null;
		SupplyGeneration existingGeneration = null;
		if (generations.isEmpty()) {
			Debug.print("Empty.");
			supplyGeneration = new SupplyGeneration(this, startDate, null,
					hhdcAccount, meter);
			generations.add(supplyGeneration);
		} else {
			Debug.print("Not empty.");
			existingGeneration = getGeneration(startDate);
			if (existingGeneration == null) {
				throw new UserException(
						"You can't add a generation before the start of the supply.");
			}
			supplyGeneration = new SupplyGeneration(this, startDate,
					existingGeneration.getFinishDate(), hhdcAccount, meter);
			String existingImportMpanStr = null;
			Ssc existingImportSsc = null;
			Account existingImportSupplierAccount = null;
			Integer existingImportAgreedSupplyCapacity = null;
			String existingExportMpanStr = null;
			Ssc existingExportSsc = null;
			Account existingExportSupplierAccount = null;
			Integer existingExportAgreedSupplyCapacity = null;
			if (existingGeneration.getImportMpan() != null) {
				Mpan eMpan = existingGeneration.getImportMpan();
				existingImportMpanStr = eMpan.toString();
				existingImportSsc = eMpan.getSsc();
				existingImportSupplierAccount = eMpan.getSupplierAccount();
				existingImportAgreedSupplyCapacity = eMpan
						.getAgreedSupplyCapacity();
			}
			if (existingGeneration.getExportMpan() != null) {
				Mpan eMpan = existingGeneration.getExportMpan();
				existingExportMpanStr = eMpan.toString();
				existingExportSsc = eMpan.getSsc();
				existingExportSupplierAccount = eMpan.getSupplierAccount();
				existingExportAgreedSupplyCapacity = eMpan
						.getAgreedSupplyCapacity();
			}
			existingGeneration.internalUpdate(
					existingGeneration.getStartDate(), startDate.getPrevious(),
					existingGeneration.getHhdcAccount(), existingGeneration
							.getMeter(), existingImportMpanStr,
					existingImportSsc, existingImportSupplierAccount,
					existingImportAgreedSupplyCapacity, existingExportMpanStr,
					existingExportSsc, existingExportSupplierAccount,
					existingExportAgreedSupplyCapacity);
			generations.add(supplyGeneration);
		}
		Hiber.flush();
		supplyGeneration.internalUpdate(supplyGeneration.getStartDate(),
				supplyGeneration.getFinishDate(), supplyGeneration
						.getHhdcAccount(), supplyGeneration.getMeter(),
				importMpanStr, importSsc, importSupplierAccount,
				importAgreedSupplyCapacity, exportMpanStr, exportSsc,
				exportSupplierAccount, exportAgreedSupplyCapacity);
		for (Map.Entry<Site, Boolean> entry : siteMap.entrySet()) {
			supplyGeneration.attachSite(entry.getKey(), entry.getValue());
		}
		Debug.print("Existing generation is " + existingGeneration);
		supplyGeneration.setMeter(meter);
		if (existingGeneration != null) {
			Debug.print("There is an existing generation.");
			for (Channel existingChannel : existingGeneration.getChannels()) {
				supplyGeneration.insertChannel(existingChannel.getIsImport(),
						existingChannel.getIsKwh());
				Debug.print("Inserting channel."
						+ existingChannel.getIsImport() + " "
						+ existingChannel.getIsKwh());
			}
			Hiber.flush();
			onSupplyGenerationChange(startDate, supplyGeneration
					.getFinishDate());
		}
		Hiber.flush();
		return supplyGeneration;
	}

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
		if (((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from HhDatum datum where datum.channel.supplyGeneration = :generation")
				.setEntity("generation", generation).uniqueResult()) > 0) {
			throw new UserException(
					"One can't delete a supply generation if there are still data attached to it.");
		}
		SupplyGeneration previousGeneration = getGenerationPrevious(generation);
		SupplyGeneration nextGeneration = getGenerationNext(generation);
		getGenerations().remove(generation);
		generation.deleteMpans();
		Hiber.session().delete(generation);
		if (previousGeneration == null) {
			nextGeneration.update(generation.getStartDate(), nextGeneration
					.getFinishDate(), nextGeneration.getHhdcAccount(),
					nextGeneration.getMeter());
		} else {
			previousGeneration.update(previousGeneration.getStartDate(),
					generation.getFinishDate(), previousGeneration
							.getHhdcAccount(), previousGeneration.getMeter());
		}
		onSupplyGenerationChange(generation.getStartDate(), generation
				.getFinishDate());
	}

	@SuppressWarnings("unchecked")
	public void onSupplyGenerationChange(HhEndDate from, HhEndDate to)
			throws HttpException {
		Hiber.flush();
		Date supplyStartDate = getGenerationFirst().getStartDate().getDate();
		Date supplyFinishDate = getGenerationLast().getFinishDate() == null ? null
				: getGenerationLast().getFinishDate().getDate();
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
			for (Boolean isImport : new Boolean[] { true, false }) {
				for (Boolean isKwh : new Boolean[] { true, false }) {
					Channel targetChannel = generation.getChannel(isImport,
							isKwh);
					Query query = Hiber
							.session()
							.createQuery(
									"from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.endDate.date >= :from"
											+ (generation.getFinishDate() == null ? ""
													: " and datum.endDate.date <= :to")
											+ (targetChannel == null ? ""
													: " and datum.channel != :targetChannel"))
							.setEntity("supply", this).setBoolean("isImport",
									isImport).setBoolean("isKwh", isKwh)
							.setTimestamp("from",
									generation.getStartDate().getDate());
					if (generation.getFinishDate() != null) {
						query.setTimestamp("to", generation.getFinishDate()
								.getDate());
					}
					if (targetChannel != null) {
						query.setEntity("targetChannel", targetChannel);
					}
					ScrollableResults hhData = query.scroll();
					HhDatum datum = null;
					if (hhData.next()) {
						datum = (HhDatum) hhData.get(0);
						if (targetChannel == null) {
							throw new UserException(
									"There is no channel for the HH datum: "
											+ datum.toString()
											+ " is import? "
											+ isImport
											+ " is kWh? "
											+ isKwh
											+ " to move to in the generation starting "
											+ generation.getStartDate()
											+ ", finishing "
											+ generation.getFinishDate() + ".");
						}
					}
					hhData.beforeFirst();
					while (hhData.next()) {
						datum = (HhDatum) hhData.get(0);
						HhEndDate endDate = datum.getEndDate();
						datum.setChannel(targetChannel);
						if (datum.getValue().doubleValue() < 0) {
							targetChannel.addSnag(ChannelSnag.SNAG_NEGATIVE,
									endDate, endDate);
						}
						if (datum.getStatus() != HhDatum.ACTUAL) {
							targetChannel.addSnag(ChannelSnag.SNAG_ESTIMATED,
									endDate, endDate);
						}
						targetChannel.deleteSnag(ChannelSnag.SNAG_MISSING,
								endDate, endDate);
						Hiber.flush();
						Hiber.session().evict(datum);
					}
					hhData.close();
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
					Mpan targetMpan = read.getMpan().getLlfc().getIsImport() ? targetGeneration
							.getImportMpan()
							: targetGeneration.getExportMpan();
					if (targetMpan == null) {
						throw new UserException(
								"There's no MPAN for the meter read to move to.");
					}
					read.setMpan(targetMpan);
				}
			}

			// checkMpanRelationship
			if (generation.getHhdcAccount() != null) {
				HhdcContract hhdcContract = HhdcContract
						.getHhdcContract(generation.getHhdcAccount()
								.getContract().getId());
				HhEndDate hhdcContractStartDate = hhdcContract
						.getStartRateScript().getStartDate();
				if (hhdcContractStartDate.getDate().after(
						generation.getStartDate().getDate())) {
					throw new UserException(
							"The HHDC contract starts after the supply generation.");
				}
				HhEndDate hhdcContractFinishDate = hhdcContract
						.getFinishRateScript().getFinishDate();
				if (hhdcContractFinishDate != null
						&& (generation.getFinishDate() == null || hhdcContractFinishDate
								.getDate().before(
										generation.getStartDate().getDate()))) {
					throw new UserException("The HHDC contract "
							+ hhdcContract.getId()
							+ " finishes before the supply generation.");
				}
			}
			for (Mpan mpan : generation.getMpans()) {
				SupplierContract supplierContract = SupplierContract
						.getSupplierContract(mpan.getSupplierAccount()
								.getContract().getId());
				HhEndDate supplierContractStartDate = supplierContract
						.getStartRateScript().getStartDate();
				if (supplierContractStartDate.getDate().after(
						generation.getStartDate().getDate())) {
					throw new UserException(
							"The supplier contract starts after the supply generation.");
				}
				HhEndDate supplierContractFinishDate = supplierContract
						.getFinishRateScript().getFinishDate();
				if (generation.getFinishDate() == null
						&& supplierContractFinishDate != null
						|| supplierContractFinishDate != null
						&& generation.getFinishDate() != null
						&& supplierContractFinishDate.getDate().before(
								generation.getStartDate().getDate())) {
					throw new UserException(
							"The supplier contract finishes before the supply generation.");
				}
			}

			// update missing bill account snags
			Account hhdcAccount = generation.getHhdcAccount();
			if (hhdcAccount != null) {
				hhdcAccount.addSnag(AccountSnag.MISSING_BILL, generation
						.getStartDate(), generation.getFinishDate());
				for (Bill bill : (List<Bill>) Hiber.session().createQuery(
						"from Bill bill where bill.account = :account")
						.setEntity("account", hhdcAccount).list()) {
					hhdcAccount.deleteSnag(AccountSnag.MISSING_BILL, bill
							.getStartDate(), bill.getFinishDate());
				}
			}
			for (Mpan mpan : generation.getMpans()) {
				Account supplierAccount = mpan.getSupplierAccount();
				supplierAccount.addSnag(AccountSnag.MISSING_BILL, generation
						.getStartDate(), generation.getFinishDate());
				for (Bill bill : (List<Bill>) Hiber.session().createQuery(
						"from Bill bill where bill.account = :account")
						.setEntity("account", supplierAccount).list()) {
					supplierAccount.deleteSnag(AccountSnag.MISSING_BILL, bill
							.getStartDate(), bill.getFinishDate());
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

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element supplyElement = (Element) toXml(doc, new XmlTree("generations",
				new XmlTree("mpans", new XmlTree("core").put("llfc",
						new XmlTree("voltageLevel")))).put("source").put(
				"generatorType").put("gspGroup"));
		source.appendChild(supplyElement);
		for (Source supplySource : (List<Source>) Hiber.session().createQuery(
				"from Source source order by source.code").list()) {
			source.appendChild(supplySource.toXml(doc));
		}
		for (GeneratorType type : (List<GeneratorType>) Hiber.session()
				.createQuery("from GeneratorType type order by type.code")
				.list()) {
			source.appendChild(type.toXml(doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (GspGroup group : (List<GspGroup>) Hiber.session().createQuery(
				"from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}

		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		try {
			if (inv.hasParameter("delete")) {
				Document doc = document();
				Element source = doc.getDocumentElement();

				source.appendChild(toXml(doc));
				delete(this);
				Hiber.commit();
				source.appendChild(new MonadMessage(
						"Supply deleted successfully.").toXml(doc));
				inv.sendSeeOther(Chellow.SUPPLIES_INSTANCE.getUri());
			} else {
				String name = inv.getString("name");
				Long sourceId = inv.getLong("source-id");
				Long gspGroupId = inv.getLong("gsp-group-id");

				if (!inv.isValid()) {
					throw new UserException(document());
				}
				Source supplySource = Source.getSource(sourceId);
				GeneratorType type = null;
				if (supplySource.getCode().equals(Source.GENERATOR_CODE)
						|| supplySource.getCode().equals(
								Source.GENERATOR_NETWORK_CODE)) {
					Long generatorTypeId = inv.getLong("generator-type-id");
					if (!inv.isValid()) {
						throw new UserException(document());
					}
					type = GeneratorType.getGeneratorType(generatorTypeId);
				}
				GspGroup gspGroup = GspGroup.getGspGroup(gspGroupId);
				update(name, supplySource, type, gspGroup);
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
		return Chellow.SUPPLIES_INSTANCE.getUrlPath().resolve(getUriId())
				.append("/");
	}

	public SupplyGenerations getSupplyGenerationsInstance() {
		return new SupplyGenerations(this);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (SupplyGenerations.URI_ID.equals(uriId)) {
			return new SupplyGenerations(this);
		} else {
			throw new NotFoundException();
		}
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof Supply) {
			isEqual = getId().equals(((Supply) obj).getId());
		}
		return isEqual;
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
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(invoice) from Invoice invoice, Mpan mpan where invoice.bill.account = mpan.supplierAccount and mpan.supplyGeneration.supply = :supply")
				.setEntity("supply", this).uniqueResult() > 0) {
			throw new UserException(
					"One can't delete a supply if there are still invoices associated with supplier accounts referred to by its MPANs.");
		}
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(invoice) from Invoice invoice, Mpan mpan where invoice.bill.account = mpan.hhdcAccount and mpan.supplyGeneration.supply = :supply")
				.setEntity("supply", this).uniqueResult() > 0) {
			throw new UserException(
					"One can't delete a supply if there are still invoices associated with hhdc accounts referred to by its MPANs.");
		}
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(invoice) from Invoice invoice, Mpan mpan where invoice.bill.account = mpan.mopAccount and mpan.supplyGeneration.supply = :supply")
				.setEntity("supply", this).uniqueResult() > 0) {
			throw new UserException(
					"One can't delete a supply if there are still invoices associated with MOP accounts referred to by its MPANs.");
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
						"from ChannelSnag snag where snag.channel.supplyGeneration.supply = :supply")
				.setEntity("supply", this).list()) {
			Hiber.session().delete(snag);
			Hiber.flush();
		}
		mpanCores.clear();
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
}
