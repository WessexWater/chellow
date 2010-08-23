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
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
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

import org.hibernate.Query;
import org.hibernate.ScrollableResults;
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
					.length() == 0 ? null : new HhStartDate(dateStr));
			if (supplyGeneration == null) {
				throw new UserException(
						"There isn't a generation at this date.");
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 2);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values, 3);
			MopContract mopContract = null;
			String mopContractName = GeneralImport.addField(csvElement,
					"MOP Contract", values, 4);
			if (mopContractName.equals(GeneralImport.NO_CHANGE)) {
				mopContract = supplyGeneration.getMopContract();
			} else if (mopContractName.length() > 0) {
				mopContract = MopContract.getMopContract(mopContractName);
			}
			String mopAccount = GeneralImport.addField(csvElement,
					"MOP Account", values, 5);
			if (mopAccount.equals(GeneralImport.NO_CHANGE)) {
				mopAccount = supplyGeneration.getMopAccount();
			}
			HhdcContract hhdcContract = null;
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 6);
			if (hhdcContractName.equals(GeneralImport.NO_CHANGE)) {
				hhdcContract = supplyGeneration.getHhdcContract();
			} else if (hhdcContractName.length() > 0) {
				hhdcContract = HhdcContract.getHhdcContract(hhdcContractName);
			}
			String hhdcAccount = GeneralImport.addField(csvElement,
					"HHDC account", values, 7);
			if (hhdcAccount.equals(GeneralImport.NO_CHANGE)) {
				hhdcAccount = supplyGeneration.getHhdcAccount();
			}
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh?", values, 8);
			boolean hasImportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(true, true) != null : Boolean
					.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh?", values, 9);
			boolean hasImportKvarh = hasImportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(true, false) != null : Boolean
					.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh?", values, 10);
			boolean hasExportKwh = hasExportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getChannel(false, true) != null : Boolean
					.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh?", values, 11);
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
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 12);
			if (meterSerialNumber.equals(GeneralImport.NO_CHANGE)) {
				meterSerialNumber = supplyGeneration.getMeterSerialNumber();
			}
			String pcCode = GeneralImport.addField(csvElement, "Profile Class",
					values, 13);
			Pc pc = null;
			if (pcCode.equals(GeneralImport.NO_CHANGE)) {
				pc = supplyGeneration.getPc();
			} else {
				pc = Pc.getPc(pcCode);
			}

			String mtcCode = GeneralImport.addField(csvElement,
					"Meter Timeswitch Class", values, 14);
			if (mtcCode.equals(GeneralImport.NO_CHANGE)) {
				mtcCode = supplyGeneration.getMtc().toString();
			}

			String copCode = GeneralImport.addField(csvElement, "CoP", values,
					15);
			Cop cop = null;
			if (pcCode.equals(GeneralImport.NO_CHANGE)) {
				cop = supplyGeneration.getCop();
			} else {
				cop = Cop.getCop(copCode);
			}

			Ssc ssc = null;
			String sscCode = GeneralImport.addField(csvElement, "SSC", values,
					16);
			if (sscCode.equals(GeneralImport.NO_CHANGE)) {
				ssc = supplyGeneration.getSsc();
			} else {
				ssc = sscCode.length() == 0 ? null : Ssc.getSsc(sscCode);
			}

			String importMpanCoreStr = GeneralImport.addField(csvElement,
					"Import MPAN Core", values, 17);
			String importLlfcCode = GeneralImport.addField(csvElement,
					"Import LLFC", values, 18);
			Integer importAgreedSupplyCapacity = null;
			SupplierContract importSupplierContract = null;
			String importSupplierAccount = null;
			Mpan existingImportMpan = supplyGeneration.getImportMpan();
			if (importMpanCoreStr.equals(GeneralImport.NO_CHANGE)) {
				importMpanCoreStr = existingImportMpan == null ? null
						: existingImportMpan.getCore().toString();
			} else if (importMpanCoreStr.length() == 0) {
				importMpanCoreStr = null;
			}
			if (importMpanCoreStr != null) {
				importLlfcCode = GeneralImport.addField(csvElement,
						"Import LLFC", values, 19);
				if (importLlfcCode.equals(GeneralImport.NO_CHANGE)) {
					importLlfcCode = existingImportMpan == null ? null
							: existingImportMpan.getLlfc().toString();
				}
				String importAgreedSupplyCapacityStr = GeneralImport
						.addField(csvElement, "Import Agreed Supply Capacity",
								values, 20);
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
						csvElement, "Import Supplier Contract", values, 21);
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
						"Import Supplier Account", values, 22);
				if (importSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import supplier account.");
					}
					importSupplierAccount = existingImportMpan
							.getSupplierAccount();
				}
			}
			String exportMpanCoreStr = null;
			String exportLlfcCode = null;
			SupplierContract exportSupplierContract = null;
			String exportSupplierAccount = null;
			Integer exportAgreedSupplyCapacity = null;
			if (values.length > 23) {
				exportMpanCoreStr = GeneralImport.addField(csvElement,
						"Eport MPAN Core", values, 23);
				Mpan existingExportMpan = supplyGeneration.getExportMpan();
				if (exportMpanCoreStr.equals(GeneralImport.NO_CHANGE)) {
					exportMpanCoreStr = existingExportMpan == null ? null
							: existingExportMpan.getCore().toString();
				} else if (exportMpanCoreStr.length() == 0) {
					exportMpanCoreStr = null;
				}
				if (exportMpanCoreStr != null) {
					exportLlfcCode = GeneralImport.addField(csvElement,
							"Export LLFC", values, 24);
					if (exportLlfcCode.equals(GeneralImport.NO_CHANGE)) {
						exportLlfcCode = existingExportMpan == null ? null
								: existingExportMpan.getLlfc().toString();
					}
					String exportAgreedSupplyCapacityStr = GeneralImport
							.addField(csvElement,
									"Export Agreed Supply Capacity", values, 25);
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
							csvElement, "Export Supplier Contract", values, 26);
					if (exportSupplierContractName
							.equals(GeneralImport.NO_CHANGE)) {
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
							"Export Supplier Account", values, 27);
					if (exportSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan == null) {
							throw new UserException(
									"There isn't an existing export MPAN.");
						}
						exportSupplierAccount = existingExportMpan
								.getSupplierAccount();
					}
				}
			}
			supply.updateGeneration(supplyGeneration, startDateStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getStartDate() : new HhStartDate("start", startDateStr),
					finishDateStr.length() == 0 ? null : (finishDateStr
							.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
							.getFinishDate() : new HhStartDate("finish",
							finishDateStr)), mopContract, mopAccount,
					hhdcContract, hhdcAccount, meterSerialNumber, pc, mtcCode,
					cop, ssc, importMpanCoreStr, importLlfcCode,
					importSupplierContract, importSupplierAccount,
					importAgreedSupplyCapacity, exportMpanCoreStr,
					exportLlfcCode, exportSupplierContract,
					exportSupplierAccount, exportAgreedSupplyCapacity);
		} else if (action.equals("delete")) {
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values, 0);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			Supply supply = mpanCore.getSupply();
			String dateStr = GeneralImport.addField(csvElement, "Date", values,
					1);

			SupplyGeneration supplyGeneration = supply.getGeneration(dateStr
					.length() == 0 ? null : new HhStartDate(dateStr));
			if (supplyGeneration == null) {
				throw new UserException(
						"There isn't a generation at this date.");
			}
			supply.deleteGeneration(supplyGeneration);
		} else if (action.equals("insert")) {
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values, 0);
			Supply supply = MpanCore.getMpanCore(mpanCoreStr).getSupply();
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 1);
			HhStartDate startDate = startDateStr.length() == 0 ? null
					: new HhStartDate(startDateStr);
			SupplyGeneration existingGeneration = supply
					.getGeneration(startDate);
			if (existingGeneration == null) {
				throw new UserException(
						"The start date isn't within the supply.");
			}

			String siteCode = GeneralImport.addField(csvElement, "Site Code",
					values, 2);
			Site site = null;
			if (!siteCode.equals(GeneralImport.NO_CHANGE)) {
				site = Site.getSite(siteCode);
			}

			String mopContractName = GeneralImport.addField(csvElement,
					"MOP Contract", values, 3);
			MopContract mopContract = null;
			if (mopContractName.equals(GeneralImport.NO_CHANGE)) {
				mopContract = existingGeneration.getMopContract();
			} else {
				if (mopContractName.length() > 0) {
					mopContract = MopContract.getMopContract(mopContractName);
				}
			}
			String mopAccount = GeneralImport.addField(csvElement,
					"MOP Account Reference", values, 4);
			if (mopAccount.equals(GeneralImport.NO_CHANGE)) {
				mopAccount = existingGeneration.getMopAccount();
			}

			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 5);
			HhdcContract hhdcContract = null;
			if (hhdcContractName.equals(GeneralImport.NO_CHANGE)) {
				hhdcContract = existingGeneration.getHhdcContract();
			} else {
				if (hhdcContractName.length() > 0) {
					hhdcContract = HhdcContract
							.getHhdcContract(hhdcContractName);
				}
			}
			String hhdcAccount = GeneralImport.addField(csvElement,
					"HHDC Account Reference", values, 6);
			if (hhdcAccount.equals(GeneralImport.NO_CHANGE)) {
				hhdcAccount = existingGeneration.getHhdcAccount();
			}

			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh", values, 7);
			boolean hasImportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? existingGeneration
					.getChannel(true, true) != null : Boolean
					.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh", values, 8);
			boolean hasImportKvarh = hasImportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? existingGeneration
					.getChannel(true, false) != null : Boolean
					.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh", values, 9);
			boolean hasExportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? existingGeneration
					.getChannel(false, true) != null : Boolean
					.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh", values, 10);
			boolean hasExportKvarh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? existingGeneration
					.getChannel(false, false) != null : Boolean
					.parseBoolean(hasExportKvarhStr);

			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 11);
			if (meterSerialNumber.equals(GeneralImport.NO_CHANGE)) {
				meterSerialNumber = existingGeneration.getMeterSerialNumber();
			}

			String pcStr = GeneralImport.addField(csvElement, "Profile Class",
					values, 12);
			Pc pc = null;

			if (pcStr.equals(GeneralImport.NO_CHANGE)) {
				pc = existingGeneration.getPc();
			} else {
				pc = Pc.getPc(pcStr);
			}

			String mtcCode = GeneralImport.addField(csvElement,
					"Meter Timeswitch Class", values, 13);
			if (mtcCode.equals(GeneralImport.NO_CHANGE)) {
				mtcCode = existingGeneration.getMtc().toString();
			}

			Cop cop = null;
			String copStr = GeneralImport.addField(csvElement, "CoP", values,
					14);
			if (copStr.equals(GeneralImport.NO_CHANGE)) {
				cop = existingGeneration.getCop();
			} else {
				cop = Cop.getCop(copStr);
			}

			Ssc ssc = null;
			String sscStr = GeneralImport.addField(csvElement,
					"Standard Settlement Configuration", values, 15);
			if (sscStr.equals(GeneralImport.NO_CHANGE)) {
				ssc = existingGeneration.getSsc();
			} else {
				ssc = Ssc.getSsc(sscStr);
			}

			String importMpanCoreStr = GeneralImport.addField(csvElement,
					"Import MPAN Core", values, 16);
			Mpan existingImportMpan = existingGeneration.getImportMpan();
			if (importMpanCoreStr.equals(GeneralImport.NO_CHANGE)) {
				if (existingImportMpan == null) {
					importMpanCoreStr = "";
				} else {
					importMpanCoreStr = existingImportMpan.getCore().toString();
				}
			}

			SupplierContract importSupplierContract = null;
			String importSupplierAccount = null;
			Integer importAgreedSupplyCapacity = null;

			String importLlfcCode = GeneralImport.addField(csvElement,
					"Import Line Loss Factor Class", values, 17);

			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values, 18);
			String importContractSupplierName = GeneralImport.addField(
					csvElement, "Import Supplier Contract", values, 19);
			importSupplierAccount = GeneralImport.addField(csvElement,
					"Import Supplier Account Reference", values, 20);
			if (importMpanCoreStr.length() > 0) {
				if (importLlfcCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There ins't an existing import MPAN.");
					} else {
						importLlfcCode = existingImportMpan.getLlfc()
								.toString();
					}
				}
				if (importAgreedSupplyCapacityStr
						.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan != null) {
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

				if (importContractSupplierName.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan != null) {
						importSupplierContract = existingImportMpan
								.getSupplierContract();
					}
				} else {
					importSupplierContract = SupplierContract
							.getSupplierContract(importContractSupplierName);
				}
			}

			String exportMpanCoreStr = null;
			String exportLlfcCode = null;
			SupplierContract exportSupplierContract = null;
			String exportSupplierAccount = null;
			Integer exportAgreedSupplyCapacity = null;

			if (values.length > 21) {
				Mpan existingExportMpan = existingGeneration.getExportMpan();
				exportMpanCoreStr = GeneralImport.addField(csvElement,
						"Export MPAN", values, 21);
				if (exportMpanCoreStr.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						exportMpanCoreStr = "";
					} else {
						exportMpanCoreStr = existingExportMpan.getCore()
								.toString();
					}
				}

				if (exportMpanCoreStr.length() > 0) {
					exportLlfcCode = GeneralImport.addField(csvElement,
							"Export LLFC", values, 22);
					if (exportLlfcCode.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan == null) {
							throw new UserException(
									"There isn't an existing export MPAN.");
						} else {
							exportLlfcCode = existingExportMpan.getLlfc()
									.toString();
						}
					}

					String exportAgreedSupplyCapacityStr = GeneralImport
							.addField(csvElement,
									"Export Agreed Supply Capacity", values, 22);
					if (exportAgreedSupplyCapacityStr
							.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan != null) {
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
							csvElement, "Export Supplier Contract", values, 23);
					if (exportSupplierContractName
							.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan != null) {
							exportSupplierContract = existingExportMpan
									.getSupplierContract();
						}
					} else {
						exportSupplierContract = SupplierContract
								.getSupplierContract(exportSupplierContractName);
					}
					exportSupplierAccount = GeneralImport.addField(csvElement,
							"Export Supplier Account", values, 24);
					if (exportSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan != null) {
							exportSupplierAccount = existingExportMpan
									.getSupplierAccount();
						}
					}
				}
			}
			SupplyGeneration generation = supply.insertGeneration(site,
					startDate, mopContract, mopAccount, hhdcContract,
					hhdcAccount, meterSerialNumber, pc, mtcCode, cop, ssc,
					importMpanCoreStr, importLlfcCode, importSupplierContract,
					importSupplierAccount, importAgreedSupplyCapacity,
					exportMpanCoreStr, exportLlfcCode, exportSupplierContract,
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

	private HhStartDate startDate;

	private HhStartDate finishDate;
	private MopContract mopContract;
	private String mopAccount;

	private HhdcContract hhdcContract;
	private String hhdcAccount;
	private String meterSerialNumber;
	private Pc pc;
	private Mtc mtc;
	private Cop cop;
	private Ssc ssc;
	private Mpan importMpan;

	private Mpan exportMpan;

	private Set<Mpan> mpans;
	private Set<Channel> channels;

	SupplyGeneration() {
	}

	SupplyGeneration(Supply supply, HhStartDate startDate,
			HhStartDate finishDate, MopContract mopContract, String mopAccount,
			HhdcContract hhdcContract, String hhdcAccount,
			String meterSerialNumber, Pc pc, String mtcCode, Cop cop, Ssc ssc)
			throws HttpException {
		setChannels(new HashSet<Channel>());
		setSupply(supply);
		setSiteSupplyGenerations(new HashSet<SiteSupplyGeneration>());
		setMpans(new HashSet<Mpan>());
		setPc(pc);
		setMtc(Mtc.getMtc(null, "500"));
		setCop(cop);
		setSsc(ssc);
		setStartDate(startDate);
		setFinishDate(finishDate);
		setMopContract(mopContract);
		setMopAccount(mopAccount);
		setHhdcContract(hhdcContract);
		setHhdcAccount(hhdcAccount);
		setMeterSerialNumber(meterSerialNumber);
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

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
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

	public String getMeterSerialNumber() {
		return meterSerialNumber;
	}

	void setMeterSerialNumber(String meterSerialNumber) {
		this.meterSerialNumber = meterSerialNumber;
	}

	void setPc(Pc pc) {
		this.pc = pc;
	}

	public Mtc getMtc() {
		return mtc;
	}

	void setMtc(Mtc mtc) {
		this.mtc = mtc;
	}

	public Cop getCop() {
		return cop;
	}

	void setCop(Cop cop) {
		this.cop = cop;
	}

	public Ssc getSsc() {
		return ssc;
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
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

	public Channel getChannel(boolean isImport, boolean isKwh) {
		for (Channel candidateChannel : channels) {
			if (candidateChannel.getIsImport() == isImport
					&& candidateChannel.getIsKwh() == isKwh) {
				return candidateChannel;
			}
		}
		return null;
	}

	public void update(HhStartDate startDate, HhStartDate finishDate,
			MopContract mopContract, String mopAccount,
			HhdcContract hhdcContract, String hhdcAccount,
			String meterSerialNumber, Pc pc, String mtcCode, Cop cop, Ssc ssc)
			throws HttpException {
		String importLlfcCode = null;
		String importMpanCoreStr = null;
		SupplierContract importSupplierContract = null;
		String importSupplierAccount = null;
		Integer importAgreedSupplyCapacity = null;
		String exportMpanCoreStr = null;
		String exportLlfcCode = null;
		SupplierContract exportSupplierContract = null;
		String exportSupplierAccount = null;
		Integer exportAgreedSupplyCapacity = null;
		if (importMpan != null) {
			importLlfcCode = importMpan.getLlfc().toString();
			importMpanCoreStr = importMpan.getCore().toString();
			importSupplierAccount = importMpan.getSupplierAccount();
			importSupplierContract = importMpan.getSupplierContract();
			importAgreedSupplyCapacity = importMpan.getAgreedSupplyCapacity();
		}
		if (exportMpan != null) {
			exportLlfcCode = exportMpan.getLlfc().toString();
			exportMpanCoreStr = exportMpan.getCore().toString();
			exportSupplierAccount = exportMpan.getSupplierAccount();
			exportSupplierContract = exportMpan.getSupplierContract();
			exportAgreedSupplyCapacity = exportMpan.getAgreedSupplyCapacity();
		}
		update(startDate, finishDate, mopContract, mopAccount, hhdcContract,
				hhdcAccount, meterSerialNumber, pc, mtcCode, cop, ssc,
				importMpanCoreStr, importLlfcCode, importSupplierContract,
				importSupplierAccount, importAgreedSupplyCapacity,
				exportMpanCoreStr, exportLlfcCode, exportSupplierContract,
				exportSupplierAccount, exportAgreedSupplyCapacity);
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

	public void update(HhStartDate startDate, HhStartDate finishDate)
			throws HttpException {
		if (startDate.equals(this.startDate)
				&& HhStartDate.isEqual(finishDate, this.finishDate)) {
			return;
		} else {
			update(startDate, finishDate, mopContract, mopAccount,
					hhdcContract, hhdcAccount, meterSerialNumber, pc, mtc
							.toString(), cop, ssc);
		}
	}

	@SuppressWarnings("unchecked")
	public void update(HhStartDate startDate, HhStartDate finishDate,
			MopContract mopContract, String mopAccount,
			HhdcContract hhdcContract, String hhdcAccount,
			String meterSerialNumber, Pc pc, String mtcCode, Cop cop, Ssc ssc,
			String importMpanCoreStr, String importLlfcCode,
			SupplierContract importSupplierContract,
			String importSupplierAccount, Integer importAgreedSupplyCapacity,
			String exportMpanCoreStr, String exportLlfcCode,
			SupplierContract exportSupplierContract,
			String exportSupplierAccount, Integer exportAgreedSupplyCapacity)
			throws HttpException {
		if (startDate.after(finishDate)) {
			throw new UserException(
					"The generation start date can't be after the finish date.");
		}
		SupplyGeneration previousGeneration = (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration generation where generation.supply = :supply and generation != :generation and generation.startDate.date < :startDate order by generation.startDate.date desc")
				.setEntity("supply", supply).setEntity("generation", this)
				.setTimestamp("startDate", startDate.getDate())
				.setMaxResults(1).uniqueResult();
		SupplyGeneration nextGeneration = null;
		Debug.print("Working on " + getId() + " start date " + getStartDate()
				+ " finish Date " + getFinishDate());
		if (finishDate != null) {
			nextGeneration = (SupplyGeneration) Hiber
					.session()
					.createQuery(
							"from SupplyGeneration generation where generation.supply = :supply and generation != :generation and generation.startDate.date > :startDate order by generation.startDate.date")
					.setEntity("supply", supply).setEntity("generation", this)
					.setTimestamp("startDate", startDate.getDate())
					.setMaxResults(1).uniqueResult();
		}

		setMeterSerialNumber(meterSerialNumber);
		setPc(pc);
		setSsc(ssc);

		List<Long> contractIds = new ArrayList<Long>();
		if (importMpan == null) {
			if (importMpanCoreStr != null && importMpanCoreStr.length() != 0) {
				Hiber.flush();
				Mpan te = new Mpan(this, importLlfcCode, importMpanCoreStr,
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
			if (importMpanCoreStr == null || importMpanCoreStr.length() == 0) {
				mpans.remove(importMpan);
				setImportMpan(null);
			} else {
				importMpan.update(importLlfcCode, importMpanCoreStr,
						importSupplierContract, importSupplierAccount,
						importAgreedSupplyCapacity);
			}
		}
		Hiber.flush();
		if (exportMpan == null) {
			if (exportMpanCoreStr != null && exportMpanCoreStr.length() != 0) {
				setExportMpan(new Mpan(this, exportLlfcCode, exportMpanCoreStr,
						exportSupplierContract, exportSupplierAccount,
						exportAgreedSupplyCapacity));
				mpans.add(getExportMpan());
			}
		} else {
			if (exportMpanCoreStr == null || exportMpanCoreStr.length() == 0) {
				mpans.remove(exportMpan);
				setExportMpan(null);
			} else {
				exportMpan.update(exportLlfcCode, exportMpanCoreStr,
						exportSupplierContract, exportSupplierAccount,
						exportAgreedSupplyCapacity);
			}
		}
		if (importMpan == null && exportMpan == null) {
			throw new UserException(document(),
					"A supply generation must have at least one MPAN.");
		}
		if (importMpan != null) {
			contractIds.add(importMpan.getSupplierContract().getId());
			if (!importMpan.getLlfc().getIsImport()) {
				throw new UserException(document(),
						"The import line loss factor '" + importMpan.getLlfc()
								+ "' says that the MPAN is actually export.");
			}
			if (supply.getSource().getCode().equals(Source.NETWORK_CODE)
					&& importMpan.getCore().getDso().getCode().equals("99")) {
				throw new UserException(
						"A network supply can't have a 99 import MPAN.");
			}
		}
		if (exportMpan != null) {
			contractIds.add(exportMpan.getSupplierContract().getId());
			if (exportMpan.getLlfc().getIsImport()) {
				throw new UserException(
						"Problem with the export MPAN with core '"
								+ exportMpan.getCore()
								+ "'. The Line Loss Factor '"
								+ exportMpan.getLlfc()
								+ "' says that the MPAN is actually import.");
			}
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
		}
		Dso dso = getDso();
		setMtc(Mtc.getMtc(dso, mtcCode));
		String meterTypeCode = mtc.getMeterType().getCode();
		String copCode = cop.getCode();

		if ((meterTypeCode.equals("C5") && !(copCode.equals("1")
				|| copCode.equals("2") || copCode.equals("3")
				|| copCode.equals("4") || copCode.equals("5")))
				|| ((meterTypeCode.equals("6A") || meterTypeCode.equals("6B")
						|| meterTypeCode.equals("6C") || meterTypeCode
						.equals("6D")) && !copCode.toUpperCase().equals(
						meterTypeCode))) {
			throw new UserException("The CoP of " + copCode
					+ " is not compatible with the meter type code of "
					+ meterTypeCode + ".");
		}
		setCop(cop);
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
		if (previousGeneration == null) {
			if (((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from HhDatum datum where datum.channel.supplyGeneration.supply  = :supply and datum.startDate.date < :date")
					.setEntity("supply", supply).setTimestamp("date",
							startDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are HH data before the start of the updated supply.");
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
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (nextGeneration == null) {
			if (finishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.supplyGeneration.supply  = :supply and datum.startDate.date > :date")
							.setEntity("supply", supply).setTimestamp("date",
									finishDate.getDate()).uniqueResult()) > 0) {
				throw new UserException("There are HH data after " + finishDate
						+ ", the end of the updated supply.");
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

		if (hhdcContract == null) {
			hhdcAccount = null;
			if (!channels.isEmpty()) {
				throw new UserException(
						"Can't remove the HHDC account while there are still channels there.");
			}
		} else {
			contractIds.add(hhdcContract.getId());
			hhdcAccount = hhdcAccount == null ? null : hhdcAccount.trim();
			if (hhdcAccount == null || hhdcAccount.length() == 0) {
				throw new UserException(
						"If there's a HHDC contract, there must be an account reference.");
			}
			HhStartDate hhdcContractStartDate = hhdcContract
					.getStartRateScript().getStartDate();
			if (hhdcContractStartDate.after(startDate)) {
				throw new UserException(
						"The HHDC contract starts after the supply generation.");
			}
			HhStartDate hhdcContractFinishDate = hhdcContract
					.getFinishRateScript().getFinishDate();
			if (HhStartDate.isBefore(hhdcContractFinishDate, finishDate)) {
				throw new UserException("The HHDC contract "
						+ hhdcContract.getId()
						+ " finishes before the supply generation.");
			}
		}
		Hiber.flush();
		setHhdcAccount(hhdcAccount);
		setHhdcContract(hhdcContract);
		Hiber.flush();

		if (mopContract == null) {
			mopAccount = null;
		} else {
			contractIds.add(mopContract.getId());
			mopAccount = mopAccount == null ? null : mopAccount.trim();
			if (mopAccount == null || mopAccount.length() == 0) {
				throw new UserException(
						"If there's a MOP contract, there must be an account reference.");
			}
			HhStartDate mopContractStartDate = mopContract.getStartRateScript()
					.getStartDate();
			if (mopContractStartDate.after(startDate)) {
				throw new UserException(
						"The MOP contract starts after the supply generation.");
			}
			HhStartDate mopContractFinishDate = mopContract
					.getFinishRateScript().getFinishDate();
			if (HhStartDate.isBefore(mopContractFinishDate, finishDate)) {
				throw new UserException("The MOP contract "
						+ mopContract.getId()
						+ " finishes before the supply generation.");
			}
		}

		if (pc.getCode() == 0 && ssc != null) {
			throw new UserException(
					"A supply with Profile Class 00 can't have a Standard Settlement Configuration.");
		}
		if (pc.getCode() > 0 && ssc == null) {
			throw new UserException(
					"A NHH supply must have a Standard Settlement Configuration.");
		}

		setSsc(ssc);
		Hiber.flush();
		setMopAccount(mopAccount);
		setMopContract(mopContract);
		Hiber.flush();

		for (Channel channel : channels) {
			channel.onSupplyGenerationChange();
		}
		Hiber.flush();
		Query billQuery = Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.supply = :supply and "
								+ (finishDate == null ? ""
										: "bill.startDate.date <= :finishDate and ")
								+ " bill.finishDate.date >= :startDate and bill.batch.contract.id not in (:contractIds)")
				.setEntity("supply", supply).setTimestamp("startDate",
						startDate.getDate()).setParameterList("contractIds",
						contractIds);
		if (finishDate != null) {
			billQuery.setTimestamp("finishDate", finishDate.getDate());
		}
		List<Bill> orphanBills = (List<Bill>) billQuery.list();
		if (!orphanBills.isEmpty()) {
			throw new UserException(
					"There are some bills which wouldn't have the right contract, for example: "
							+ orphanBills.get(0).getId() + ".");
		}
		// See if we have to move hh data from one generation to the other
		for (Boolean isImport : new Boolean[] { true, false }) {
			for (Boolean isKwh : new Boolean[] { true, false }) {
				Channel targetChannel = getChannel(isImport, isKwh);
				Query query = Hiber
						.session()
						.createQuery(
								"select datum.startDate, datum.value, datum.status from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.startDate.date >= :from"
										+ (finishDate == null ? ""
												: " and datum.startDate.date <= :to")
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
				HhStartDate groupStart = null;
				if (hhData.next()) {
					groupStart = (HhStartDate) hhData.get(0);
					if (targetChannel == null) {
						throw new UserException(
								"There is no channel for the HH datum starting: "
										+ groupStart.toString()
										+ " is import? "
										+ isImport
										+ " is kWh? "
										+ isKwh
										+ " to move to in the generation starting "
										+ startDate + ", finishing "
										+ finishDate + ".");
					}
					Query channelUpdate = Hiber
							.session()
							.createSQLQuery(
									"update hh_datum set channel_id = :targetChannelId from channel, supply_generation where hh_datum.start_date >= :startDate and channel.id = hh_datum.channel_id and supply_generation.id = channel.supply_generation_id and channel.is_import = :isImport and channel.is_kwh = :isKwh and supply_generation.supply_id = :supplyId"
											+ (finishDate == null ? ""
													: " and hh_datum.start_date <= :finishDate"))
							.setLong("supplyId", supply.getId()).setBoolean(
									"isImport", isImport).setBoolean("isKwh",
									isKwh).setLong("targetChannelId",
									targetChannel.getId()).setTimestamp(
									"startDate", startDate.getDate());
					if (finishDate != null) {
						channelUpdate.setTimestamp("finishDate", finishDate
								.getDate());
					}
					channelUpdate.executeUpdate();
					HhStartDate groupFinish = groupStart;

					hhData.beforeFirst();
					while (hhData.next()) {
						HhStartDate hhStartDate = (HhStartDate) hhData.get(0);
						if (groupFinish.getNext().before(hhStartDate)) {
							targetChannel.deleteSnag(ChannelSnag.SNAG_MISSING,
									groupStart, groupFinish);
							groupStart = groupFinish = hhStartDate;
						} else {
							groupFinish = hhStartDate;
						}
						if (((BigDecimal) hhData.get(1)).doubleValue() < 0) {
							targetChannel.addSnag(ChannelSnag.SNAG_NEGATIVE,
									hhStartDate, hhStartDate);
						}
						if ((Character) hhData.get(2) != HhDatum.ACTUAL) {
							targetChannel.addSnag(ChannelSnag.SNAG_ESTIMATED,
									hhStartDate, hhStartDate);
						}
					}
					targetChannel.deleteSnag(ChannelSnag.SNAG_MISSING,
							groupStart, groupFinish);
					hhData.close();
				}
			}
		}
		Hiber.flush();
		for (Mpan mpan : mpans) {
			SupplierContract supplierContract = mpan.getSupplierContract();
			if (supplierContract.getStartRateScript().getStartDate().after(
					startDate)) {
				throw new UserException(
						"The supplier contract starts after the supply generation.");
			}
			if (HhStartDate.isBefore(supplierContract.getFinishRateScript()
					.getFinishDate(), finishDate)) {
				throw new UserException(
						"The supplier contract finishes before the supply generation.");
			}
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
		element.setAttribute("meter-serial-number", meterSerialNumber);
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
				"mtc").put("cop").put("ssc").put("supply",
				new XmlTree("source").put("gspGroup")).put("mopContract",
				new XmlTree("party")).put("hhdcContract", new XmlTree("party")));
		source.appendChild(generationElement);
		for (Mpan mpan : mpans) {
			Element mpanElement = (Element) mpan.toXml(doc, new XmlTree("core")
					.put("llfc").put("supplierContract", new XmlTree("party")));
			generationElement.appendChild(mpanElement);
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (Pc pc : (List<Pc>) Hiber.session().createQuery(
				"from Pc pc order by pc.code").list()) {
			source.appendChild(pc.toXml(doc));
		}
		for (Cop cop : (List<Cop>) Hiber.session().createQuery(
				"from Cop cop order by cop.code").list()) {
			source.appendChild(cop.toXml(doc));
		}
		for (GspGroup group : (List<GspGroup>) Hiber.session().createQuery(
				"from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}
		for (MopContract contract : (List<MopContract>) Hiber
				.session()
				.createQuery("from MopContract contract order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
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
		source.setAttribute("num-generations", Integer.toString(supply
				.getGenerations().size()));
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
				Date startDate = inv.getDate("start");
				Long mopContractId = inv.getLong("mop-contract-id");
				Long hhdcContractId = inv.getLong("hhdc-contract-id");
				String meterSerialNumber = inv.getString("meter-serial-number");
				Long pcId = inv.getLong("pc-id");
				String mtcCode = inv.getString("mtc-code");
				Long copId = inv.getLong("cop-id");
				String sscCode = inv.getString("ssc-code");

				if (!inv.isValid()) {
					throw new UserException();
				}
				HhStartDate finishDate = null;
				Cop cop = Cop.getCop(copId);
				Ssc ssc = null;
				if (sscCode.trim().length() > 0) {
					ssc = Ssc.getSsc(sscCode);
				}

				String importMpanCoreStr = null;
				Integer importAgreedSupplyCapacity = null;
				MopContract mopContract = null;
				HhdcContract hhdcContract = null;
				SupplierContract importSupplierContract = null;
				String importSupplierAccount = null;
				boolean isEnded = inv.getBoolean("is-ended");
				if (isEnded) {
					Date finishDateRaw = inv.getDate("finish");
					Calendar cal = MonadDate.getCalendar();
					cal.setTime(finishDateRaw);
					cal.add(Calendar.DAY_OF_MONTH, 1);
					finishDate = new HhStartDate(cal.getTime()).getPrevious();
				}
				String mopAccount = null;
				if (mopContractId != null) {
					mopContract = MopContract.getMopContract(mopContractId);
					mopAccount = inv.getString("mop-account");
				}
				String hhdcAccount = null;
				if (hhdcContractId != null) {
					hhdcContract = HhdcContract.getHhdcContract(hhdcContractId);
					hhdcAccount = inv.getString("hhdc-account");
				}
				Pc pc = Pc.getPc(pcId);
				boolean hasImportMpan = inv.getBoolean("has-import-mpan");
				String importLlfcCode = null;

				if (hasImportMpan) {
					importMpanCoreStr = inv.getString("import-mpan-core");
					importLlfcCode = inv.getString("import-llfc-code");
					Long importSupplierContractId = inv
							.getLong("import-supplier-contract-id");
					importSupplierAccount = inv
							.getString("import-supplier-account");
					importAgreedSupplyCapacity = inv
							.getInteger("import-agreed-supply-capacity");

					if (!inv.isValid()) {
						throw new UserException(document());
					}

					importSupplierContract = SupplierContract
							.getSupplierContract(importSupplierContractId);
				}
				String exportMpanCoreStr = null;
				String exportLlfcCode = null;
				Integer exportAgreedSupplyCapacity = null;
				String exportSupplierAccount = null;
				SupplierContract exportSupplierContract = null;
				boolean hasExportMpan = inv.getBoolean("has-export-mpan");
				if (hasExportMpan) {
					exportMpanCoreStr = inv.getString("export-mpan-core");
					exportLlfcCode = inv.getString("export-llfc-code");
					exportAgreedSupplyCapacity = inv
							.getInteger("export-agreed-supply-capacity");
					Long exportSupplierContractId = inv
							.getLong("export-supplier-contract-id");
					exportSupplierAccount = inv
							.getString("export-supplier-account");

					if (!inv.isValid()) {
						throw new UserException();
					}
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractId);
				}
				supply.updateGeneration(this, new HhStartDate(startDate),
						finishDate, mopContract, mopAccount, hhdcContract,
						hhdcAccount, meterSerialNumber, pc, mtcCode, cop, ssc,
						importMpanCoreStr, importLlfcCode,
						importSupplierContract, importSupplierAccount,
						importAgreedSupplyCapacity, exportMpanCoreStr,
						exportLlfcCode, exportSupplierContract,
						exportSupplierAccount, exportAgreedSupplyCapacity);
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
