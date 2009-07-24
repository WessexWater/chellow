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
import net.sf.chellow.billing.Dso;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
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
			String pcCode = GeneralImport.addField(csvElement, "Profile Class",
					values, 5);
			Pc pc = null;
			if (pcCode.equals(GeneralImport.NO_CHANGE)) {
				pc = supplyGeneration.getPc();
			} else {
				pc = Pc.getPc(pcCode);
			}
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has import kWh?", values, 9);
			boolean hasImportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(true, true) != null : Boolean
					.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has import kVArh?", values, 10);
			boolean hasImportKvarh = hasImportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(true, false) != null : Boolean
					.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has export kWh?", values, 11);
			boolean hasExportKwh = hasExportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(false, true) != null : Boolean
					.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has export kVArh?", values, 12);
			boolean hasExportKvarh = hasExportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(false, false) != null : Boolean
					.parseBoolean(hasExportKvarhStr);
			HhdcContract hhdcContract = null;
			Account hhdcAccount = null;
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 13);
			if (hhdcContractName.equals(GeneralImport.NO_CHANGE)) {
				Account account = supplyGeneration.getHhdcAccount();
				if (account == null) {
					throw new UserException(
							"There isn't an existing HHDC contract");
				}
				hhdcContract = HhdcContract.getHhdcContract(account
						.getContract().getId());
			} else if (hhdcContractName.length() > 0) {
				hhdcContract = HhdcContract.getHhdcContract(hhdcContractName);
			}
			String hhdcAccountReference = GeneralImport.addField(csvElement,
					"HHDC account reference", values, 14);
			if (hhdcAccountReference.equals(GeneralImport.NO_CHANGE)) {
				hhdcAccount = supplyGeneration.getHhdcAccount();
				if (hhdcAccount == null) {
					throw new UserException(
							"There isn't an existing HHDC account");
				}
			} else if (hhdcAccountReference.length() > 0) {
				hhdcAccount = hhdcContract.getAccount(hhdcAccountReference);
			}
			supplyGeneration.update(startDateStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getStartDate() : new HhEndDate("start", startDateStr),
					finishDateStr.length() == 0 ? null : (finishDateStr
							.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
							.getFinishDate() : new HhEndDate("finish",
							finishDateStr)), hhdcAccount, meter, pc);
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
					"Import MPAN", values, 5);

			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values, 6);
			Ssc importSsc = null;
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values, 8);
			Integer importAgreedSupplyCapacity = null;
			Mpan existingImportMpan = supplyGeneration.getImportMpan();
			SupplierContract importSupplierContract = null;
			Account importSupplierAccount = null;
			if (importMpanStr.equals(GeneralImport.NO_CHANGE)) {
				importMpanStr = existingImportMpan == null ? null
						: existingImportMpan.toString();
			} else if (importMpanStr.trim().length() == 0) {
				importMpanStr = null;
			}
			if (importMpanStr != null) {
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
				String importContractSupplierName = GeneralImport.addField(
						csvElement, "Import Supplier Contract", values, 15);
				if (importContractSupplierName.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import supplier.");
					}
					Account account = existingImportMpan.getSupplierAccount();
					if (account == null) {
						throw new UserException(
								"There isn't an existing import supplier.");
					}
					importSupplierContract = SupplierContract
							.getSupplierContract(account.getContract().getId());
				} else {
					importSupplierContract = SupplierContract
							.getSupplierContract(importContractSupplierName);
				}
				String importSupplierAccountReference = GeneralImport.addField(
						csvElement, "Import Supplier Account Reference",
						values, 16);
				if (importSupplierAccountReference
						.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import supplier account.");
					}
					Account account = existingImportMpan.getSupplierAccount();
					if (account == null) {
						throw new UserException(
								"There isn't an existing import supplier account.");
					}
					importSupplierAccount = account;
				} else {
					importSupplierAccount = importSupplierContract
							.getAccount(importSupplierAccountReference);
				}
			}
			String exportMpanStr = GeneralImport.addField(csvElement,
					"Eport MPAN", values, 17);
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
			Account exportAccountSupplier = null;
			if (exportMpanStr != null) {
				String exportSscCode = GeneralImport.addField(csvElement,
						"Export SSC", values, 18);
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
								values, 20);
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
				String exportContractSupplierName = GeneralImport.addField(
						csvElement, "Export Supplier Contract", values, 27);
				if (exportContractSupplierName.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export supplier contract.");
					}
					Account account = existingExportMpan.getSupplierAccount();
					if (account == null) {
						throw new UserException(
								"There isn't an existing export supplier contract.");
					}
					exportSupplierContract = SupplierContract
							.getSupplierContract(account.getContract().getId());
				} else {
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportContractSupplierName);
				}
				String exportSupplierAccountReference = GeneralImport.addField(
						csvElement, "Export Supplier Account", values, 28);
				if (exportSupplierAccountReference
						.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export supplier.");
					}
					exportAccountSupplier = existingExportMpan
							.getSupplierAccount();
				} else {
					exportAccountSupplier = exportSupplierContract
							.getAccount(exportSupplierAccountReference);
				}
			}
			supplyGeneration.addOrUpdateMpans(importMpanStr, importSsc,
					importSupplierAccount, importAgreedSupplyCapacity,
					exportMpanStr, exportSsc, exportAccountSupplier,
					exportAgreedSupplyCapacity);
		} else if (action.equals("insert")) {
			String siteCode = GeneralImport.addField(csvElement, "Site Code",
					values, 0);
			Site site = Site.getSite(siteCode);
			Supply supply = null;
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 1);
			HhEndDate startDate = startDateStr.length() == 0 ? null
					: new HhEndDate(startDateStr);
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has import kWh", values, 7);
			boolean hasImportKwh = Boolean.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has import kVArh", values, 8);
			boolean hasImportKvarh = Boolean.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has export kWh", values, 9);
			Boolean hasExportKwh = Boolean.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has export kVArh", values, 10);
			Boolean hasExportKvarh = Boolean.parseBoolean(hasExportKvarhStr);
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 11);
			HhdcContract hhdcContract = null;
			Account hhdcAccount = null;
			if (hhdcContractName.length() > 0) {
				hhdcContract = HhdcContract.getHhdcContract(hhdcContractName);
				String hhdcAccountReference = GeneralImport.addField(
						csvElement, "HHDC account reference", values, 12);
				hhdcAccount = hhdcContract.getAccount(hhdcAccountReference);
			}
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 2);
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values, 3);
			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values, 4);
			Ssc importSsc = null;
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values, 6);
			Integer importAgreedSupplyCapacity = null;
			String importContractSupplierName = GeneralImport.addField(
					csvElement, "Import Supplier Contract", values, 13);
			String importSupplierAccountReference = GeneralImport
					.addField(csvElement, "Import Supplier Account Reference",
							values, 14);
			SupplierContract importSupplierContract = null;
			Account importSupplierAccount = null;
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
				importSupplierAccount = importSupplierContract
						.getAccount(importSupplierAccountReference);
			}
			String exportMpanStr = GeneralImport.addField(csvElement,
					"Eport MPAN", values, 15);
			Integer exportAgreedSupplyCapacity = null;
			Ssc exportSsc = null;
			SupplierContract exportSupplierContract = null;
			Account exportSupplierAccount = null;

			if (exportMpanStr.length() > 0) {
				String exportSscCode = GeneralImport.addField(csvElement,
						"Export SSC", values, 16);
				String exportAgreedSupplyCapacityStr = GeneralImport
						.addField(csvElement, "Export Agreed Supply Capacity",
								values, 18);
				String exportContractSupplierName = GeneralImport.addField(
						csvElement, "Export Supplier Contract", values, 25);
				String exportSupplierAccountReference = GeneralImport.addField(
						csvElement, "Export Supplier Account", values, 26);
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
				exportSupplierAccount = exportSupplierContract
						.getAccount(exportSupplierAccountReference);
			}
			Map<Site, Boolean> siteMap = new HashMap<Site, Boolean>();
			siteMap.put(site, true);
			SupplyGeneration generation = supply.insertGeneration(siteMap,
					startDate, hhdcAccount, meterSerialNumber, importMpanStr,
					importSsc, importSupplierAccount,
					importAgreedSupplyCapacity, exportMpanStr, exportSsc,
					exportSupplierAccount, exportAgreedSupplyCapacity);
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
	private Account mopAccount;
	private Meter meter;

	private Account hhdcAccount;
	private Pc pc;
	private Mpan importMpan;

	private Mpan exportMpan;

	private Set<Mpan> mpans;
	private Set<Channel> channels;

	SupplyGeneration() {
	}

	SupplyGeneration(Supply supply, HhEndDate startDate, HhEndDate finishDate,
			Account hhdcAccount, Meter meter) throws HttpException {
		setChannels(new HashSet<Channel>());
		setSupply(supply);
		setSiteSupplyGenerations(new HashSet<SiteSupplyGeneration>());
		setMpans(new HashSet<Mpan>());
		internalUpdate(startDate, finishDate, hhdcAccount, meter, Pc
				.getPc("00"));
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

	public Account getMopAccount() {
		return mopAccount;
	}

	void setMopAccount(Account mopAccount) {
		this.mopAccount = mopAccount;
	}

	public Account getHhdcAccount() {
		return hhdcAccount;
	}

	void setHhdcAccount(Account hhdcAccount) {
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

	public void addOrUpdateMpans(String importMpanStr, Ssc importSsc,
			Account importSupplierAccount, Integer importAgreedSupplyCapacity,
			String exportMpanStr, Ssc exportSsc, Account exportSupplierAccount,
			Integer exportAgreedSupplyCapacity) throws HttpException {
		Pc importPc = null;
		Pc exportPc = null;
		if (importMpan == null) {
			if (importMpanStr != null && importMpanStr.length() != 0) {
				setImportMpan(new Mpan(this, importMpanStr, importSsc,
						importSupplierAccount, importAgreedSupplyCapacity));
				mpans.add(getImportMpan());
			}
		} else {
			if (importMpanStr == null || importMpanStr.length() == 0) {
				mpans.remove(importMpan);
				setImportMpan(null);
			} else {
				importMpan.update(importMpanStr, importSsc,
						importSupplierAccount, importAgreedSupplyCapacity);
			}
		}
		if (exportMpan == null) {
			if (exportMpanStr != null && exportMpanStr.length() != 0) {
				setExportMpan(new Mpan(this, exportMpanStr, exportSsc,
						exportSupplierAccount, exportAgreedSupplyCapacity));
				mpans.add(getExportMpan());
			}
		} else {
			if (exportMpanStr == null || exportMpanStr.length() == 0) {
				mpans.remove(exportMpan);
				setExportMpan(null);
			} else {
				exportMpan.update(exportMpanStr, exportSsc,
						exportSupplierAccount, exportAgreedSupplyCapacity);
			}
		}
		if (importMpan == null && exportMpan == null) {
			throw new UserException(document(),
					"A supply generation must have at least one MPAN.");
		}
		SupplyGeneration previousGeneration = supply
				.getGenerationPrevious(this);
		if (previousGeneration != null) {
			boolean isOverlap = false;
			if (importMpan != null) {
				Mpan prevImportMpan = previousGeneration.getImportMpan();
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
		if (dso != null && dso.getCode().equals("22")) {
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
		Hiber.flush();
		// more optimization possible here, doesn't necessarily need to check
		// data.
		// Debug.print("starting onsupgen change. 99");
		Hiber.flush();
		checkMpanRelationship();
		// Debug.print("checked relationsip.");
		// checkForMissing(getStartDate(), getFinishDate());
		// Debug.print("finished add or update.");
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

	public void internalUpdate(HhEndDate startDate, HhEndDate finishDate,
			Account hhdcAccount, Meter meter, Pc pc) throws HttpException {
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new UserException(
					"The generation start date can't be after the finish date.");
		}
		if (startDate == null) {
			throw new InternalException("start date can't be null.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (hhdcAccount == null && !channels.isEmpty()) {
			throw new UserException(
					"Can't remove the HHDC account while there are still channels there.");
		}
		setHhdcAccount(hhdcAccount);
		setMeter(meter);
		setPc(pc);
		// resolve any snags channel snags outside range
		for (Channel channel : channels) {
			channel.onSupplyGenerationChange();
		}
	}

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
	}

	private void checkMpanRelationship() throws HttpException {
		if (hhdcAccount != null) {
			HhdcContract hhdcContract = HhdcContract
					.getHhdcContract(hhdcAccount.getContract().getId());
			HhEndDate hhdcContractStartDate = hhdcContract.getStartRateScript()
					.getStartDate();
			if (hhdcContractStartDate.getDate().after(getStartDate().getDate())) {
				throw new UserException(
						"The HHDC contract starts after the supply generation.");
			}
			HhEndDate hhdcContractFinishDate = hhdcContract
					.getFinishRateScript().getFinishDate();
			if (hhdcContractFinishDate != null
					&& (finishDate == null || hhdcContractFinishDate.getDate()
							.before(getStartDate().getDate()))) {
				throw new UserException("The HHDC contract "
						+ hhdcContract.getId()
						+ " finishes before the supply generation.");
			}
		}
		for (Mpan mpan : mpans) {
			SupplierContract supplierContract = SupplierContract
					.getSupplierContract(mpan.getSupplierAccount()
							.getContract().getId());
			HhEndDate supplierContractStartDate = supplierContract
					.getStartRateScript().getStartDate();
			if (supplierContractStartDate.getDate().after(
					getStartDate().getDate())) {
				throw new UserException(
						"The supplier contract starts after the supply generation.");
			}
			HhEndDate supplierContractFinishDate = supplierContract
					.getFinishRateScript().getFinishDate();
			if (finishDate == null
					&& supplierContractFinishDate != null
					|| supplierContractFinishDate != null
					&& finishDate != null
					&& supplierContractFinishDate.getDate().before(
							getStartDate().getDate())) {
				throw new UserException(
						"The supplier contract finishes before the supply generation.");
			}
		}
	}

	public void update(HhEndDate startDate, HhEndDate finishDate,
			Account hhdcAccount, Meter meter, Pc pc) throws HttpException {
		HhEndDate originalStartDate = getStartDate();
		HhEndDate originalFinishDate = getFinishDate();
		if (startDate.equals(originalStartDate)
				&& ((finishDate != null && originalFinishDate != null && finishDate
						.equals(originalFinishDate)) || (finishDate == null && originalFinishDate == null))) {
			return;
		}
		SupplyGeneration previousSupplyGeneration = supply
				.getGenerationPrevious(this);
		if (previousSupplyGeneration != null) {
			if (!previousSupplyGeneration.getStartDate().getDate().before(
					startDate.getDate())) {
				throw new UserException(
						"The start date must be after the start date of the previous generation.");
			}
			previousSupplyGeneration.internalUpdate(previousSupplyGeneration
					.getStartDate(), startDate.getPrevious(),
					previousSupplyGeneration.getHhdcAccount(),
					previousSupplyGeneration.getMeter(),
					previousSupplyGeneration.getPc());
		}
		SupplyGeneration nextSupplyGeneration = supply.getGenerationNext(this);
		if (nextSupplyGeneration != null) {
			if (finishDate == null) {
				throw new UserException(
						"The finish date must be before the finish date of the next generation.");
			}
			if (nextSupplyGeneration.getFinishDate() != null
					&& !finishDate.getDate().before(
							nextSupplyGeneration.getFinishDate().getDate())) {
				throw new UserException(
						"The finish date must be before the finish date of the next generation.");
			}
			nextSupplyGeneration.internalUpdate(finishDate.getNext(),
					nextSupplyGeneration.getFinishDate(), nextSupplyGeneration
							.getHhdcAccount(), nextSupplyGeneration.getMeter(),
					nextSupplyGeneration.getPc());
		}
		internalUpdate(startDate, finishDate, hhdcAccount, meter, pc);
		Hiber.flush();
		checkMpanRelationship();
		HhEndDate checkFinishDate = originalStartDate;
		if (originalFinishDate != null && finishDate != null) {
			if (!originalFinishDate.getDate().equals(finishDate)) {
				checkFinishDate = finishDate.getDate().after(
						originalFinishDate.getDate()) ? finishDate
						: originalFinishDate;
			}
		} else if (originalFinishDate == null || finishDate == null) {
			checkFinishDate = null;
		}
		supply.onSupplyGenerationChange(startDate.getDate().before(
				originalStartDate.getDate()) ? startDate : originalStartDate,
				checkFinishDate);
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
				.put("hhdcAccount",
						new XmlTree("contract", new XmlTree("party"))));
		source.appendChild(generationElement);
		for (Mpan mpan : mpans) {
			Element mpanElement = (Element) mpan.toXml(doc, new XmlTree("core")
					.put("mtc").put("llfc").put("ssc").put("supplierAccount",
							new XmlTree("contract", new XmlTree("party"))));
			generationElement.appendChild(mpanElement);
			for (RegisterRead read : (List<RegisterRead>) Hiber.session()
					.createQuery(
							"from RegisterRead read where read.mpan = :mpan")
					.setEntity("mpan", mpan).list()) {
				mpanElement.appendChild(read.toXml(doc, new XmlTree("invoice",
						new XmlTree("batch", new XmlTree("contract",
								new XmlTree("party"))))));
			}
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (Pc pc : (List<Pc>) Hiber.session().createQuery(
				"from Pc pc order by pc.code").list()) {
			source.appendChild(pc.toXml(doc));
		}
		return doc;
	}

	void deleteMpans() throws HttpException {
		for (Mpan mpan : mpans) {
			mpan.delete();
		}
		mpans.clear();
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
				String hhdcContractName = inv.getString("hhdc-contract-name");
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
				Account hhdcAccount = null;
				SupplierContract importSupplierContract = null;
				Account importSupplierAccount = null;
				boolean isEnded = inv.getBoolean("is-ended");
				if (isEnded) {
					finishDate = inv.getDate("finish-date");
				}
				hhdcContractName = hhdcContractName.trim();
				if (hhdcContractName.length() != 0) {
					hhdcContract = HhdcContract
							.getHhdcContract(hhdcContractName);
					String hhdcAccountReference = inv
							.getString("hhdc-account-reference");
					hhdcAccount = hhdcContract.getAccount(hhdcAccountReference
							.trim());
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

					importMpanStr = getPc().codeAsString() + importMtcCode
							+ importLlfcCodeStr + importMpanCoreStr;
					importAgreedSupplyCapacity = inv
							.getInteger("import-agreed-supply-capacity");

					if (!inv.isValid()) {
						throw new UserException();
					}
					String importSupplierContractName = inv
							.getString("import-supplier-contract-name");
					importSupplierContract = SupplierContract
							.getSupplierContract(importSupplierContractName
									.trim());
					String importSupplierAccountReference = inv
							.getString("import-supplier-account-reference");
					importSupplierAccount = importSupplierContract
							.getAccount(importSupplierAccountReference.trim());
				}
				String exportMpanStr = null;
				Ssc exportSsc = null;
				Integer exportAgreedSupplyCapacity = null;
				Account exportSupplierAccount = null;
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
					exportMpanStr = getPc().codeAsString() + exportMtcCode
							+ llfcCodeStr + exportMpanCoreStr;
					exportAgreedSupplyCapacity = inv
							.getInteger("export-agreed-supply-capacity");
					if (!inv.isValid()) {
						throw new UserException();
					}
					String exportSupplierContractName = inv
							.getString("export-supplier-contract-name");
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractName
									.trim());
					String exportSupplierAccountReference = inv
							.getString("export-supplier-account-reference");
					exportSupplierAccount = exportSupplierContract
							.getAccount(exportSupplierAccountReference.trim());
				}
				addOrUpdateMpans(importMpanStr, importSsc,
						importSupplierAccount, importAgreedSupplyCapacity,
						exportMpanStr, exportSsc, exportSupplierAccount,
						exportAgreedSupplyCapacity);
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
						hhdcAccount, meter, pc);
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
	/*
	 * public void checkForMissing(HhEndDate from, HhEndDate to) throws
	 * HttpException { for (Channel channel : channels) {
	 * channel.checkForMissing(from, to); } }
	 * 
	 * public void checkForMissingFromLatest(HhEndDate to) throws HttpException
	 * { for (Channel channel : channels) {
	 * channel.checkForMissingFromLatest(to); } }
	 */
}
