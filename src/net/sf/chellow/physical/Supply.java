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

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.MopContract;
import net.sf.chellow.billing.SupplierContract;
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
			HhStartDate startDate = HhStartDate.roundUp(new MonadDate(
					startDateStr).getDate());
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values, 6);
			HhStartDate finishDate = finishDateStr.trim().length() > 0 ? HhStartDate
					.roundUp(new MonadDate(finishDateStr).getDate())
					: null;
			String mopContractName = GeneralImport.addField(csvElement,
					"MOP Contract", values, 7);
			MopContract mopContract = mopContractName.length() == 0 ? null
					: MopContract.getMopContract(mopContractName);
			String mopAccount = GeneralImport.addField(csvElement,
					"MOP Account", values, 8);
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 9);
			HhdcContract hhdcContract = hhdcContractName.length() == 0 ? null
					: HhdcContract.getHhdcContract(hhdcContractName);
			String hhdcAccount = GeneralImport.addField(csvElement,
					"HHDC Account", values, 10);
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh", values, 11);
			boolean hasImportKwh = Boolean.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh", values, 12);
			boolean hasImportKvarh = Boolean.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh", values, 13);
			boolean hasExportKwh = Boolean.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh", values, 14);
			boolean hasExportKvarh = Boolean.parseBoolean(hasExportKvarhStr);
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 15);
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values, 16);
			Integer importAgreedSupplyCapacity = null;
			SupplierContract importSupplierContract = null;
			Ssc importSsc = null;
			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values, 17);
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values, 18);
			String importSupplierContractName = GeneralImport.addField(
					csvElement, "Import supplier contract name", values, 19);
			String importSupplierAccount = GeneralImport.addField(csvElement,
					"Import supplier account reference", values, 20);
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
			}
			SupplierContract exportSupplierContract = null;
			Integer exportAgreedSupplyCapacity = null;
			Ssc exportSsc = null;
			String exportMpanStr = null;
			String exportSupplierAccount = null;
			if (values.length > 21) {
				exportMpanStr = GeneralImport.addField(csvElement,
						"Export MPAN", values, 21);
				if (exportMpanStr != null && exportMpanStr.trim().length() != 0) {
					String exportSscCode = GeneralImport.addField(csvElement,
							"Export SSC", values, 22);
					exportSsc = exportSscCode.trim().length() == 0 ? null : Ssc
							.getSsc(exportSscCode);
					String exportAgreedSupplyCapacityStr = GeneralImport
							.addField(csvElement,
									"Export Agreed Supply Capacity", values, 23);
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
							values, 24);
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractName);
					exportSupplierAccount = GeneralImport.addField(csvElement,
							"Export supplier account", values, 25);
				}
			}
			Supply supply = site.insertSupply(source, generatorType,
					supplyName, startDate, finishDate, gspGroup, mopContract,
					mopAccount, hhdcContract, hhdcAccount, meterSerialNumber,
					importMpanStr, importSsc, importSupplierContract,
					importSupplierAccount, importAgreedSupplyCapacity,
					exportMpanStr, exportSsc, exportSupplierContract,
					exportSupplierAccount, exportAgreedSupplyCapacity);
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

	public Supply() {
	}

	Supply(String name, Source source, GeneratorType generatorType,
			GspGroup gspGroup) throws HttpException {
		setGenerations(new HashSet<SupplyGeneration>());
		update(name, source, generatorType, gspGroup);
		setMpanCores(new HashSet<MpanCore>());
	}

	public void update(String name, Source source, GeneratorType generatorType,
			GspGroup gspGroup) throws HttpException {
		if (name == null) {
			throw new InternalException("The supply name " + "cannot be null.");
		}
		name = name.trim();
		if (name.length() == 0) {
			throw new UserException("The supply name can't be blank.");
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

	public SupplyGeneration getGenerationFinishing(HhStartDate finishDate) {
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
	public List<SupplyGeneration> getGenerations(HhStartDate from,
			HhStartDate to) {
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

	public SupplyGeneration insertGeneration(HhStartDate startDate)
			throws HttpException {
		SupplyGeneration existingGeneration = getGeneration(startDate);
		if (existingGeneration == null) {
			throw new UserException(
					"You can't add a generation before the first generation, or after the last.");
		}
		HhdcContract existingHhdcContract = existingGeneration
				.getHhdcContract();
		String existingHhdcAccount = existingGeneration.getHhdcAccount();
		MopContract existingMopContract = existingGeneration.getMopContract();
		String existingMopAccount = existingGeneration.getMopAccount();

		String meterSerialNumber = existingGeneration.getMeterSerialNumber();
		Mpan existingImportMpan = existingGeneration.getImportMpan();
		Mpan existingExportMpan = existingGeneration.getExportMpan();
		Map<Site, Boolean> existingSiteMap = new HashMap<Site, Boolean>();
		for (SiteSupplyGeneration siteSupplyGeneration : existingGeneration
				.getSiteSupplyGenerations()) {
			existingSiteMap.put(siteSupplyGeneration.getSite(),
					siteSupplyGeneration.getIsPhysical());
		}
		String existingImportMpanStr = null;
		String existingExportMpanStr = null;
		SupplierContract existingImportSupplierContract = null;
		String existingImportSupplierAccount = null;
		SupplierContract existingExportSupplierContract = null;
		String existingExportSupplierAccount = null;
		Ssc existingImportSsc = null;
		Ssc existingExportSsc = null;
		Integer existingImportSupplyCapacity = null;
		Integer existingExportSupplyCapacity = null;
		if (existingExportMpan != null) {
			existingExportSupplierContract = existingExportMpan
					.getSupplierContract();
			existingExportSupplierAccount = existingExportMpan
					.getSupplierAccount();
			existingExportMpanStr = existingExportMpan.toString();
			existingExportSsc = existingExportMpan.getSsc();
			existingExportSupplyCapacity = existingExportMpan
					.getAgreedSupplyCapacity();
		}
		if (existingImportMpan != null) {
			existingImportMpanStr = existingImportMpan.toString();
			existingImportSupplierAccount = existingImportMpan
					.getSupplierAccount();
			existingImportSupplierContract = existingImportMpan
					.getSupplierContract();
			existingImportSsc = existingImportMpan.getSsc();
			existingImportSupplyCapacity = existingImportMpan
					.getAgreedSupplyCapacity();
		}
		return insertGeneration(existingSiteMap, startDate,
				existingMopContract, existingMopAccount, existingHhdcContract,
				existingHhdcAccount, meterSerialNumber, existingImportMpanStr,
				existingImportSsc, existingImportSupplierContract,
				existingImportSupplierAccount, existingImportSupplyCapacity,
				existingExportMpanStr, existingExportSsc,
				existingExportSupplierContract, existingExportSupplierAccount,
				existingExportSupplyCapacity);
	}

	public void updateGeneration(SupplyGeneration generation,
			HhStartDate start, HhStartDate finish) throws HttpException {
		generation = (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply and generation.id = :id")
				.setEntity("supply", this).setLong("id", generation.getId())
				.uniqueResult();
		if (generation == null) {
			throw new UserException(
					"The generation doesn't belong to this supply.");
		}
		generation.update(start, finish);
		SupplyGeneration previousGeneration = (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply and generation.startDate.date < :startDate order by generation.startDate.date desc")
				.setEntity("supply", this).setTimestamp("startDate",
						generation.getStartDate().getDate()).setMaxResults(1)
				.uniqueResult();
		SupplyGeneration nextGeneration = (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply and generation.startDate.date > :startDate order by generation.startDate.date")
				.setEntity("supply", this).setTimestamp("startDate",
						generation.getStartDate().getDate()).setMaxResults(1)
				.uniqueResult();
		if (previousGeneration != null) {
			previousGeneration.update(previousGeneration.getStartDate(), start
					.getPrevious());
		}
		if (nextGeneration != null) {
			nextGeneration.update(finish.getNext(), nextGeneration
					.getFinishDate());
		}
	}

	public SupplyGeneration insertGeneration(Map<Site, Boolean> siteMap,
			HhStartDate startDate, MopContract mopContract, String mopAccount,
			HhdcContract hhdcContract, String hhdcAccount,
			String meterSerialNumber, String importMpanStr, Ssc importSsc,
			SupplierContract importSupplierContract,
			String importSupplierAccount, Integer importAgreedSupplyCapacity,
			String exportMpanStr, Ssc exportSsc,
			SupplierContract exportSupplierContract,
			String exportSupplierAccount, Integer exportAgreedSupplyCapacity)
			throws HttpException {
		SupplyGeneration supplyGeneration = null;
		SupplyGeneration existingGeneration = null;
		if (generations.isEmpty()) {
			supplyGeneration = new SupplyGeneration(this, startDate, null,
					mopContract, mopAccount, hhdcContract, hhdcAccount,
					meterSerialNumber);
			Hiber.flush();
			generations.add(supplyGeneration);
			Hiber.flush();
			supplyGeneration.update(supplyGeneration.getStartDate(),
					supplyGeneration.getFinishDate(), supplyGeneration
							.getMopContract(),
					supplyGeneration.getMopAccount(), supplyGeneration
							.getHhdcContract(), supplyGeneration
							.getHhdcAccount(), supplyGeneration
							.getMeterSerialNumber(), importMpanStr, importSsc,
					importSupplierContract, importSupplierAccount,
					importAgreedSupplyCapacity, exportMpanStr, exportSsc,
					exportSupplierContract, exportSupplierAccount,
					exportAgreedSupplyCapacity);
		} else {
			existingGeneration = getGeneration(startDate);
			if (existingGeneration == null) {
				throw new UserException(
						"You can't add a generation before the start of the supply.");
			}
			supplyGeneration = new SupplyGeneration(this, startDate,
					existingGeneration.getFinishDate(), mopContract,
					mopAccount, hhdcContract, hhdcAccount, meterSerialNumber);
			generations.add(supplyGeneration);
			Hiber.flush();
			for (Channel channel : existingGeneration.getChannels()) {
				supplyGeneration.insertChannel(channel.getIsImport(), channel
						.getIsKwh());
			}
			Hiber.flush();
			supplyGeneration.update(supplyGeneration.getStartDate(),
					supplyGeneration.getFinishDate(), supplyGeneration
							.getMopContract(),
					supplyGeneration.getMopAccount(), supplyGeneration
							.getHhdcContract(), supplyGeneration
							.getHhdcAccount(), supplyGeneration
							.getMeterSerialNumber(), importMpanStr, importSsc,
					importSupplierContract, importSupplierAccount,
					importAgreedSupplyCapacity, exportMpanStr, exportSsc,
					exportSupplierContract, exportSupplierAccount,
					exportAgreedSupplyCapacity);
			Hiber.flush();
			existingGeneration.update(existingGeneration.getStartDate(),
					startDate.getPrevious());
			Hiber.flush();
		}
		Hiber.flush();
		for (Map.Entry<Site, Boolean> entry : siteMap.entrySet()) {
			supplyGeneration.attachSite(entry.getKey(), entry.getValue());
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

	public SupplyGeneration getGeneration(HhStartDate date) {
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
						"select count(*) from Channel channel where channel.supplyGeneration = :generation")
				.setEntity("generation", generation).uniqueResult()) > 0) {
			throw new UserException(
					"One can't delete a supply generation if there are still channels attached to it.");
		}
		SupplyGeneration previousGeneration = getGenerationPrevious(generation);
		SupplyGeneration nextGeneration = getGenerationNext(generation);
		getGenerations().remove(generation);
		Hiber.session().delete(generation);
		if (previousGeneration == null) {
			nextGeneration.update(generation.getStartDate(), nextGeneration
					.getFinishDate());
		} else {
			previousGeneration.update(previousGeneration.getStartDate(),
					generation.getFinishDate());
		}
		Hiber.flush();
		// onSupplyGenerationChange(generation.getStartDate(), generation
		// .getFinishDate());
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
				delete();
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
			return getSupplyGenerationsInstance();
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

	public void delete() throws HttpException {
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(bill) from Bill bill where bill.supply = :supply")
				.setEntity("supply", this).uniqueResult() > 0) {
			throw new UserException(
					"One can't delete a supply if there are still bills attached to it.");
		}
		for (SupplyGeneration generation : getGenerations()) {
			generation.delete();
		}
		mpanCores.clear();
		Hiber.session().delete(this);
		Hiber.flush();
	}

	public void siteCheck(HhStartDate from, HhStartDate to)
			throws HttpException {
		// long now = System.currentTimeMillis();
		for (SupplyGeneration generation : generations) {
			generation.getChannel(true, true).siteCheck(from, to);
			generation.getChannel(false, true).siteCheck(from, to);
		}
	}

	public String toString() {
		return "Supply id " + getId();
	}
}
