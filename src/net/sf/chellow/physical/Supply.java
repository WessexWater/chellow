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
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.hibernate.Criteria;
import org.hibernate.criterion.Restrictions;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.billing.Contract;
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
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

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
					.roundUp(new MonadDate(finishDateStr).getDate()) : null;
			String mopContractName = GeneralImport.addField(csvElement,
					"MOP Contract", values, 7);
			Contract mopContract = mopContractName.length() == 0 ? null
					: Contract.getMopContract(mopContractName);
			String mopAccount = GeneralImport.addField(csvElement,
					"MOP Account", values, 8);
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 9);
			Contract hhdcContract = hhdcContractName.length() == 0 ? null
					: Contract.getHhdcContract(hhdcContractName);
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

			String pcCode = GeneralImport.addField(csvElement, "Profile Class",
					values, 16);
			Pc pc = Pc.getPc(pcCode);

			String mtcCode = GeneralImport.addField(csvElement,
					"Meter Timeswitch Class", values, 17);

			String copCode = GeneralImport.addField(csvElement, "CoP", values,
					18);
			Cop cop = Cop.getCop(copCode);

			String sscCode = GeneralImport.addField(csvElement,
					"Standard Settlement Configuration", values, 19);
			Ssc ssc = null;
			if (sscCode.length() > 0) {
				ssc = Ssc.getSsc(sscCode);
			}

			String impMpanCore = GeneralImport.addField(csvElement,
					"Import MPAN Core", values, 20);
			if (impMpanCore.length() == 0) {
				impMpanCore = null;
			}
			Integer impSc = null;
			Contract impSupplierContract = null;
			String importLlfcCode = null;
			String importLlfcCodeRaw = GeneralImport.addField(csvElement,
					"Import LLFC", values, 21);
			String impScStr = GeneralImport.addField(csvElement,
					"Import Agreed Supply Capacity", values, 22);
			String impSupplierContractName = GeneralImport.addField(csvElement,
					"Import Supplier Contract", values, 23);
			String impSupplierAccount = null;
			String impSupplierAccountRaw = GeneralImport.addField(csvElement,
					"Import Supplier Account", values, 24);
			if (impMpanCore != null) {
				importLlfcCode = importLlfcCodeRaw;
				try {
					impSc = new Integer(impScStr);
				} catch (NumberFormatException e) {
					throw new UserException(
							"The import supply capacity must be an integer."
									+ e.getMessage());
				}
				impSupplierContract = Contract
						.getSupplierContract(impSupplierContractName);
				impSupplierAccount = impSupplierAccountRaw;

			}
			Contract exportSupplierContract = null;
			Integer exportAgreedSupplyCapacity = null;
			String exportLlfcCode = null;
			String exportMpanStr = null;
			String exportSupplierAccount = null;
			if (values.length > 25) {
				exportMpanStr = GeneralImport.addField(csvElement,
						"Export MPAN Core", values, 25);
				if (exportMpanStr != null && exportMpanStr.trim().length() != 0) {
					exportLlfcCode = GeneralImport.addField(csvElement,
							"Export LLFC", values, 26);
					String exportAgreedSupplyCapacityStr = GeneralImport
							.addField(csvElement,
									"Export Agreed Supply Capacity", values, 27);
					try {
						exportAgreedSupplyCapacity = new Integer(
								exportAgreedSupplyCapacityStr);
					} catch (NumberFormatException e) {
						throw new UserException(
								"The export agreed supply capacity must be an integer."
										+ e.getMessage());
					}
					String exportSupplierContractName = GeneralImport.addField(
							csvElement, "Export Supplier Contract", values, 28);
					exportSupplierContract = Contract
							.getSupplierContract(exportSupplierContractName);
					exportSupplierAccount = GeneralImport.addField(csvElement,
							"Export Supplier Account", values, 29);
				}
			}
			Supply supply = site.insertSupply(source, generatorType,
					supplyName, startDate, finishDate, gspGroup, "",
					mopContract, mopAccount, hhdcContract, hhdcAccount,
					meterSerialNumber, pc, mtcCode, cop, ssc, impMpanCore,
					importLlfcCode, impSupplierContract, impSupplierAccount,
					impSc, exportMpanStr, exportLlfcCode,
					exportSupplierContract, exportSupplierAccount,
					exportAgreedSupplyCapacity);
			Hiber.flush();
			Era era = supply.getEraFirst();
			if (hasImportKwh) {
				era.insertChannel(true, true);
			}
			if (hasImportKvarh) {
				era.insertChannel(true, false);
			}
			if (hasExportKwh) {
				era.insertChannel(false, true);
			}
			if (hasExportKvarh) {
				era.insertChannel(false, false);
			}
		} else if (action.equals("update")) {
			String mpanCore = GeneralImport.addField(csvElement, "MPAN Core",
					values, 0);
			String sourceCode = GeneralImport.addField(csvElement,
					"Source Code", values, 1);
			String generatorType = GeneralImport.addField(csvElement,
					"Generator Type", values, 2);
			String dnoCode = GeneralImport.addField(csvElement, "DNO Code",
					values, 3);
			String gspGroupCode = GeneralImport.addField(csvElement,
					"GSP Group", values, 4);
			String supplyName = GeneralImport.addField(csvElement,
					"Supply Name", values, 5);
			Supply supply = Supply.getSupply(mpanCore);
			supply.update(
					supplyName.equals(GeneralImport.NO_CHANGE) ? supply
							.getName() : supplyName,
					sourceCode.equals(GeneralImport.NO_CHANGE) ? supply
							.getSource() : Source.getSource(sourceCode),
					generatorType.equals(GeneralImport.NO_CHANGE) ? supply
							.getGeneratorType() : GeneratorType
							.getGeneratorType(generatorType),
					dnoCode.equals(GeneralImport.NO_CHANGE) ? supply
							.getDnoContract() : Contract
							.getDnoContract(dnoCode),
					gspGroupCode.equals(GeneralImport.NO_CHANGE) ? supply
							.getGspGroup() : GspGroup.getGspGroup(gspGroupCode));
		} else if (action.equals("delete")) {
			String mpanCore = GeneralImport.addField(csvElement, "MPAN Core",
					values, 0);
			Supply supply = Supply.getSupply(mpanCore);
			supply.delete();
		}
	}

	static public Supply getSupply(Long id) throws HttpException {
		Supply supply = (Supply) Hiber.session().get(Supply.class, id);
		if (supply == null) {
			throw new UserException("There is no supply with that id.");
		}
		return supply;
	}

	static public Supply getSupply(String mpanCore) {
		Era era = (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.impMpanCore = :mpanCore or era.expMpanCore = :mpanCore")
				.setString("mpanCore", mpanCore).setMaxResults(1)
				.uniqueResult();
		if (era == null) {
			throw new UserException("There isn't an era with the mpan core "
					+ mpanCore);
		}
		return era.getSupply();
	}

	private String name;

	private Source source;

	private GeneratorType generatorType;

	private Contract dnoContract;

	private GspGroup gspGroup;

	private String note;

	private Set<Era> eras;

	public Supply() {
	}

	Supply(String name, Source source, GeneratorType generatorType,
			Contract dnoContract, GspGroup gspGroup, String note)
			throws HttpException {
		setEras(new HashSet<Era>());
		update(name, source, generatorType, dnoContract, gspGroup);
		setNote(note);
	}

	public void update(String name, Source source, GeneratorType generatorType,
			Contract dnoContract, GspGroup gspGroup) throws HttpException {
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
		setDnoContract(dnoContract);
		setGspGroup(gspGroup);

		if (getSource().getCode().equals(Source.NETWORK_CODE)
				&& dnoContract.getParty().getDnoCode().equals("99")) {
			throw new UserException("A network supply can't have a 99 DNO.");
		}

	}

	public String getName() {
		return name;
	}

	protected void setName(String name) {
		this.name = name;
	}

	public Source getSource() {
		return source;
	}

	protected void setSource(Source source) {
		this.source = source;
	}

	public GeneratorType getGeneratorType() {
		return generatorType;
	}

	protected void setGeneratorType(GeneratorType generatorType) {
		this.generatorType = generatorType;
	}

	public Contract getDnoContract() {
		return dnoContract;
	}

	public void setDnoContract(Contract contract) {
		this.dnoContract = contract;
	}

	public GspGroup getGspGroup() {
		return gspGroup;
	}

	void setGspGroup(GspGroup gspGroup) {
		this.gspGroup = gspGroup;
	}

	public String getNote() {
		return note;
	}

	public void setNote(String note) {
		this.note = note;
	}

	public Set<Era> getEras() {
		return eras;
	}

	void setEras(Set<Era> eras) {
		this.eras = eras;
	}

	public Eras getErasInstance() {
		return new Eras(this);
	}

	public Era insertEra(HhStartDate startDate) throws HttpException {
		if (eras.isEmpty()) {
			throw new UserException(
					"Can't insert era as there aren't any existing eras");
		}
		if (startDate.after(getEraLast().getFinishDate())) {
			throw new UserException(
					"One can't add a era that starts after the supply has finished.");
		}

		Era firstEra = getEraFirst();
		Era templateEra = null;

		if (startDate.before(firstEra.getStartDate())) {
			templateEra = firstEra;
		} else {
			templateEra = getEra(startDate);
		}

		List<Site> logicalSites = new ArrayList<Site>();
		Site physicalSite = null;
		for (SiteEra ssgen : templateEra.getSiteEras()) {
			if (ssgen.getIsPhysical()) {
				physicalSite = ssgen.getSite();
			} else {
				logicalSites.add(ssgen.getSite());
			}
		}

		String impMpanCore = templateEra.getImpMpanCore();
		String impLlfcCode = null;
		Contract impSupplierContract = null;
		String impSupplierAccount = null;
		Integer impSc = null;
		if (impMpanCore != null) {
			impLlfcCode = templateEra.getImpLlfc().getCode();
			impSupplierContract = templateEra.getImpSupplierContract();
			impSupplierAccount = templateEra.getImpSupplierAccount();
			impSc = templateEra.getImpSc();
		}
		String expMpanCore = templateEra.getExpMpanCore();
		String expLlfcCode = null;
		Contract expSupplierContract = null;
		String expSupplierAccount = null;
		Integer expSc = null;
		if (expMpanCore != null) {
			expLlfcCode = templateEra.getExpLlfc().getCode();
			expSupplierContract = templateEra.getExpSupplierContract();
			expSupplierAccount = templateEra.getExpSupplierAccount();
			expSc = templateEra.getExpSc();
		}
		boolean hasImportKwh = templateEra.getChannel(true, true) != null;
		boolean hasImportKvarh = templateEra.getChannel(true, false) != null;
		boolean hasExportKwh = templateEra.getChannel(false, true) != null;
		boolean hasExportKvarh = templateEra.getChannel(false, false) != null;

		return insertEra(physicalSite, logicalSites, startDate,
				templateEra.getMopContract(), templateEra.getMopAccount(),
				templateEra.getHhdcContract(), templateEra.getHhdcAccount(),
				templateEra.getMsn(), templateEra.getPc(), templateEra.getMtc()
						.toString(), templateEra.getCop(),
				templateEra.getSsc(), impMpanCore, impLlfcCode,
				impSupplierContract, impSupplierAccount, impSc, expMpanCore,
				expLlfcCode, expSupplierContract, expSupplierAccount, expSc,
				hasImportKwh, hasImportKvarh, hasExportKwh, hasExportKvarh);
	}

	public Era insertEra(Site physicalSite, List<Site> logicalSites,
			HhStartDate startDate, Contract mopContract, String mopAccount,
			Contract hhdcContract, String hhdcAccount, String msn, Pc pc,
			String mtcCode, Cop cop, Ssc ssc, String importMpanCoreStr,
			String importLlfcCode, Contract importSupplierContract,
			String importSupplierAccount, Integer impSc,
			String exportMpanCoreStr, String exportLlfcCode,
			Contract exportSupplierContract, String exportSupplierAccount,
			Integer exportAgreedSupplyCapacity, boolean hasImportKwh,
			boolean hasImportKvarh, boolean hasExportKwh, boolean hasExportKvarh)
			throws HttpException {
		HhStartDate finishDate = null;
		Era coveredEra = null;

		if (!eras.isEmpty()) {
			if (startDate.after(getEraLast().getFinishDate())) {
				throw new UserException(
						"One can't add a era that starts after the supply has finished.");
			}

			Era firstGeneration = getEraFirst();

			if (startDate.before(firstGeneration.getStartDate())) {
				finishDate = firstGeneration.getStartDate().getPrevious();
			} else {
				coveredEra = getEra(startDate);
				if (startDate.equals(coveredEra.getStartDate())) {
					throw new UserException(
							"There's already a era with that start date.");
				}
				finishDate = coveredEra.getFinishDate();
			}
		}
		Era era = new Era(this, startDate, finishDate, mopContract, mopAccount,
				hhdcContract, hhdcAccount, msn, pc, mtcCode, cop, ssc);
		Hiber.flush();
		eras.add(era);
		Hiber.flush();
		if (hasImportKwh) {
			era.insertChannel(true, true);
		}
		if (hasImportKvarh) {
			era.insertChannel(true, false);
		}
		if (hasExportKwh) {
			era.insertChannel(false, true);
		}
		if (hasExportKvarh) {
			era.insertChannel(false, false);
		}
		Hiber.flush();
		era.attachSite(physicalSite, true);
		for (Site site : logicalSites) {
			era.attachSite(site, false);
		}
		Hiber.flush();
		era.update(startDate, finishDate, mopContract, mopAccount,
				hhdcContract, hhdcAccount, msn, pc, mtcCode, cop, ssc,
				importMpanCoreStr, importLlfcCode, importSupplierContract,
				importSupplierAccount, impSc, exportMpanCoreStr,
				exportLlfcCode, exportSupplierContract, exportSupplierAccount,
				exportAgreedSupplyCapacity);
		Hiber.flush();
		if (coveredEra != null) {
			coveredEra.update(coveredEra.getStartDate(),
					startDate.getPrevious());
		}
		Hiber.flush();
		return era;
	}

	public Era getEraFirst() {
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply order by era.startDate.date")
				.setEntity("supply", this).setMaxResults(1).uniqueResult();
	}

	public Era getEraLast() {
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply.id = :id order by era.finishDate.date desc")
				.setLong("id", getId()).setMaxResults(1).list().get(0);
	}

	public Era getEra(HhStartDate date) {
		if (date == null) {
			return getEraFinishing(null);
		} else {
			return (Era) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and era.startDate.date <= :date and (era.finishDate.date >= :date or era.finishDate.date is null)")
					.setEntity("supply", this)
					.setTimestamp("date", date.getDate()).uniqueResult();
		}
	}

	public Era getEraFinishing(HhStartDate finishDate) {
		Criteria criteria = Hiber.session().createCriteria(Era.class);
		if (finishDate == null) {
			criteria.add(Restrictions.isNull("finishDate.date"));
		} else {
			criteria.add(Restrictions.eq("finishDate.date",
					finishDate.getDate()));
		}
		criteria.createCriteria("supply").add(Restrictions.eq("id", getId()));
		return (Era) criteria.uniqueResult();
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supply");
		element.setAttribute("name", name);
		element.setAttribute("note", note);
		return element;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.SUPPLIES_INSTANCE.getUrlPath().resolve(getUriId())
				.append("/");
	}

	public void updateEra(Era era, HhStartDate start, HhStartDate finish,
			Contract mopContract, String mopAccount, Contract hhdcContract,
			String hhdcAccount, String meterSerialNumber, Pc pc,
			String mtcCode, Cop cop, Ssc ssc, String impMpanCore,
			String impLlfcCode, Contract impSupplierContract,
			String impSupplierAccount, Integer impSc, String expMpanCore,
			String expLlfcCode, Contract expSupplierContract,
			String expSupplierAccount, Integer expSc) throws HttpException {
		if (Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.id = :id")
				.setEntity("supply", this).setLong("id", era.getId())
				.uniqueResult() == null) {
			throw new UserException("The era doesn't belong to this supply.");
		}
		Era previousEra = (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.startDate.date < :startDate order by era.startDate.date desc")
				.setEntity("supply", this)
				.setTimestamp("startDate", era.getStartDate().getDate())
				.setMaxResults(1).uniqueResult();
		Era nextEra = (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.startDate.date > :startDate order by era.startDate.date")
				.setEntity("supply", this)
				.setTimestamp("startDate", era.getStartDate().getDate())
				.setMaxResults(1).uniqueResult();
		era.update(start, finish, mopContract, mopAccount, hhdcContract,
				hhdcAccount, meterSerialNumber, pc, mtcCode, cop, ssc,
				impMpanCore, impLlfcCode, impSupplierContract,
				impSupplierAccount, impSc, expMpanCore, expLlfcCode,
				expSupplierContract, expSupplierAccount, expSc);
		if (previousEra != null) {
			previousEra.update(previousEra.getStartDate(), start.getPrevious());
		}
		if (nextEra != null) {
			nextEra.update(finish.getNext(), nextEra.getFinishDate());
		}
	}

	public void deleteEra(Era era) throws HttpException {
		if (getEras().size() == 1) {
			throw new UserException(
					"The only way to delete the last era is to delete the entire supply.");
		}
		Era previousEra = getEraPrevious(era);
		Era nextEra = getEraNext(era);
		if (previousEra != null) {
			previousEra.update(previousEra.getStartDate(), era.getFinishDate());
		} else {
			nextEra.update(era.getStartDate(), nextEra.getFinishDate());
		}
		Hiber.flush();
		List<Channel> tempChannels = new ArrayList<Channel>();
		for (Channel channel : era.getChannels()) {
			tempChannels.add(channel);
		}
		for (Channel channel : tempChannels) {
			era.deleteChannel(channel.getIsImport(), channel.getIsKwh());
		}
		getEras().remove(era);
		Hiber.session().delete(era);
		Hiber.flush();
	}

	public Era getEraPrevious(Era era) throws HttpException {
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.finishDate.date = :eraFinishDate")
				.setEntity("supply", this)
				.setTimestamp("eraFinishDate",
						era.getStartDate().getPrevious().getDate())
				.uniqueResult();
	}

	public Era getEraNext(Era era) throws HttpException {
		if (era.getFinishDate() == null) {
			return null;
		}
		return (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era.startDate.date = :eraStartDate")
				.setEntity("supply", this)
				.setTimestamp("eraStartDate",
						era.getFinishDate().getNext().getDate()).uniqueResult();
	}

	@SuppressWarnings("unchecked")
	public List<Era> getEras(HhStartDate from, HhStartDate to) {
		List<Era> eras = null;
		if (to == null) {
			eras = (List<Era>) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and (era.finishDate.date >= :fromDate or era.finishDate.date is null) order by era.finishDate.date")
					.setEntity("supply", this)
					.setTimestamp("fromDate", from.getDate()).list();
		} else {
			eras = (List<Era>) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and era.startDate.date <= :toDate and (era.finishDate.date >= :fromDate or era.finishDate.date is null) order by era.finishDate.date")
					.setEntity("supply", this)
					.setTimestamp("fromDate", from.getDate())
					.setTimestamp("toDate", to.getDate()).list();
		}
		return eras;
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
		for (Era era : getEras()) {
			era.delete();
		}
		Hiber.session().delete(this);
		Hiber.flush();
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element supplyElement = (Element) toXml(
				doc,
				new XmlTree("eras").put("source").put("generatorType")
						.put("gspGroup"));
		source.appendChild(supplyElement);
		for (Source supplySource : (List<Source>) Hiber.session()
				.createQuery("from Source source order by source.code").list()) {
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
		for (GspGroup group : (List<GspGroup>) Hiber.session()
				.createQuery("from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}

		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		try {
			if (inv.hasParameter("delete")) {
				Document doc = document();
				Element source = doc.getDocumentElement();

				source.appendChild(toXml(doc));
				delete();
				Hiber.commit();
				source.appendChild(new MonadMessage(
						"Supply deleted successfully.").toXml(doc));
				inv.sendSeeOther(Chellow.SUPPLIES_INSTANCE.getEditUri());
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
				update(name, supplySource, type, this.dnoContract, gspGroup);
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

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Eras.URI_ID.equals(uriId)) {
			return getErasInstance();
		} else {
			throw new NotFoundException();
		}
	}
}
