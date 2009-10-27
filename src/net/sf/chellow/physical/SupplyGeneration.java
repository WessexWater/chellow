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

import net.sf.chellow.billing.Bill;
import net.sf.chellow.billing.Dso;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.MopContract;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.Criteria;
import org.hibernate.Query;
import org.hibernate.ScrollableResults;
import org.hibernate.criterion.Order;
import org.hibernate.criterion.Restrictions;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplyGeneration extends PersistentEntity {
	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("update")) {
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values, 0);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			Supply supply = mpanCore.getSupply();
			String dateStr = GeneralImport.addField(csvElement, "Date", values,
					1);

			SupplyGeneration supplyGeneration = supply.getGeneration(dateStr
					.length() == 0 ? null : new HhEndDate(dateStr));
			if (supplyGeneration == null) {
				throw new UserException(
						"There isn't a generation at this date.");
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 2);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values, 3);
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 4);
			Meter meter = null;
			if (meterSerialNumber.equals(GeneralImport.NO_CHANGE)) {
				meter = supplyGeneration.getMeter();
			} else if (meterSerialNumber.length() != 0) {
				meter = supply.findMeter(meterSerialNumber);
				if (meter == null) {
					meter = supply.insertMeter(meterSerialNumber);
				}
			}
			HhdcContract hhdcContract = null;
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 5);
			if (hhdcContractName.equals(GeneralImport.NO_CHANGE)) {
				hhdcContract = supplyGeneration.getHhdcContract();
				if (hhdcContract == null) {
					throw new UserException(
							"There isn't an existing HHDC contract");
				}
			} else if (hhdcContractName.length() > 0) {
				hhdcContract = HhdcContract.getHhdcContract(hhdcContractName);
			}
			String hhdcAccount = GeneralImport.addField(csvElement,
					"HHDC account", values, 6);
			if (hhdcAccount.equals(GeneralImport.NO_CHANGE)) {
				hhdcAccount = supplyGeneration.getHhdcAccount();
				if (hhdcAccount == null) {
					throw new UserException(
							"There isn't an existing HHDC account");
				}
			}
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh?", values, 7);
			boolean hasImportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(true, true) != null : Boolean
					.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh?", values, 8);
			boolean hasImportKvarh = hasImportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(true, false) != null : Boolean
					.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh?", values, 9);
			boolean hasExportKwh = hasExportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(false, true) != null : Boolean
					.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh?", values, 10);
			boolean hasExportKvarh = hasExportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(false, false) != null : Boolean
					.parseBoolean(hasExportKvarhStr);
			for (boolean isImport : new boolean[] { true, false }) {
				for (boolean isKwh : new boolean[] { true, false }) {
					boolean hasChannel;
					if (isImport) {
						if (isKwh) {
							hasChannel = hasImportKwh;
						} else {
							hasChannel = hasImportKvarh;
						}
					} else {
						if (isKwh) {
							hasChannel = hasExportKwh;
						} else {
							hasChannel = hasExportKvarh;
						}
					}
					if (hasChannel
							&& supplyGeneration.getChannel(isImport, isKwh) == null) {
						supplyGeneration.insertChannel(isImport, isKwh);
					}
					if (!hasChannel
							&& supplyGeneration.getChannel(isImport, isKwh) != null) {
						supplyGeneration.deleteChannel(isImport, isKwh);
					}
				}
			}
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values, 11);
			Ssc importSsc = null;
			Integer importAgreedSupplyCapacity = null;
			SupplierContract importSupplierContract = null;
			String importSupplierAccount = null;
			Mpan existingImportMpan = supplyGeneration.getImportMpan();
			if (importMpanStr.equals(GeneralImport.NO_CHANGE)) {
				importMpanStr = existingImportMpan == null ? null
						: existingImportMpan.toString();
			} else if (importMpanStr.trim().length() == 0) {
				importMpanStr = null;
			}
			if (importMpanStr != null) {
				String importSscCode = GeneralImport.addField(csvElement,
						"Import SSC", values, 12);
				if (importSscCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import MPAN.");
					} else {
						importSsc = existingImportMpan.getSsc();
					}
				} else {
					importSsc = importSscCode.length() == 0 ? null : Ssc
							.getSsc(importSscCode);
				}
				String importAgreedSupplyCapacityStr = GeneralImport
						.addField(csvElement, "Import Agreed Supply Capacity",
								values, 13);
				if (importAgreedSupplyCapacityStr
						.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import MPAN.");
					} else {
						importAgreedSupplyCapacity = existingImportMpan
								.getAgreedSupplyCapacity();
					}
				} else {
					try {
						importAgreedSupplyCapacity = Integer
								.parseInt(importAgreedSupplyCapacityStr);
					} catch (NumberFormatException e) {
						throw new UserException(
								"The import agreed supply capacity must be an integer. "
										+ e.getMessage());
					}
				}
				String importSupplierContractName = GeneralImport.addField(
						csvElement, "Import Supplier Contract", values, 14);
				if (importSupplierContractName.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import supplier.");
					}
					importSupplierContract = existingImportMpan
							.getSupplierContract();
				} else {
					importSupplierContract = SupplierContract
							.getSupplierContract(importSupplierContractName);
				}
				importSupplierAccount = GeneralImport.addField(csvElement,
						"Import Supplier Account", values, 15);
				if (importSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import supplier account.");
					}
					importSupplierAccount = existingImportMpan
							.getSupplierAccount();
				}
			}
			String exportMpanStr = GeneralImport.addField(csvElement,
					"Eport MPAN", values, 16);
			Ssc exportSsc = null;
			Mpan existingExportMpan = supplyGeneration.getExportMpan();
			Integer exportAgreedSupplyCapacity = null;
			if (exportMpanStr.equals(GeneralImport.NO_CHANGE)) {
				exportMpanStr = existingExportMpan == null ? null
						: existingExportMpan.toString();
			} else if (exportMpanStr.trim().length() == 0) {
				exportMpanStr = null;
			}
			SupplierContract exportSupplierContract = null;
			String exportSupplierAccount = null;
			if (exportMpanStr != null) {
				String exportSscCode = GeneralImport.addField(csvElement,
						"Export SSC", values, 17);
				if (exportSscCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export MPAN.");
					} else {
						exportSsc = existingExportMpan.getSsc();
					}
				} else {
					exportSsc = exportSscCode.length() == 0 ? null : Ssc
							.getSsc(exportSscCode);
				}
				String exportAgreedSupplyCapacityStr = GeneralImport
						.addField(csvElement, "Export Agreed Supply Capacity",
								values, 18);
				if (exportAgreedSupplyCapacityStr
						.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export MPAN.");
					} else {
						exportAgreedSupplyCapacity = existingExportMpan
								.getAgreedSupplyCapacity();
					}
				} else {
					try {
						exportAgreedSupplyCapacity = new Integer(
								exportAgreedSupplyCapacityStr);
					} catch (NumberFormatException e) {
						throw new UserException(
								"The export supply capacity must be an integer. "
										+ e.getMessage());
					}
				}
				String exportSupplierContractName = GeneralImport.addField(
						csvElement, "Export Supplier Contract", values, 19);
				if (exportSupplierContractName.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export supplier contract.");
					}
					exportSupplierContract = existingExportMpan
							.getSupplierContract();
				} else {
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractName);
				}
				exportSupplierAccount = GeneralImport.addField(csvElement,
						"Export Supplier Account", values, 20);
				if (exportSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export MPAN.");
					}
					exportSupplierAccount = existingExportMpan
							.getSupplierAccount();
				}
			}
			supplyGeneration.update(startDateStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getStartDate() : new HhEndDate("start", startDateStr),
					finishDateStr.length() == 0 ? null : (finishDateStr
							.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
							.getFinishDate() : new HhEndDate("finish",
							finishDateStr)), hhdcContract, hhdcAccount, meter,
					importMpanStr, importSsc, importSupplierContract,
					importSupplierAccount, importAgreedSupplyCapacity,
					exportMpanStr, exportSsc, exportSupplierContract,
					exportSupplierAccount, exportAgreedSupplyCapacity);
		} else if (action.equals("delete")) {
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values, 0);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			Supply supply = mpanCore.getSupply();
			String dateStr = GeneralImport.addField(csvElement, "Date", values,
					1);

			SupplyGeneration supplyGeneration = supply.getGeneration(dateStr
					.length() == 0 ? null : new HhEndDate(dateStr));
			if (supplyGeneration == null) {
				throw new UserException(
						"There isn't a generation at this date.");
			}
			supply.deleteGeneration(supplyGeneration);
		} else if (action.equals("insert")) {
			String siteCode = GeneralImport.addField(csvElement, "Site Code",
					values, 0);
			Site site = Site.getSite(siteCode);
			Supply supply = null;
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 1);
			HhEndDate startDate = startDateStr.length() == 0 ? null
					: new HhEndDate(startDateStr);
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 2);
			HhdcContract hhdcContract = null;
			String hhdcAccountReference = GeneralImport.addField(csvElement,
					"HHDC Account Reference", values, 3);
			if (hhdcContractName.length() > 0) {
				hhdcContract = HhdcContract.getHhdcContract(hhdcContractName);
			}
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh", values, 4);
			boolean hasImportKwh = Boolean.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh", values, 5);
			boolean hasImportKvarh = Boolean.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh", values, 6);
			Boolean hasExportKwh = Boolean.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh", values, 7);
			Boolean hasExportKvarh = Boolean.parseBoolean(hasExportKvarhStr);
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 8);
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values, 9);
			SupplierContract importSupplierContract = null;
			String importSupplierAccountReference = null;
			Ssc importSsc = null;
			Integer importAgreedSupplyCapacity = null;
			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values, 10);
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values, 11);
			String importContractSupplierName = GeneralImport.addField(
					csvElement, "Import Supplier Contract", values, 12);
			importSupplierAccountReference = GeneralImport.addField(csvElement,
					"Import Supplier Account Reference", values, 13);
			if (importMpanStr.length() > 0) {
				MpanCore mpanCore = MpanCore.findMpanCore(Mpan
						.getCore(importMpanStr));
				if (mpanCore != null) {
					supply = mpanCore.getSupply();
				}
				importSsc = importSscCode.length() == 0 ? null : Ssc
						.getSsc(importSscCode);
				try {
					importAgreedSupplyCapacity = Integer
							.parseInt(importAgreedSupplyCapacityStr);
				} catch (NumberFormatException e) {
					throw new UserException(
							"The import agreed supply capacity must be an integer. "
									+ e.getMessage());
				}
				importSupplierContract = SupplierContract
						.getSupplierContract(importContractSupplierName);
			}
			String exportMpanStr = GeneralImport.addField(csvElement,
					"Eport MPAN", values, 14);
			Integer exportAgreedSupplyCapacity = null;
			Ssc exportSsc = null;
			SupplierContract exportSupplierContract = null;
			String exportSupplierAccountReference = null;

			if (exportMpanStr.length() > 0) {
				String exportSscCode = GeneralImport.addField(csvElement,
						"Export SSC", values, 15);
				String exportAgreedSupplyCapacityStr = GeneralImport
						.addField(csvElement, "Export Agreed Supply Capacity",
								values, 16);
				String exportContractSupplierName = GeneralImport.addField(
						csvElement, "Export Supplier Contract", values, 17);
				exportSupplierAccountReference = GeneralImport.addField(
						csvElement, "Export Supplier Account", values, 18);
				if (supply == null) {
					supply = MpanCore.getMpanCore(Mpan.getCore(exportMpanStr))
							.getSupply();
				}
				exportSsc = exportSscCode.length() == 0 ? null : Ssc
						.getSsc(exportSscCode);
				try {
					exportAgreedSupplyCapacity = new Integer(
							exportAgreedSupplyCapacityStr);
				} catch (NumberFormatException e) {
					throw new UserException(
							"The export supply capacity must be an integer. "
									+ e.getMessage());
				}
				exportSupplierContract = SupplierContract
						.getSupplierContract(exportContractSupplierName);
			}
			Map<Site, Boolean> siteMap = new HashMap<Site, Boolean>();
			siteMap.put(site, true);
			SupplyGeneration generation = supply.insertGeneration(siteMap,
					startDate, hhdcContract, hhdcAccountReference,
					meterSerialNumber, importMpanStr, importSsc,
					importSupplierContract, importSupplierAccountReference,
					importAgreedSupplyCapacity, exportMpanStr, exportSsc,
					exportSupplierContract, exportSupplierAccountReference,
					exportAgreedSupplyCapacity);
			for (boolean isImport : new boolean[] { true, false }) {
				for (boolean isKwh : new boolean[] { true, false }) {
					boolean hasChannel;
					if (isImport) {
						if (isKwh) {
							hasChannel = hasImportKwh;
						} else {
							hasChannel = hasImportKvarh;
						}
					} else {
						if (isKwh) {
							hasChannel = hasExportKwh;
						} else {
							hasChannel = hasExportKvarh;
						}
					}
					Channel channel = generation.getChannel(isImport, isKwh);
					if (hasChannel && channel == null) {
						generation.insertChannel(isImport, isKwh);
					} else if (!hasChannel && channel != null) {
						generation.deleteChannel(isImport, isKwh);
					}
				}
			}
		}
	}

	static public SupplyGeneration getSupplyGeneration(Long id)
			throws HttpException {
		SupplyGeneration supplyGeneration = (SupplyGeneration) Hiber.session()
				.get(SupplyGeneration.class, id);
		if (supplyGeneration == null) {
			throw new UserException(
					"There is no supply generation with that id.");
		}
		return supplyGeneration;
	}

	private Supply supply;

	private Set<SiteSupplyGeneration> siteSupplyGenerations;

	private HhEndDate startDate;

	private HhEndDate finishDate;
	private MopContract mopContract;
	private String mopAccount;
	private Meter meter;

	private HhdcContract hhdcContract;
	private String hhdcAccount;
	private Pc pc;
	private Mpan importMpan;

	private Mpan exportMpan;

	private Set<Mpan> mpans;
	private Set<Channel> channels;

	SupplyGeneration() {
	}

	SupplyGeneration(Supply supply, HhEndDate startDate, HhEndDate finishDate,
			HhdcContract hhdcContract, String hhdcAccount, Meter meter)
			throws HttpException {
		setChannels(new HashSet<Channel>());
		setSupply(supply);
		setSiteSupplyGenerations(new HashSet<SiteSupplyGeneration>());
		setMpans(new HashSet<Mpan>());
		setPc(Pc.getPc("00"));
		setStartDate(startDate);
		setFinishDate(finishDate);
		setHhdcContract(hhdcContract);
		setHhdcAccount(hhdcAccount);
		setMeter(meter);
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Supply getSupply() {
		return supply;
	}

	public Set<SiteSupplyGeneration> getSiteSupplyGenerations() {
		return siteSupplyGenerations;
	}

	protected void setSiteSupplyGenerations(
			Set<SiteSupplyGeneration> siteSupplyGenerations) {
		this.siteSupplyGenerations = siteSupplyGenerations;
	}

	public HhEndDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhEndDate startDate) {
		this.startDate = startDate;
	}

	public HhEndDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhEndDate finishDate) {
		this.finishDate = finishDate;
	}

	public MopContract getMopContract() {
		return mopContract;
	}

	void setMopContract(MopContract mopContract) {
		this.mopContract = mopContract;
	}

	public String getMopAccount() {
		return mopAccount;
	}

	void setMopAccount(String mopAccount) {
		this.mopAccount = mopAccount;
	}

	public HhdcContract getHhdcContract() {
		return hhdcContract;
	}

	void setHhdcContract(HhdcContract hhdcContract) {
		this.hhdcContract = hhdcContract;
	}

	public String getHhdcAccount() {
		return hhdcAccount;
	}

	void setHhdcAccount(String hhdcAccount) {
		this.hhdcAccount = hhdcAccount;
	}

	public Pc getPc() {
		return pc;
	}

	void setPc(Pc pc) {
		this.pc = pc;
	}

	public Mpan getImportMpan() {
		return importMpan;
	}

	void setImportMpan(Mpan importMpan) {
		this.importMpan = importMpan;
	}

	public Mpan getMpan(boolean isImport) {
		return isImport ? getImportMpan() : getExportMpan();
	}

	public Set<Channel> getChannels() {
		return channels;
	}

	void setChannels(Set<Channel> channels) {
		this.channels = channels;
	}

	public Dso getDso() {
		if (importMpan == null) {
			return exportMpan.getCore().getDso();
		} else {
			return importMpan.getCore().getDso();
		}
	}

	public void attachSite(Site site) throws HttpException {
		attachSite(site, false);
	}

	public void attachSite(Site site, boolean isLocation) throws HttpException {
		boolean alreadyThere = false;
		for (SiteSupplyGeneration siteSupplyGeneration : siteSupplyGenerations) {
			if (siteSupplyGeneration.getSite().equals(site)) {
				alreadyThere = true;
				break;
			}
		}
		if (alreadyThere) {
			throw new UserException(
					"The site is already attached to this supply.");
		} else {
			SiteSupplyGeneration siteSupplyGeneration = new SiteSupplyGeneration(
					site, this, false);
			siteSupplyGenerations.add(siteSupplyGeneration);
			site.attachSiteSupplyGeneration(siteSupplyGeneration);
		}
		if (isLocation) {
			setPhysicalLocation(site);
		}
	}

	public void detachSite(Site site) throws HttpException {
		if (siteSupplyGenerations.size() < 2) {
			throw new UserException(
					"A supply has to be attached to at least one site.");
		}
		SiteSupplyGeneration siteSupplyGeneration = (SiteSupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.site = :site")
				.setEntity("supplyGeneration", this).setEntity("site", site)
				.uniqueResult();
		if (siteSupplyGeneration == null) {
			throw new UserException(
					"Can't detach this site, as it wasn't attached in the first place.");
		}
		siteSupplyGenerations.remove(siteSupplyGeneration);
		siteSupplyGenerations.iterator().next().setIsPhysical(true);
		Hiber.flush();
		site.detachSiteSupplyGeneration(siteSupplyGeneration);
		Hiber.flush();
	}

	public Mpan getExportMpan() {
		return exportMpan;
	}

	public void setExportMpan(Mpan exportMpan) {
		this.exportMpan = exportMpan;
	}

	public Set<Mpan> getMpans() {
		return mpans;
	}

	void setMpans(Set<Mpan> mpans) {
		this.mpans = mpans;
	}

	public Meter getMeter() {
		return meter;
	}

	void setMeter(Meter meter) {
		this.meter = meter;
	}

	public Channel getChannel(boolean isImport, boolean isKwh) {
		for (Channel candidateChannel : channels) {
			if (candidateChannel.getIsImport() == isImport
					&& candidateChannel.getIsKwh() == isKwh) {
				return candidateChannel;
			}
		}
		return null;
	}

	public void update(HhEndDate startDate, HhEndDate finishDate,
			HhdcContract hhdcContract, String hhdcAccount, Meter meter)
			throws HttpException {
		String importMpanStr = null;
		Ssc importSsc = null;
		SupplierContract importSupplierContract = null;
		String importSupplierAccount = null;
		Integer importAgreedSupplyCapacity = null;
		String exportMpanStr = null;
		Ssc exportSsc = null;
		SupplierContract exportSupplierContract = null;
		String exportSupplierAccount = null;
		Integer exportAgreedSupplyCapacity = null;
		if (importMpan != null) {
			importMpanStr = importMpan.toString();
			importSsc = importMpan.getSsc();
			importSupplierAccount = importMpan.getSupplierAccount();
			importSupplierContract = importMpan.getSupplierContract();
			importAgreedSupplyCapacity = importMpan.getAgreedSupplyCapacity();
		}
		if (exportMpan != null) {
			exportMpanStr = exportMpan.toString();
			exportSsc = exportMpan.getSsc();
			exportSupplierAccount = exportMpan.getSupplierAccount();
			exportSupplierContract = exportMpan.getSupplierContract();
			exportAgreedSupplyCapacity = exportMpan.getAgreedSupplyCapacity();
		}
		update(startDate, finishDate, hhdcContract, hhdcAccount, meter,
				importMpanStr, importSsc, importSupplierContract,
				importSupplierAccount, importAgreedSupplyCapacity,
				exportMpanStr, exportSsc, exportSupplierContract,
				exportSupplierAccount, exportAgreedSupplyCapacity);
	}

	/*
	 * @SuppressWarnings("unchecked") public void internalUpdate(HhEndDate
	 * startDate, HhEndDate finishDate, HhdcContract hhdcContract, String
	 * hhdcAccount, Meter meter, String importMpanStr, Ssc importSsc,
	 * SupplierContract importSupplierContract, String importSupplierAccount,
	 * Integer importAgreedSupplyCapacity, String exportMpanStr, Ssc exportSsc,
	 * SupplierContract exportSupplierContract, String exportSupplierAccount,
	 * Integer exportAgreedSupplyCapacity) throws HttpException { Mpan
	 * origImportMpan = getImportMpan(); String origImportSupplierAccount =
	 * null; if (origImportMpan != null) { origImportSupplierAccount =
	 * origImportMpan.getSupplierAccount(); } Mpan origExportMpan =
	 * getExportMpan(); String origExportSupplierAccount = null; if
	 * (origExportMpan != null) { origExportSupplierAccount =
	 * origExportMpan.getSupplierAccount(); } String originalHhdcAccount =
	 * this.hhdcAccount; HhEndDate originalStartDate = this.startDate; HhEndDate
	 * originalFinishDate = this.finishDate; List<Bill> originalHhdcBills =
	 * null; if (originalHhdcAccount == null) { originalHhdcBills = new
	 * ArrayList<Bill>(); } else if (((Long) Hiber .session() .createQuery(
	 * "select count(*) from SupplyGeneration generation where generation.hhdcAccount = :hhdcAccount and generation.startDate.date = :startDate"
	 * ) .setTimestamp("startDate", originalStartDate.getDate())
	 * .setEntity("hhdcAccount", originalHhdcAccount).uniqueResult()) > 1) {
	 * originalHhdcBills = new ArrayList<Bill>(); } else { Query
	 * originalBillsQuery = null; if (originalFinishDate == null) {
	 * originalBillsQuery = Hiber .session() .createQuery(
	 * "from Bill bill where bill.account = :account and bill.startDate.date >= :startDate"
	 * ); } else { originalBillsQuery = Hiber .session() .createQuery(
	 * "from Bill bill where bill.account = :account and bill.startDate.date >= :startDate and bill.startDate.date <= :finishDate"
	 * ) .setTimestamp("finishDate", originalFinishDate.getDate()); }
	 * originalHhdcBills = (List<Bill>) originalBillsQuery.setEntity( "account",
	 * originalHhdcAccount).setTimestamp("startDate",
	 * originalStartDate.getDate()).list(); } List<Bill> origImportSupplierBills
	 * = null; if (origImportSupplierAccount == null) { origImportSupplierBills
	 * = new ArrayList<Bill>(); } else if (((Long) Hiber .session()
	 * .createQuery(
	 * "select count(*) from SupplyGeneration generation where generation.importMpan is not null and generation.importMpan.supplierAccount = :supplierAccount and generation.startDate.date = :startDate"
	 * ) .setTimestamp("startDate", originalStartDate.getDate())
	 * .setEntity("supplierAccount", origImportSupplierAccount) .uniqueResult())
	 * > 1) { origImportSupplierBills = new ArrayList<Bill>(); } else { Query
	 * originalBillsQuery = null; if (originalFinishDate == null) {
	 * originalBillsQuery = Hiber .session() .createQuery(
	 * "from Bill bill where bill.account = :account and bill.startDate.date >= :startDate"
	 * ); } else { originalBillsQuery = Hiber .session() .createQuery(
	 * "from Bill bill where bill.account = :account and bill.startDate.date >= :startDate and bill.startDate.date <= :finishDate"
	 * ) .setTimestamp("finishDate", originalFinishDate.getDate()); }
	 * origImportSupplierBills = (List<Bill>) originalBillsQuery
	 * .setEntity("account", origImportSupplierAccount)
	 * .setTimestamp("startDate", originalStartDate.getDate()) .list(); }
	 * 
	 * List<Bill> origExportSupplierBills = null; if (origExportSupplierAccount
	 * == null) { origExportSupplierBills = new ArrayList<Bill>(); } else if
	 * (((Long) Hiber .session() .createQuery(
	 * "select count(*) from SupplyGeneration generation where generation.exportMpan is not null and generation.importMpan.supplierAccount = :supplierAccount and generation.startDate.date = :startDate"
	 * ) .setTimestamp("startDate", originalStartDate.getDate())
	 * .setEntity("supplierAccount", origExportSupplierAccount) .uniqueResult())
	 * > 1) { origExportSupplierBills = new ArrayList<Bill>(); } else { Query
	 * originalBillsQuery = null; if (originalFinishDate == null) {
	 * originalBillsQuery = Hiber .session() .createQuery(
	 * "from Bill bill where bill.account = :account and bill.startDate.date >= :startDate"
	 * ); } else { originalBillsQuery = Hiber .session() .createQuery(
	 * "from Bill bill where bill.account = :account and bill.startDate.date >= :startDate and bill.startDate.date <= :finishDate"
	 * ) .setTimestamp("finishDate", originalFinishDate.getDate()); }
	 * origExportSupplierBills = (List<Bill>) originalBillsQuery
	 * .setEntity("account", origExportSupplierAccount)
	 * .setTimestamp("startDate", originalStartDate.getDate()) .list(); }
	 * 
	 * SupplyGeneration previousGeneration = supply
	 * .getGenerationPrevious(this); if (finishDate != null &&
	 * startDate.getDate().after(finishDate.getDate())) { throw new
	 * UserException(
	 * "The generation start date can't be after the finish date."); } if
	 * (startDate == null) { throw new
	 * InternalException("start date can't be null."); }
	 * setStartDate(startDate); setFinishDate(finishDate);
	 * setHhdcContract(hhdcContract); if (hhdcContract == null) {
	 * setHhdcAccount(null); } else { if (hhdcAccount == null) { throw new
	 * UserException
	 * ("If there's a HHDC contract, there must be an account reference."); }
	 * hhdcAccount = hhdcAccount.trim(); if (hhdcAccount.length() == 0) { throw
	 * newUserException(
	 * "If there's a HHDC contract, there must be an account reference."); }
	 * setHhdcAccount(hhdcAccount); } if (hhdcAccount == null &&
	 * !channels.isEmpty()) { throw new UserException(
	 * "Can't remove the HHDC account while there are still channels there."); }
	 * setMeter(meter); // resolve any snags channel snags outside range for
	 * (Channel channel : channels) { channel.onSupplyGenerationChange(); }
	 * 
	 * Pc importPc = null; Pc exportPc = null; if (importMpan == null) { if
	 * (importMpanStr != null && importMpanStr.length() != 0) {
	 * setImportMpan(new Mpan(this, importMpanStr, importSsc,
	 * importSupplierContract, importSupplierAccount,
	 * importAgreedSupplyCapacity)); mpans.add(getImportMpan()); } } else { if
	 * (importMpanStr == null || importMpanStr.length() == 0) {
	 * mpans.remove(importMpan); setImportMpan(null); } else {
	 * importMpan.update(importMpanStr, importSsc, importSupplierContract,
	 * importSupplierAccount, importAgreedSupplyCapacity); } } if (exportMpan ==
	 * null) { if (exportMpanStr != null && exportMpanStr.length() != 0) {
	 * setExportMpan(new Mpan(this, exportMpanStr, exportSsc,
	 * exportSupplierContract, exportSupplierAccount,
	 * exportAgreedSupplyCapacity)); mpans.add(getExportMpan()); } } else { if
	 * (exportMpanStr == null || exportMpanStr.length() == 0) {
	 * mpans.remove(exportMpan); setExportMpan(null); } else {
	 * exportMpan.update(exportMpanStr, exportSsc, exportSupplierContract,
	 * exportSupplierAccount, exportAgreedSupplyCapacity); } } if (importMpan ==
	 * null && exportMpan == null) { throw new UserException(document(),
	 * "A supply generation must have at least one MPAN."); } if
	 * (previousGeneration != null) { boolean isOverlap = false; if (importMpan
	 * != null) { Mpan prevImportMpan = previousGeneration.getImportMpan(); if
	 * (prevImportMpan != null && importMpan.getCore()
	 * .equals(prevImportMpan.getCore())) { isOverlap = true; } } if (!isOverlap
	 * && exportMpan != null) { Mpan prevExportMpan =
	 * previousGeneration.getExportMpan(); if (prevExportMpan != null &&
	 * exportMpan.getCore() .equals(prevExportMpan.getCore())) { isOverlap =
	 * true; } } if (!isOverlap) { throw new UserException(
	 * "MPAN cores can't change without an overlapping period."); } } if
	 * (importMpan != null) { if (!importMpan.getLlfc().getIsImport()) { throw
	 * new UserException(document(), "The import line loss factor '" +
	 * importMpan.getLlfc() + "' says that the MPAN is actually export."); }
	 * importPc = Mpan.pc(importMpanStr); } if (exportMpan != null) { if
	 * (exportMpan.getLlfc().getIsImport()) { throw new UserException(
	 * "Problem with the export MPAN with core '" + exportMpan.getCore() +
	 * "'. The Line Loss Factor '" + exportMpan.getLlfc() +
	 * "' says that the MPAN is actually import."); } exportPc =
	 * Mpan.pc(exportMpanStr); } if (importMpan != null && exportMpan != null) {
	 * if (!importMpan.getCore().getDso().equals(
	 * exportMpan.getCore().getDso())) { throw new UserException(
	 * "Two MPANs on the same supply generation must have the same DSO."); } if
	 * (!importMpan.getLlfc().getVoltageLevel().equals(
	 * exportMpan.getLlfc().getVoltageLevel())) { throw new UserException(
	 * "The voltage level indicated by the Line Loss Factor must be the same for both the MPANs."
	 * ); } if (!importPc.equals(exportPc)) { throw new UserException(
	 * "The Profile Classes of both MPANs must be the same."); } } Dso dso =
	 * getDso(); if (dso != null && dso.getCode().equals("22")) {
	 * 
	 * if (importMpan != null) { LineLossFactorCode code =
	 * importLineLossFactor.getCode(); if ((code.equals(new
	 * LineLossFactorCode("520")) || code.equals(new LineLossFactorCode("550"))
	 * || code .equals(new LineLossFactorCode("580"))) && getExportMpan() ==
	 * null) { throw UserException .newOk("The Line Loss Factor of the import
	 * MPAN says that there should be an export MPAN, but there isn't one."); }
	 * }
	 * 
	 * 
	 * if (getExportMpan() != null && getImportMpan() != null) { int code =
	 * getImportMpan().getLlfc().getCode(); if (code != 520 && code != 550 &&
	 * code != 580) { throw new UserException(
	 * "The DSO is 22, there's an export MPAN and the Line Loss Factor of the import MPAN "
	 * + getImportMpan() + " can only be 520, 550 or 580."); } } } if (importPc
	 * == null) { setPc(exportPc); } else { setPc(importPc); }
	 * 
	 * // move hhdc bills if necessary if (originalHhdcBills.size() > 0 &&
	 * !originalHhdcAccount.equals(hhdcAccount)) { if (hhdcAccount == null) {
	 * throw new UserException(
	 * "There are HHDC bills associated with this supply generation, so you can't remove the HHDC account."
	 * ); } else { Query billUpdateQuery = null; if (finishDate == null) {
	 * billUpdateQuery = Hiber .session() .createQuery(
	 * "update Bill bill set bill.account = : where bill.account = :account and bill.startDate.date >= :generationStart"
	 * ); } else { billUpdateQuery = Hiber .session() .createQuery(
	 * "update Bill bill where bill.account = :account and bill.startDate.date >= :generationStart and bill.startDate.date <= :generationFinish"
	 * ) .setTimestamp("generationFinish", finishDate.getDate()); }
	 * billUpdateQuery.setEntity("account", originalHhdcAccount)
	 * .setTimestamp("generationStart", startDate.getDate()) .executeUpdate(); }
	 * } Hiber.flush(); for (Bill bill : originalHhdcBills) { if (((Long) Hiber
	 * .session() .createQuery(
	 * "count(*) from SupplyGeneration generation where generation.hhdcAccount = :hhdcAccount and (generation.finishDate.date is null or :startDate <= generation.finishDate.date) and :startDate >= generation.startDate.date"
	 * ) .setEntity("hhdcAccount", bill.getMpan()).setTimestamp( "start",
	 * bill.getStartDate().getDate()) .uniqueResult()) == 0) { throw new
	 * UserException( "The bill " + bill +
	 * " has been left stranded without a supply generation attached to it."); }
	 * } Hiber.flush(); // check if we can delete the old hhdc account if
	 * (originalHhdcAccount != null && !originalHhdcAccount.equals(hhdcAccount)
	 * && ((Long) Hiber .session() .createQuery(
	 * "select count(*) from SupplyGeneration generation where generation.hhdcAccount = :hhdcAccount"
	 * ) .setEntity("hhdcAccount", originalHhdcAccount) .uniqueResult()) == 0) {
	 * originalHhdcAccount.deleteSnag(SupplySnag.MISSING_HHDC_BILL, null);
	 * Hiber.session().delete(originalHhdcAccount); Hiber.flush(); }
	 * 
	 * // move import supplier bills if necessary if
	 * (origImportSupplierBills.size() > 0 &&
	 * !origImportSupplierAccount.equals(importMpan == null ? null :
	 * importMpan.getSupplierAccount())) { if (importMpan == null) { throw new
	 * UserException(
	 * "There are Supplier bills associated with the import MPAN of this supply generation, so you can't remove the import MPAN."
	 * ); } else { Query billUpdateQuery = null; if (finishDate == null) {
	 * billUpdateQuery = Hiber .session() .createQuery(
	 * "update Bill bill set bill.account = : where bill.account = :account and bill.startDate.date >= :generationStart"
	 * ); } else { billUpdateQuery = Hiber .session() .createQuery(
	 * "update Bill bill where bill.account = :account and bill.startDate.date >= :generationStart and bill.startDate.date <= :generationFinish"
	 * ) .setTimestamp("generationFinish", finishDate.getDate()); }
	 * billUpdateQuery.setEntity("account", origImportSupplierAccount)
	 * .setTimestamp("generationStart", startDate.getDate()) .executeUpdate(); }
	 * } Hiber.flush(); for (Bill bill : originalHhdcBills) { if (((Long) Hiber
	 * .session() .createQuery(
	 * "count(*) from Mpan mpan where mpan.supplierAccount = :supplierAccount and (generation.finishDate.date is null or :startDate <= generation.finishDate.date) and :startDate >= generation.startDate.date"
	 * ) .setEntity("supplierAccount", bill.getMpan()) .setTimestamp("start",
	 * bill.getStartDate().getDate()) .uniqueResult()) == 0) { throw new
	 * UserException( "The bill " + bill +
	 * " has been left stranded without an MPAN attached to it."); } } // check
	 * if we can delete the old import supplier account if
	 * (origImportSupplierAccount != null &&
	 * !origImportSupplierAccount.equals(importMpan == null ? null :
	 * importMpan.getSupplierAccount()) && ((Long) Hiber .session()
	 * .createQuery(
	 * "select count(*) from Mpan mpan where mpan.supplierAccount = :supplierAccount"
	 * ) .setEntity("supplierAccount", origImportSupplierAccount)
	 * .uniqueResult()) == 0) {
	 * Hiber.session().delete(origImportSupplierAccount); Hiber.flush(); }
	 * 
	 * // move export supplier bills if necessary if
	 * (origExportSupplierBills.size() > 0 &&
	 * !originalHhdcAccount.equals(hhdcAccount)) { if (hhdcAccount == null) {
	 * throw new UserException(
	 * "There are HHDC bills associated with this supply generation, so you can't remove the HHDC account."
	 * ); } else { Query billUpdateQuery = null; if (finishDate == null) {
	 * billUpdateQuery = Hiber .session() .createQuery(
	 * "update Bill bill set bill.account = : where bill.account = :account and bill.startDate.date >= :generationStart"
	 * ); } else { billUpdateQuery = Hiber .session() .createQuery(
	 * "update Bill bill where bill.account = :account and bill.startDate.date >= :generationStart and bill.startDate.date <= :generationFinish"
	 * ) .setTimestamp("generationFinish", finishDate.getDate()); }
	 * billUpdateQuery.setEntity("account", originalHhdcAccount)
	 * .setTimestamp("generationStart", startDate.getDate()) .executeUpdate(); }
	 * } Hiber.flush(); for (Bill bill : originalHhdcBills) { if (((Long) Hiber
	 * .session() .createQuery(
	 * "count(*) from SupplyGeneration generation where generation.hhdcAccount = :hhdcAccount and (generation.finishDate.date is null or :startDate <= generation.finishDate.date) and :startDate >= generation.startDate.date"
	 * ) .setEntity("hhdcAccount", bill.getMpan()).setTimestamp( "start",
	 * bill.getStartDate().getDate()) .uniqueResult()) == 0) { throw new
	 * UserException( "The bill " + bill +
	 * " has been left stranded without a supply generation attached to it."); }
	 * } // check if we can delete the old export supplier account if
	 * (origExportSupplierAccount != null &&
	 * !origExportSupplierAccount.equals(importMpan == null ? null :
	 * importMpan.getSupplierAccount()) && ((Long) Hiber .session()
	 * .createQuery(
	 * "select count(*) from Mpan mpan where mpan.supplierAccount = :supplierAccount"
	 * ) .setEntity("supplierAccount", origExportSupplierAccount)
	 * .uniqueResult()) == 0) {
	 * Hiber.session().delete(origExportSupplierAccount); Hiber.flush(); } }
	 */
	void delete() throws HttpException {
		List<SiteSupplyGeneration> ssGens = new ArrayList<SiteSupplyGeneration>();
		for (SiteSupplyGeneration ssGen : siteSupplyGenerations) {
			ssGens.add(ssGen);
		}
		for (SiteSupplyGeneration ssGen : ssGens) {
			siteSupplyGenerations.remove(ssGen);
			Hiber.flush();
			ssGen.getSite().detachSiteSupplyGeneration(ssGen);
			Hiber.flush();
		}
		List<Channel> ssChannels = new ArrayList<Channel>();
		for (Channel channel : channels) {
			ssChannels.add(channel);
		}
		for (Channel channel : ssChannels) {
			deleteChannel(channel.getIsImport(), channel.getIsKwh());
		}
		Criteria crit = Hiber.session().createCriteria(RegisterRead.class).createAlias("meter", "mtr").add(Restrictions.eq("mtr.supply", supply)).add(Restrictions.ge("presentDate.date", startDate.getDate()));
	if (finishDate != null) {
		crit.add(Restrictions.le("presentDate", finishDate.getDate()));
	}
	}

	public void update(HhEndDate startDate, HhEndDate finishDate)
			throws HttpException {
		if (startDate.equals(this.startDate)
				&& HhEndDate.isEqual(finishDate, this.finishDate)) {
			return;
		} else {
			update(startDate, finishDate, hhdcContract, hhdcAccount, meter);
		}
	}

	@SuppressWarnings("unchecked")
	public void update(HhEndDate startDate, HhEndDate finishDate,
			HhdcContract hhdcContract, String hhdcAccount, Meter meter,
			String importMpanStr, Ssc importSsc,
			SupplierContract importSupplierContract,
			String importSupplierAccount, Integer importAgreedSupplyCapacity,
			String exportMpanStr, Ssc exportSsc,
			SupplierContract exportSupplierContract,
			String exportSupplierAccount, Integer exportAgreedSupplyCapacity)
			throws HttpException {
		if (startDate.after(finishDate)) {
			throw new UserException(
					"The generation start date can't be after the finish date.");
		}
		Pc importPc = null;
		Pc exportPc = null;
		if (importMpan == null) {
			if (importMpanStr != null && importMpanStr.length() != 0) {
				Hiber.flush();
				Mpan te = new Mpan(this, importMpanStr, importSsc,
						importSupplierContract, importSupplierAccount,
						importAgreedSupplyCapacity);
				Hiber.session().save(te);
				Hiber.flush();
				setImportMpan(te);
				Hiber.flush();
				mpans.add(getImportMpan());
				Hiber.flush();
			}
		} else {
			if (importMpanStr == null || importMpanStr.length() == 0) {
				mpans.remove(importMpan);
				setImportMpan(null);
			} else {
				importMpan.update(importMpanStr, importSsc,
						importSupplierContract, importSupplierAccount,
						importAgreedSupplyCapacity);
			}
		}
		Hiber.flush();
		if (exportMpan == null) {
			if (exportMpanStr != null && exportMpanStr.length() != 0) {
				setExportMpan(new Mpan(this, exportMpanStr, exportSsc,
						exportSupplierContract, exportSupplierAccount,
						exportAgreedSupplyCapacity));
				mpans.add(getExportMpan());
			}
		} else {
			if (exportMpanStr == null || exportMpanStr.length() == 0) {
				mpans.remove(exportMpan);
				setExportMpan(null);
			} else {
				exportMpan.update(exportMpanStr, exportSsc,
						exportSupplierContract, exportSupplierAccount,
						exportAgreedSupplyCapacity);
			}
		}
		if (importMpan == null && exportMpan == null) {
			throw new UserException(document(),
					"A supply generation must have at least one MPAN.");
		}
		if (importMpan != null) {
			if (!importMpan.getLlfc().getIsImport()) {
				throw new UserException(document(),
						"The import line loss factor '" + importMpan.getLlfc()
								+ "' says that the MPAN is actually export.");
			}
			importPc = Mpan.pc(importMpanStr);
		}
		if (exportMpan != null) {
			if (exportMpan.getLlfc().getIsImport()) {
				throw new UserException(
						"Problem with the export MPAN with core '"
								+ exportMpan.getCore()
								+ "'. The Line Loss Factor '"
								+ exportMpan.getLlfc()
								+ "' says that the MPAN is actually import.");
			}
			exportPc = Mpan.pc(exportMpanStr);
		}
		if (importMpan != null && exportMpan != null) {
			if (!importMpan.getCore().getDso().equals(
					exportMpan.getCore().getDso())) {
				throw new UserException(
						"Two MPANs on the same supply generation must have the same DSO.");
			}
			if (!importMpan.getLlfc().getVoltageLevel().equals(
					exportMpan.getLlfc().getVoltageLevel())) {
				throw new UserException(
						"The voltage level indicated by the Line Loss Factor must be the same for both the MPANs.");
			}
			if (!importPc.equals(exportPc)) {
				throw new UserException(
						"The Profile Classes of both MPANs must be the same.");
			}
		}
		Dso dso = getDso();
		if (dso.getCode().equals("22")) {
			/*
			 * if (importMpan != null) { LineLossFactorCode code =
			 * importLineLossFactor.getCode(); if ((code.equals(new
			 * LineLossFactorCode("520")) || code.equals(new
			 * LineLossFactorCode("550")) || code .equals(new
			 * LineLossFactorCode("580"))) && getExportMpan() == null) { throw
			 * UserException .newOk("The Line Loss Factor of the import MPAN
			 * says that there should be an export MPAN, but there isn't one.");
			 * } }
			 */

			if (getExportMpan() != null && getImportMpan() != null) {
				int code = getImportMpan().getLlfc().getCode();
				if (code != 520 && code != 550 && code != 580) {
					throw new UserException(
							"The DSO is 22, there's an export MPAN and the Line Loss Factor of the import MPAN "
									+ getImportMpan()
									+ " can only be 520, 550 or 580.");
				}
			}
		}
		if (importPc == null) {
			setPc(exportPc);
		} else {
			setPc(importPc);
		}
		SupplyGeneration previousGeneration = supply
				.getGenerationPrevious(this);
		if (previousGeneration == null) {
			if (((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from HhDatum datum where datum.channel.supplyGeneration.supply  = :supply and datum.endDate.date < :date")
					.setEntity("supply", this).setTimestamp("date",
							startDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are HH data before the start of the updated supply.");
			}
			if (((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from RegisterRead read where read.meter.supply  = :supply and read.presentDate.date < :date")
					.setEntity("supply", supply).setTimestamp("date",
							startDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are register reads before the start of the updated supply.");
			}
			if (((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from Bill bill where bill.supply  = :supply and bill.startDate.date < :date")
					.setEntity("supply", supply).setTimestamp("date",
							startDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are bills before the start of the updated supply.");
			}

		} else {
			boolean isOverlap = false;
			if (importMpan != null) {
				Debug.print("Import MPAN is " + importMpan.toString());
				Mpan prevImportMpan = previousGeneration.getImportMpan();
				Debug.print("Previous Import mpan " + prevImportMpan);
				if (prevImportMpan != null
						&& importMpan.getCore()
								.equals(prevImportMpan.getCore())) {
					isOverlap = true;
				}
			}
			if (!isOverlap && exportMpan != null) {
				Mpan prevExportMpan = previousGeneration.getExportMpan();
				if (prevExportMpan != null
						&& exportMpan.getCore()
								.equals(prevExportMpan.getCore())) {
					isOverlap = true;
				}
			}
			if (!isOverlap) {
				throw new UserException(
						"MPAN cores can't change without an overlapping period.");
			}
		}
		SupplyGeneration nextGeneration = supply.getGenerationNext(this);
		if (nextGeneration == null) {
			if (finishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.supplyGeneration.supply  = :supply and datum.endDate.date > :date")
							.setEntity("supply", this).setTimestamp("date",
									finishDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are HH data after " + finishDate + ", the end of the updated supply.");
			}

			if (finishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from RegisterRead read where read.meter.supply  = :supply and read.presentDate.date > :date")
							.setEntity("supply", supply).setTimestamp("date",
									finishDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are register reads after the end of the updated supply.");
			}
			if (finishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from Bill bill where bill.supply  = :supply and bill.startDate.date > :date")
							.setEntity("supply", supply).setTimestamp("date",
									finishDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are bills after the end of the updated supply.");
			}
		} else {
			boolean isOverlap = false;
			if (importMpan != null) {
				Mpan nextImportMpan = nextGeneration.getImportMpan();
				if (nextImportMpan != null
						&& importMpan.getCore()
								.equals(nextImportMpan.getCore())) {
					isOverlap = true;
				}
			}
			if (!isOverlap && exportMpan != null) {
				Mpan nextExportMpan = nextGeneration.getExportMpan();
				if (nextExportMpan != null
						&& exportMpan.getCore()
								.equals(nextExportMpan.getCore())) {
					isOverlap = true;
				}
			}
			if (!isOverlap) {
				throw new UserException(
						"MPAN cores can't change without an overlapping period.");
			}

		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (hhdcContract == null) {
			hhdcAccount = null;
			if (!channels.isEmpty()) {
				throw new UserException(
						"Can't remove the HHDC account while there are still channels there.");
			}
		} else {
			hhdcAccount = hhdcAccount == null ? null : hhdcAccount.trim();
			if (hhdcAccount == null || hhdcAccount.length() == 0) {
				throw new UserException(
						"If there's a HHDC contract, there must be an account reference.");
			}
			HhEndDate hhdcContractStartDate = hhdcContract.getStartRateScript()
					.getStartDate();
			if (hhdcContractStartDate.after(startDate)) {
				throw new UserException(
						"The HHDC contract starts after the supply generation.");
			}
			HhEndDate hhdcContractFinishDate = hhdcContract
					.getFinishRateScript().getFinishDate();
			if (HhEndDate.isBefore(hhdcContractFinishDate, finishDate)) {
				throw new UserException("The HHDC contract "
						+ hhdcContract.getId()
						+ " finishes before the supply generation.");
			}
			Criteria crit = Hiber.session().createCriteria(Bill.class).add(
					Restrictions.eq("supply", supply)).add(
					Restrictions.ge("finishDate.date", startDate.getDate()))
					.createAlias("batch", "bt").add(
							Restrictions.eq("bt.contract.id", hhdcContract
									.getId())).addOrder(
							Order.asc("startDate.date"));
			if (finishDate != null) {
				crit.add(Restrictions
						.le("startDate.date", finishDate.getDate()));
			}
			Bill firstHhdcBill = (Bill) crit.uniqueResult();
			if (firstHhdcBill == null) {
				supply.addSnag(hhdcContract, SupplySnag.MISSING_BILL,
						getStartDate(), getFinishDate());
			} else {
				if (firstHhdcBill.getStartDate().after(getStartDate())) {
					supply.addSnag(hhdcContract, SupplySnag.MISSING_BILL,
							getStartDate(), firstHhdcBill.getStartDate()
									.getPrevious());
				}
			}
		}
		Hiber.flush();
		setHhdcAccount(hhdcAccount);
		setHhdcContract(hhdcContract);
		setMeter(meter);
		for (Channel channel : channels) {
			channel.onSupplyGenerationChange();
		}

		if (importMpan != null) {
			Criteria impCrit = Hiber.session().createCriteria(Bill.class).add(
					Restrictions.eq("supply", supply)).add(
					Restrictions
							.ge("finishDate.date", getStartDate().getDate()))
					.createAlias("batch", "bt").add(
							Restrictions.eq("bt.contract.id", importMpan
									.getSupplierContract().getId())).addOrder(
							Order.asc("startDate.date"));
			if (finishDate != null) {
				impCrit.add(Restrictions.le("startDate.date", finishDate
						.getDate()));
			}
			Bill firstImpSupBill = (Bill) impCrit.uniqueResult();
			if (firstImpSupBill == null) {
				supply.addSnag(importMpan.getSupplierContract(),
						SupplySnag.MISSING_BILL, getStartDate(),
						getFinishDate());
			} else {
				if (firstImpSupBill.getStartDate().after(getStartDate())) {
					supply.addSnag(importMpan.getSupplierContract(),
							SupplySnag.MISSING_BILL, getStartDate(),
							firstImpSupBill.getStartDate().getPrevious());
				}
			}
		}
		if (exportMpan != null) {
			Criteria expCrit = Hiber.session().createCriteria(Bill.class).add(
					Restrictions.eq("supply", supply)).createAlias("batch",
					"bt").add(
					Restrictions.eq("bt.contract.id", exportMpan
							.getSupplierContract().getId())).add(
					Restrictions
							.ge("finishDate.date", getStartDate().getDate()))
					.addOrder(Order.asc("startDate.date"));
			if (finishDate != null) {
				expCrit.add(Restrictions.le("startDate.date", finishDate
						.getDate()));
			}
			Bill firstExpSupBill = (Bill) expCrit.uniqueResult();
			if (firstExpSupBill == null) {
				supply.addSnag(exportMpan.getSupplierContract(),
						SupplySnag.MISSING_BILL, getStartDate(),
						getFinishDate());
			} else {
				if (firstExpSupBill.getStartDate().after(getStartDate())) {
					supply.addSnag(exportMpan.getSupplierContract(),
							SupplySnag.MISSING_BILL, getStartDate(),
							firstExpSupBill.getStartDate().getPrevious());
				}
			}
		}
		if (previousGeneration != null) {
			previousGeneration.update(previousGeneration.getStartDate(),
					startDate.getPrevious());
		}
		if (nextGeneration != null) {
			nextGeneration.update(finishDate.getNext(), nextGeneration
					.getFinishDate());
		}
		Criteria billsCrit = Hiber.session().createCriteria(Bill.class).add(
				Restrictions.eq("supply", getSupply())).add(
				Restrictions.ge("finishDate.date", getStartDate().getDate()));
		if (getFinishDate() != null) {
			billsCrit.add(Restrictions.le("startDate.date", finishDate
					.getDate()));
		}
		for (Bill bill : (List<Bill>) billsCrit.list()) {
			bill.virtualEqualsActual();
		}
		for (Boolean isImport : new Boolean[] { true, false }) {
			for (Boolean isKwh : new Boolean[] { true, false }) {
				Channel targetChannel = getChannel(isImport, isKwh);
				Query query = Hiber
						.session()
						.createQuery(
								"from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.endDate.date >= :from"
										+ (finishDate == null ? ""
												: " and datum.endDate.date <= :to")
										+ (targetChannel == null ? ""
												: " and datum.channel != :targetChannel"))
						.setEntity("supply", supply).setBoolean("isImport",
								isImport).setBoolean("isKwh", isKwh)
						.setTimestamp("from", startDate.getDate());
				if (finishDate != null) {
					query.setTimestamp("to", finishDate.getDate());
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
										+ startDate + ", finishing "
										+ finishDate + ".");
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
					targetChannel.deleteSnag(ChannelSnag.SNAG_MISSING, endDate,
							endDate);
					Hiber.flush();
					Hiber.session().evict(datum);
				}
				hhData.close();
			}
		}
		for (Mpan mpan : mpans) {
			SupplierContract supplierContract = mpan.getSupplierContract();
			if (supplierContract.getStartRateScript().getStartDate().after(
					startDate)) {
				throw new UserException(
						"The supplier contract starts after the supply generation.");
			}
			if (HhEndDate.isBefore(supplierContract.getFinishRateScript()
					.getFinishDate(), finishDate)) {
				throw new UserException(
						"The supplier contract finishes before the supply generation.");
			}
		}
		// check doesn't have superfluous meters
		List<Meter> metersToRemove = new ArrayList<Meter>();
		for (Meter meterToCheck : supply.getMeters()) {
			if ((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from SupplyGeneration generation where generation.meter = :meter")
					.setEntity("meter", meterToCheck).uniqueResult() == 0) {
				metersToRemove.add(meterToCheck);
			}
		}
		for (Meter meterToRemove : metersToRemove) {
			supply.getMeters().remove(meterToRemove);
		}
		Hiber.flush();
	}

	public int compareTo(Object obj) {
		return getFinishDate().getDate().compareTo(
				((SupplyGeneration) obj).getFinishDate().getDate());
	}

	public void deleteMpan(Mpan mpan) throws HttpException {
		if (mpans.size() < 2) {
			throw new UserException(
					"There must be at least one MPAN generation in each supply generation.");
		}
		mpans.remove(mpan);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supply-generation");
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		if (hhdcAccount != null) {
			element.setAttribute("hhdc-account", hhdcAccount);
		}
		return element;
	}

	public Channel insertChannel(boolean isImport, boolean isKwh)
			throws HttpException {
		if (hhdcAccount == null) {
			throw new UserException(
					"Can't add a channel if there's no HHDC account.");
		}
		Channel channel = new Channel(this, isImport, isKwh);
		try {
			Hiber.session().save(channel);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException("There's already a channel with import: "
					+ isImport + " and kWh: " + isKwh + ".");
		}
		channels.add(channel);
		channel.addSnag(ChannelSnag.SNAG_MISSING, getStartDate(),
				getFinishDate());
		return channel;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element generationElement = (Element) toXml(doc, new XmlTree(
				"siteSupplyGenerations", new XmlTree("site")).put("pc").put(
				"meter").put("supply", new XmlTree("source").put("gspGroup"))
				.put("hhdcContract", new XmlTree("party")));
		source.appendChild(generationElement);
		for (Mpan mpan : mpans) {
			Element mpanElement = (Element) mpan.toXml(doc, new XmlTree("core")
					.put("mtc").put("llfc").put("ssc").put("supplierContract",
							new XmlTree("party")));
			generationElement.appendChild(mpanElement);
			/*
			 * for (RegisterRead read : (List<RegisterRead>) Hiber.session()
			 * .createQuery( "from RegisterRead read where read.mpan = :mpan")
			 * .setEntity("mpan", mpan).list()) {
			 * mpanElement.appendChild(read.toXml(doc, new XmlTree("invoice",
			 * new XmlTree("batch", new XmlTree("contract", new
			 * XmlTree("party")))))); }
			 */
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (Pc pc : (List<Pc>) Hiber.session().createQuery(
				"from Pc pc order by pc.code").list()) {
			source.appendChild(pc.toXml(doc));
		}
		for (GspGroup group : (List<GspGroup>) Hiber.session().createQuery(
				"from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}
		for (HhdcContract contract : (List<HhdcContract>) Hiber.session()
				.createQuery(
						"from HhdcContract contract order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		for (SupplierContract contract : (List<SupplierContract>) Hiber
				.session()
				.createQuery(
						"from SupplierContract contract order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws HttpException {
		Document doc = document();
		try {
			if (inv.hasParameter("delete")) {
				supply.deleteGeneration(this);
				Hiber.commit();
				inv.sendSeeOther(new SupplyGenerations(supply).getUri());
			} else if (inv.hasParameter("attach")) {
				String siteCode = inv.getString("site-code");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				Site site = Site.getSite(siteCode);
				attachSite(site);
				Hiber.commit();
				inv.sendOk(document());
			} else if (inv.hasParameter("detach")) {
				Long siteId = inv.getLong("site-id");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				Site site = Site.getSite(siteId);
				detachSite(site);
				Hiber.commit();
				inv.sendOk(document());
			} else if (inv.hasParameter("set-location")) {
				Long siteId = inv.getLong("site-id");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				Site site = Site.getSite(siteId);
				setPhysicalLocation(site);
				Hiber.commit();
				inv.sendOk(document());
			} else {
				Date startDate = inv.getDate("start-date");
				Long hhdcContractId = inv.getLong("hhdc-contract-id");
				String meterSerialNumber = inv.getString("meter-serial-number");
				Long pcId = inv.getLong("pc-id");
				if (!inv.isValid()) {
					throw new UserException();
				}
				Date finishDate = null;
				String importMpanStr = null;
				Ssc importSsc = null;
				Integer importAgreedSupplyCapacity = null;
				HhdcContract hhdcContract = null;
				SupplierContract importSupplierContract = null;
				String importSupplierAccountReference = null;
				boolean isEnded = inv.getBoolean("is-ended");
				if (isEnded) {
					finishDate = inv.getDate("finish-date");
				}
				String hhdcAccountReference = null;
				if (hhdcContractId != null) {
					hhdcContract = HhdcContract.getHhdcContract(hhdcContractId);
					hhdcAccountReference = inv
							.getString("hhdc-account-reference");
				}
				Pc pc = Pc.getPc(pcId);
				boolean hasImportMpan = inv.getBoolean("has-import-mpan");

				if (hasImportMpan) {
					String importMpanCoreStr = inv
							.getString("import-mpan-core");
					String importLlfcCodeStr = inv
							.getString("import-llfc-code");
					String importMtcCode = inv.getString("import-mtc-code");
					String importSscCode = inv.getString("import-ssc-code");

					if (!inv.isValid()) {
						throw new UserException(document());
					}
					if (importSscCode.trim().length() > 0) {
						importSsc = Ssc.getSsc(importSscCode);
					}

					importMpanStr = pc.codeAsString() + importMtcCode
							+ importLlfcCodeStr + importMpanCoreStr;
					importAgreedSupplyCapacity = inv
							.getInteger("import-agreed-supply-capacity");

					if (!inv.isValid()) {
						throw new UserException();
					}
					Long importSupplierContractId = inv
							.getLong("import-supplier-contract-id");
					importSupplierContract = SupplierContract
							.getSupplierContract(importSupplierContractId);
					importSupplierAccountReference = inv
							.getString("import-supplier-account-reference");
				}
				String exportMpanStr = null;
				Ssc exportSsc = null;
				Integer exportAgreedSupplyCapacity = null;
				String exportSupplierAccountReference = null;
				SupplierContract exportSupplierContract = null;
				boolean hasExportMpan = inv.getBoolean("has-export-mpan");
				if (hasExportMpan) {
					String exportMpanCoreStr = inv
							.getString("export-mpan-core");
					String llfcCodeStr = inv.getString("export-llfc-code");
					String exportMtcCode = inv.getString("export-mtc-code");
					String exportSscCode = inv.getString("export-ssc-code");
					if (!inv.isValid()) {
						throw new UserException();
					}
					if (exportSscCode.trim().length() > 0) {
						exportSsc = Ssc.getSsc(exportSscCode);
					}
					exportMpanStr = pc.codeAsString() + exportMtcCode
							+ llfcCodeStr + exportMpanCoreStr;
					exportAgreedSupplyCapacity = inv
							.getInteger("export-agreed-supply-capacity");
					if (!inv.isValid()) {
						throw new UserException();
					}
					Long exportSupplierContractId = inv
							.getLong("export-supplier-contract-id");
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractId);
					exportSupplierAccountReference = inv
							.getString("export-supplier-account-reference");
				}
				Meter meter = null;
				if (meterSerialNumber != null
						&& meterSerialNumber.length() != 0) {
					meter = supply.findMeter(meterSerialNumber);
					if (meter == null) {
						meter = supply.insertMeter(meterSerialNumber);
					}
				}
				update(new HhEndDate(startDate).getNext(),
						finishDate == null ? null : new HhEndDate(finishDate),
						hhdcContract, hhdcAccountReference, meter,
						importMpanStr, importSsc, importSupplierContract,
						importSupplierAccountReference,
						importAgreedSupplyCapacity, exportMpanStr, exportSsc,
						exportSupplierContract, exportSupplierAccountReference,
						exportAgreedSupplyCapacity);
				Hiber.commit();
				inv.sendOk(document());
			}
		} catch (HttpException e) {
			e.setDocument(doc);
			throw e;
		}
	}

	public MonadUri getUri() throws HttpException {
		return supply.getSupplyGenerationsInstance().getUri().resolve(
				getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Channels.URI_ID.equals(uriId)) {
			return new Channels(this);
		} else {
			throw new NotFoundException();
		}
	}

	public String toString() {
		return "SupplyGeneration id " + getId();
	}

	public void setPhysicalLocation(Site site) throws HttpException {
		SiteSupplyGeneration targetSiteSupply = null;
		for (SiteSupplyGeneration siteSupply : siteSupplyGenerations) {
			if (site.equals(siteSupply.getSite())) {
				targetSiteSupply = siteSupply;
			}
		}
		if (targetSiteSupply == null) {
			throw new UserException("The site isn't attached to this supply.");
		}
		for (SiteSupplyGeneration siteSupply : siteSupplyGenerations) {
			siteSupply.setIsPhysical(siteSupply.equals(targetSiteSupply));
		}
		Hiber.flush();
	}

	public Channels getChannelsInstance() {
		return new Channels(this);
	}

	@SuppressWarnings("unchecked")
	public void deleteChannel(boolean isImport, boolean isKwh)
			throws HttpException {
		Channel channel = getChannel(isImport, isKwh);
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from HhDatum datum where datum.channel = :channel")
				.setEntity("channel", channel).uniqueResult() > 0) {
			throw new UserException(
					"One can't delete a channel if there are still HH data attached to it.");
		}
		// delete any concommitant snags
		for (ChannelSnag snag : (List<ChannelSnag>) Hiber.session()
				.createQuery(
						"from ChannelSnag snag where snag.channel = :channel")
				.setEntity("channel", channel).list()) {
			ChannelSnag.deleteChannelSnag(snag);
		}
		channels.remove(channel);
		Hiber.session().flush();
	}
}
