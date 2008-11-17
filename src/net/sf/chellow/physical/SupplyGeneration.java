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
			if (values.length < 29) {
				throw new UserException(
						"There aren't enough fields in this row");
			}
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values[0]);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			Supply supply = mpanCore.getSupply();
			String dateStr = GeneralImport.addField(csvElement, "Date",
					values[1]);

			SupplyGeneration supplyGeneration = supply.getGeneration(dateStr
					.length() == 0 ? null : new HhEndDate(dateStr));
			if (supplyGeneration == null) {
				throw new UserException(
						"There isn't a generation at this date.");
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values[2]);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values[3]);
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values[4]);
			Meter meter = null;
			if (meterSerialNumber.length() != 0) {
				meter = supply.findMeter(meterSerialNumber);
				if (meter == null) {
					meter = supply.insertMeter(meterSerialNumber);
				}
			}
			supplyGeneration.update(startDateStr
					.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
					.getStartDate() : new HhEndDate("start", startDateStr),
					finishDateStr.length() == 0 ? null : (finishDateStr
							.equals(GeneralImport.NO_CHANGE) ? supplyGeneration
							.getFinishDate() : new HhEndDate("finish",
							finishDateStr)), meter);
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values[5]);
			boolean importHasImportKwh = false;
			boolean importHasImportKvarh = false;
			boolean importHasExportKwh = false;
			boolean importHasExportKvarh = false;
			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values[6]);
			Ssc importSsc = null;
			String importGspGroupCode = GeneralImport.addField(csvElement,
					"Import GSP Group", values[7]);
			GspGroup importGspGroup = null;
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values[8]);
			Integer importAgreedSupplyCapacity = null;
			Mpan existingImportMpan = supplyGeneration.getImportMpan();
			HhdcContract importHhdcContract = null;
			Account importHhdcAccount = null;
			SupplierContract importSupplierContract = null;
			Account importSupplierAccount = null;
			if (importMpanStr.equals(GeneralImport.NO_CHANGE)) {
				importMpanStr = existingImportMpan == null ? null
						: existingImportMpan.toString();
			}
			if (importMpanStr != null) {
				if (importSscCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import MPAN.");
					} else {
						importSsc = existingImportMpan.getTop().getSsc();
					}
				} else {
					importSsc = importSscCode.length() == 0 ? null : Ssc
							.getSsc(importSscCode);
				}
				if (importGspGroupCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingImportMpan == null) {
						throw new UserException(
								"There isn't an existing import MPAN.");
					} else {
						importGspGroup = existingImportMpan.getTop()
								.getGspGroup();
					}
				} else {
					importGspGroup = GspGroup.getGspGroup(importSscCode);
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
				String importHasImportKwhStr = GeneralImport.addField(
						csvElement, "Import is import kWh", values[9]);
				importHasImportKwh = importHasImportKwhStr
						.equals(GeneralImport.NO_CHANGE) ? existingImportMpan == null ? false
						: existingImportMpan.getHasImportKwh()
						: Boolean.parseBoolean(importHasImportKwhStr);
				String importHasImportKvarhStr = GeneralImport.addField(
						csvElement, "Import is import kVArh", values[10]);
				importHasImportKvarh = importHasImportKvarhStr
						.equals(GeneralImport.NO_CHANGE) ? existingImportMpan == null ? false
						: existingImportMpan.getHasImportKvarh()
						: Boolean.parseBoolean(importHasImportKvarhStr);
				String importHasExportKwhStr = GeneralImport.addField(
						csvElement, "Import is export kWh", values[11]);
				importHasExportKwh = importHasExportKwhStr
						.equals(GeneralImport.NO_CHANGE) ? existingImportMpan == null ? false
						: existingImportMpan.getHasExportKwh()
						: Boolean.parseBoolean(importHasExportKwhStr);
				String importHasExportKvarhStr = GeneralImport.addField(
						csvElement, "Import is export kVArh", values[12]);
				importHasExportKvarh = importHasExportKvarhStr
						.equals(GeneralImport.NO_CHANGE) ? existingImportMpan == null ? false
						: existingImportMpan.getHasExportKvarh()
						: Boolean.parseBoolean(importHasExportKvarhStr);
				if (importHasImportKwh || importHasImportKvarh
						|| importHasExportKwh || importHasExportKvarh) {
					/*
					 * String importHhdceStr = values[13];
					 * csvElement.appendChild(getField("Import DCE",
					 * importHhdceStr)); if (importHhdceStr.equals(NO_CHANGE)) {
					 * if (existingImportMpan.getHhdceContract() == null) {
					 * throw new UserException( "There isn't an existing DCE
					 * contract"); } else { importHhdce = existingImportMpan
					 * .getHhdceContract().getProvider(); } } else { importHhdce =
					 * Provider.getProvider( importHhdceStr, MarketRole.HHDC); }
					 */
					String importHhdcContractName = GeneralImport.addField(
							csvElement, "Import HHDC Contract", values[13]);
					if (importHhdcContractName.equals(GeneralImport.NO_CHANGE)) {
						if (existingImportMpan == null) {
							throw new UserException(
									"There isn't an existing HHDC contract");
						}
						Account account = existingImportMpan.getHhdcAccount();
						if (account == null) {
							throw new UserException(
									"There isn't an existing HHDC contract");
						}
						importHhdcContract = HhdcContract
								.getHhdcContract(account.getContract().getId());
					} else {
						importHhdcContract = HhdcContract
								.getHhdcContract(importHhdcContractName);
					}
					String importHhdcAccountReference = GeneralImport.addField(
							csvElement, "Import HHDC account reference",
							values[14]);
					if (importHhdcAccountReference
							.equals(GeneralImport.NO_CHANGE)) {
						if (existingImportMpan == null) {
							throw new UserException(
									"There isn't an existing import HHDC account");
						}
						Account account = existingImportMpan.getHhdcAccount();
						if (account == null) {
							throw new UserException(
									"There isn't an existing HHDC account");
						}
						importHhdcAccount = account;
					} else {
						importHhdcAccount = importHhdcContract
								.getAccount(importHhdcAccountReference);
					}
				}
				String importContractSupplierName = GeneralImport.addField(
						csvElement, "Import Supplier Contract", values[15]);
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
						values[16]);
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
					"Eport MPAN", values[17]);
			String exportSscCode = GeneralImport.addField(csvElement,
					"Export SSC", values[18]);
			Ssc exportSsc = null;
			String exportGspGroupCode = GeneralImport.addField(csvElement,
					"Export GSP Group", values[19]);
			GspGroup exportGspGroup = null;
			boolean exportHasImportKwh = false;
			boolean exportHasImportKvarh = false;
			boolean exportHasExportKwh = false;
			boolean exportHasExportKvarh = false;
			String exportAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Export Agreed Supply Capacity", values[20]);
			Mpan existingExportMpan = supplyGeneration.getExportMpan();
			Integer exportAgreedSupplyCapacity = null;
			if (exportMpanStr.equals(GeneralImport.NO_CHANGE)) {
				exportMpanStr = existingExportMpan == null ? null
						: existingExportMpan.toString();
			}
			Account exportHhdcAccount = null;
			SupplierContract exportSupplierContract = null;
			Account exportAccountSupplier = null;
			if (exportMpanStr != null) {
				if (exportSscCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export MPAN.");
					} else {
						exportSsc = existingExportMpan.getTop().getSsc();
					}
				} else {
					exportSsc = exportSscCode.length() == 0 ? null : Ssc
							.getSsc(exportSscCode);
				}
				if (exportGspGroupCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingExportMpan == null) {
						throw new UserException(
								"There isn't an existing export MPAN.");
					} else {
						exportGspGroup = existingExportMpan.getTop()
								.getGspGroup();
					}
				} else {
					exportGspGroup = GspGroup.getGspGroup(exportGspGroupCode);
				}
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
				String exportHasImportKwhStr = GeneralImport.addField(
						csvElement, "Export is import kWh", values[21]);
				exportHasImportKwh = exportHasImportKwhStr
						.equals(GeneralImport.NO_CHANGE) ? existingExportMpan == null ? false
						: existingExportMpan.getHasImportKwh()
						: Boolean.parseBoolean(exportHasImportKwhStr);
				String exportHasImportKvarhStr = GeneralImport.addField(
						csvElement, "Export is import kVArh", values[22]);
				exportHasImportKvarh = exportHasImportKvarhStr
						.equals(GeneralImport.NO_CHANGE) ? existingExportMpan == null ? false
						: existingExportMpan.getHasImportKvarh()
						: Boolean.parseBoolean(exportHasImportKvarhStr);
				String exportHasExportKwhStr = GeneralImport.addField(
						csvElement, "Export is export kWh", values[23]);
				exportHasExportKwh = exportHasExportKwhStr
						.equals(GeneralImport.NO_CHANGE) ? existingExportMpan == null ? false
						: existingExportMpan.getHasExportKwh()
						: Boolean.parseBoolean(exportHasExportKwhStr);
				String exportHasExportKvarhStr = GeneralImport.addField(
						csvElement, "Export is export kVArh", values[24]);
				exportHasExportKvarh = exportHasExportKvarhStr
						.equals(GeneralImport.NO_CHANGE) ? existingExportMpan == null ? false
						: existingExportMpan.getHasExportKvarh()
						: Boolean.parseBoolean(exportHasExportKvarhStr);
				HhdcContract exportHhdcContract = null;
				if (exportHasImportKwh || exportHasImportKvarh
						|| exportHasExportKwh || exportHasExportKvarh) {
					String exportHhdcContractName = GeneralImport
							.addField(csvElement, "Export HHDC Contract Name",
									values[25]);
					if (exportHhdcContractName.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan == null) {
							throw new UserException(
									"There isn't an existing export HHDC contract.");
						}
						Account account = existingExportMpan.getHhdcAccount();
						if (account == null) {
							throw new UserException(
									"There isn't an existing export HHDC contract.");
						}
						exportHhdcContract = HhdcContract
								.getHhdcContract(account.getContract().getId());
					} else {
						exportHhdcContract = HhdcContract
								.getHhdcContract(exportHhdcContractName);
					}
					String exportHhdcAccountReference = GeneralImport.addField(
							csvElement, "Export HHDC account", values[26]);
					if (exportHhdcAccountReference
							.equals(GeneralImport.NO_CHANGE)) {
						if (existingExportMpan == null) {
							throw new UserException(
									"There isn't an existing export supplier account.");
						}
						Account account = existingExportMpan.getHhdcAccount();
						if (account == null) {
							throw new UserException(
									"There isn't an existing export supplier account.");
						}
						exportHhdcAccount = existingExportMpan.getHhdcAccount();
					} else {
						exportHhdcAccount = exportHhdcContract
								.getAccount(exportHhdcAccountReference);
					}
				}
				String exportContractSupplierName = GeneralImport.addField(
						csvElement, "Export Supplier Contract", values[27]);
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
						csvElement, "Export Supplier Account", values[28]);
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
					importGspGroup, importHhdcAccount, importSupplierAccount,
					importHasImportKwh, importHasImportKvarh,
					importHasExportKwh, importHasExportKvarh,
					importAgreedSupplyCapacity, exportMpanStr, exportSsc,
					exportGspGroup, exportHhdcAccount, exportAccountSupplier,
					exportHasImportKwh, exportHasImportKvarh,
					exportHasExportKwh, exportHasExportKvarh,
					exportAgreedSupplyCapacity);
		} else if (action.equals("insert")) {
			String siteCode = GeneralImport.addField(csvElement, "Site Code",
					values[0]);
			Site site = Site.getSite(siteCode);
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values[0]);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			Supply supply = mpanCore.getSupply();
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values[1]);
			HhEndDate finishDate = finishDateStr.length() == 0 ? null : new HhEndDate(finishDateStr);
			String meterSerialNumber = GeneralImport.addField(csvElement,
					"Meter Serial Number", values[2]);
			Meter meter = null;
			if (meterSerialNumber.length() != 0) {
				meter = supply.findMeter(meterSerialNumber);
				if (meter == null) {
					meter = supply.insertMeter(meterSerialNumber);
				}
			}
			String importMpanStr = GeneralImport.addField(csvElement,
					"Import MPAN", values[3]);
			boolean importHasImportKwh = false;
			boolean importHasImportKvarh = false;
			boolean importHasExportKwh = false;
			boolean importHasExportKvarh = false;
			String importSscCode = GeneralImport.addField(csvElement,
					"Import SSC", values[4]);
			Ssc importSsc = null;
			String importGspGroupCode = GeneralImport.addField(csvElement,
					"Import GSP Group", values[5]);
			GspGroup importGspGroup = null;
			String importAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Import Agreed Supply Capacity", values[6]);
			Integer importAgreedSupplyCapacity = null;
			HhdcContract importHhdcContract = null;
			Account importHhdcAccount = null;
			SupplierContract importSupplierContract = null;
			Account importSupplierAccount = null;
			if (importMpanStr != null) {
				importSsc = importSscCode.length() == 0 ? null : Ssc
						.getSsc(importSscCode);
				importGspGroup = GspGroup.getGspGroup(importGspGroupCode);
				try {
					importAgreedSupplyCapacity = Integer
							.parseInt(importAgreedSupplyCapacityStr);
				} catch (NumberFormatException e) {
					throw new UserException(
							"The import agreed supply capacity must be an integer. "
									+ e.getMessage());
				}
				String importHasImportKwhStr = GeneralImport.addField(
						csvElement, "Import is import kWh", values[7]);
				importHasImportKwh = Boolean
						.parseBoolean(importHasImportKwhStr);
				String importHasImportKvarhStr = GeneralImport.addField(
						csvElement, "Import is import kVArh", values[8]);
				importHasImportKvarh = Boolean
						.parseBoolean(importHasImportKvarhStr);
				String importHasExportKwhStr = GeneralImport.addField(
						csvElement, "Import is export kWh", values[9]);
				importHasExportKwh = Boolean
						.parseBoolean(importHasExportKwhStr);
				String importHasExportKvarhStr = GeneralImport.addField(
						csvElement, "Import is export kVArh", values[10]);
				importHasExportKvarh = Boolean
						.parseBoolean(importHasExportKvarhStr);
				if (importHasImportKwh || importHasImportKvarh
						|| importHasExportKwh || importHasExportKvarh) {
					String importHhdcContractName = GeneralImport.addField(
							csvElement, "Import HHDC Contract", values[11]);
					importHhdcContract = HhdcContract
							.getHhdcContract(importHhdcContractName);
					String importHhdcAccountReference = GeneralImport.addField(
							csvElement, "Import HHDC account reference",
							values[12]);
					importHhdcAccount = importHhdcContract
							.getAccount(importHhdcAccountReference);
				}
				String importContractSupplierName = GeneralImport.addField(
						csvElement, "Import Supplier Contract", values[13]);
				importSupplierContract = SupplierContract
						.getSupplierContract(importContractSupplierName);
				String importSupplierAccountReference = GeneralImport.addField(
						csvElement, "Import Supplier Account Reference",
						values[14]);
				importSupplierAccount = importSupplierContract
						.getAccount(importSupplierAccountReference);
			}
			String exportMpanStr = GeneralImport.addField(csvElement,
					"Eport MPAN", values[15]);
			String exportSscCode = GeneralImport.addField(csvElement,
					"Export SSC", values[16]);
			Ssc exportSsc = null;
			String exportGspGroupCode = GeneralImport.addField(csvElement,
					"Export GSP Group", values[17]);
			GspGroup exportGspGroup = null;
			boolean exportHasImportKwh = false;
			boolean exportHasImportKvarh = false;
			boolean exportHasExportKwh = false;
			boolean exportHasExportKvarh = false;
			String exportAgreedSupplyCapacityStr = GeneralImport.addField(
					csvElement, "Export Agreed Supply Capacity", values[18]);
			Integer exportAgreedSupplyCapacity = null;
			Account exportHhdcAccount = null;
			SupplierContract exportSupplierContract = null;
			Account exportSupplierAccount = null;
			if (exportMpanStr != null) {
				exportSsc = exportSscCode.length() == 0 ? null : Ssc
						.getSsc(exportSscCode);
				exportGspGroup = GspGroup.getGspGroup(exportGspGroupCode);
				try {
					exportAgreedSupplyCapacity = new Integer(
							exportAgreedSupplyCapacityStr);
				} catch (NumberFormatException e) {
					throw new UserException(
							"The export supply capacity must be an integer. "
									+ e.getMessage());
				}
				String exportHasImportKwhStr = GeneralImport.addField(
						csvElement, "Export is import kWh", values[19]);
				exportHasImportKwh = Boolean
						.parseBoolean(exportHasImportKwhStr);
				String exportHasImportKvarhStr = GeneralImport.addField(
						csvElement, "Export is import kVArh", values[20]);
				exportHasImportKvarh = Boolean
						.parseBoolean(exportHasImportKvarhStr);
				String exportHasExportKwhStr = GeneralImport.addField(
						csvElement, "Export is export kWh", values[21]);
				exportHasExportKwh = Boolean
						.parseBoolean(exportHasExportKwhStr);
				String exportHasExportKvarhStr = GeneralImport.addField(
						csvElement, "Export is export kVArh", values[22]);
				exportHasExportKvarh = Boolean
						.parseBoolean(exportHasExportKvarhStr);
				HhdcContract exportHhdcContract = null;
				if (exportHasImportKwh || exportHasImportKvarh
						|| exportHasExportKwh || exportHasExportKvarh) {
					String exportHhdcContractName = GeneralImport
							.addField(csvElement, "Export HHDC Contract Name",
									values[23]);
					exportHhdcContract = HhdcContract
							.getHhdcContract(exportHhdcContractName);
					String exportHhdcAccountReference = GeneralImport.addField(
							csvElement, "Export HHDC account", values[24]);
					exportHhdcAccount = exportHhdcContract
							.getAccount(exportHhdcAccountReference);
				}
				String exportContractSupplierName = GeneralImport.addField(
						csvElement, "Export Supplier Contract", values[25]);
				exportSupplierContract = SupplierContract
						.getSupplierContract(exportContractSupplierName);
				String exportSupplierAccountReference = GeneralImport.addField(
						csvElement, "Export Supplier Account", values[26]);
				exportSupplierAccount = exportSupplierContract
						.getAccount(exportSupplierAccountReference);
			}
			Map<Site, Boolean> siteMap = new HashMap<Site, Boolean>();
			siteMap.put(site, true);
			supply.insertGeneration(siteMap, finishDate, meter, importMpanStr, importSsc,
					importGspGroup, importHhdcAccount, importSupplierAccount,
					importHasImportKwh, importHasImportKvarh,
					importHasExportKwh, importHasExportKvarh,
					importAgreedSupplyCapacity, exportMpanStr, exportSsc,
					exportGspGroup, exportHhdcAccount, exportSupplierAccount,
					exportHasImportKwh, exportHasImportKvarh,
					exportHasExportKwh, exportHasExportKvarh,
					exportAgreedSupplyCapacity);
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

	private Mpan importMpan;

	private Mpan exportMpan;

	private Set<Mpan> mpans;

	private Meter meter;

	private Set<Channel> channels;

	SupplyGeneration() {
	}

	SupplyGeneration(Supply supply, HhEndDate startDate, HhEndDate finishDate,
			Meter meter) throws HttpException {
		setChannels(new HashSet<Channel>());
		setSupply(supply);
		setSiteSupplyGenerations(new HashSet<SiteSupplyGeneration>());
		setMpans(new HashSet<Mpan>());
		internalUpdate(startDate, finishDate, meter);
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

	/*
	 * public void addOrUpdateMpans(MpanTop importMpanTop, MpanCore
	 * importMpanCore, Account importHhdcAccount, Account importSupplierAccount,
	 * boolean importHasImportKwh, boolean importHasImportKvarh, boolean
	 * importHasExportKwh, boolean importHasExportKvarh, Integer
	 * importAgreedSupplyCapacity, MpanTop exportMpanTop, MpanCore
	 * exportMpanCore, Account exportHhdcAccount, Account exportSupplierAccount,
	 * boolean exportHasImportKwh, boolean exportHasImportKvarh, boolean
	 * exportHasExportKwh, boolean exportHasExportKvarh, Integer
	 * exportAgreedSupplyCapacity) throws HttpException { if (importMpanCore ==
	 * null && exportMpanCore == null) { throw new UserException(document(), "A
	 * supply generation must have at least one MPAN."); } if (importMpanCore ==
	 * null) { mpans.remove(importMpan); setImportMpan(null); } else { if
	 * (!importMpanCore.getSupply().equals(getSupply())) { throw new
	 * UserException( "This import MPAN core is not attached to this supply."); }
	 * if (!importMpanTop.getLlfc().getIsImport()) { throw new
	 * UserException(document(), "The import line loss factor '" +
	 * importMpanTop.getLlfc() + "' says that the MPAN is actually export."); }
	 * if (importMpan == null) { setImportMpan(new Mpan(this, importMpanTop,
	 * importMpanCore, importHhdcAccount, importSupplierAccount,
	 * importHasImportKwh, importHasImportKvarh, importHasExportKwh,
	 * importHasExportKvarh, importAgreedSupplyCapacity));
	 * mpans.add(importMpan); } else { importMpan.update(importMpanTop,
	 * importMpanCore, importHhdcAccount, importSupplierAccount,
	 * importHasImportKwh, importHasImportKvarh, importHasExportKwh,
	 * importHasExportKvarh, importAgreedSupplyCapacity); } } if (exportMpanCore ==
	 * null) { mpans.remove(exportMpan); setExportMpan(null); } else { if
	 * (!exportMpanCore.getSupply().equals(getSupply())) { throw new
	 * UserException( "This export MPAN core is not attached to this supply."); }
	 * if (exportMpanTop.getLlfc().getIsImport()) { throw new UserException(
	 * "Problem with the export MPAN with core '" + exportMpanCore + "'. The
	 * Line Loss Factor '" + exportMpanTop.getLlfc() + "' says that the MPAN is
	 * actually import."); } if (exportMpan == null) { setExportMpan(new
	 * Mpan(this, exportMpanTop, exportMpanCore, exportHhdcAccount,
	 * exportSupplierAccount, exportHasImportKwh, exportHasImportKvarh,
	 * exportHasExportKwh, exportHasExportKvarh, exportAgreedSupplyCapacity));
	 * mpans.add(exportMpan); } else { exportMpan.update(exportMpanTop,
	 * exportMpanCore, exportHhdcAccount, exportSupplierAccount,
	 * exportHasImportKwh, exportHasImportKvarh, exportHasExportKwh,
	 * exportHasExportKvarh, exportAgreedSupplyCapacity); } } if
	 * (importHhdcAccount != null && exportHhdcAccount != null &&
	 * importHhdcAccount.getContract().getId() != exportHhdcAccount
	 * .getContract().getId()) { throw new UserException( "The HHDC for the
	 * import and export MPANs must be the same."); } synchronizeChannel(true,
	 * true, importHasImportKwh, exportHasImportKwh); synchronizeChannel(true,
	 * false, importHasImportKvarh, exportHasImportKvarh);
	 * synchronizeChannel(false, true, importHasExportKwh, exportHasExportKwh);
	 * synchronizeChannel(false, false, importHasExportKvarh,
	 * exportHasExportKvarh); Hiber.flush(); // Check that if settlement MPANs
	 * then they're the same DSO. if (importMpanCore != null && exportMpanCore !=
	 * null) { if (importMpanCore.getDso().getCode().isSettlement() &&
	 * exportMpanCore.getDso().getCode().isSettlement() &&
	 * !importMpanCore.getDso().equals(exportMpanCore.getDso())) { throw new
	 * UserException( "Two settlement MPAN generations on the same supply must
	 * have the same DSO."); } if
	 * (!importMpanTop.getLlfc().getVoltageLevel().equals(
	 * exportMpanTop.getLlfc().getVoltageLevel())) { throw new UserException(
	 * "The voltage level indicated by the Line Loss Factor must be the same for
	 * both the MPANs."); } } Dso dso = getDso(); if (dso != null &&
	 * dso.getCode().equals(new DsoCode("22"))) { /* if (importMpan != null) {
	 * LineLossFactorCode code = importLineLossFactor.getCode(); if
	 * ((code.equals(new LineLossFactorCode("520")) || code.equals(new
	 * LineLossFactorCode("550")) || code .equals(new
	 * LineLossFactorCode("580"))) && getExportMpan() == null) { throw
	 * UserException .newOk("The Line Loss Factor of the import MPAN says that
	 * there should be an export MPAN, but there isn't one."); } }
	 */
	/*
	 * if (getExportMpan() != null && getImportMpan() != null) { LlfcCode code =
	 * getImportMpan().getMpanTop().getLlfc() .getCode(); if (!code.equals(new
	 * LlfcCode(520)) && !code.equals(new LlfcCode(550)) && !code.equals(new
	 * LlfcCode(580))) { throw new UserException( "The DSO is 22, there's an
	 * export MPAN and the Line Loss Factor of the import MPAN " +
	 * getImportMpan() + " can only be 520, 550 or 580."); } } } Hiber.flush(); //
	 * more optimization possible here, doesn't necessarily need to check //
	 * data. getSupply().checkAfterUpdate(getStartDate(), getFinishDate()); }
	 */

	public void addOrUpdateMpans(String importMpanStr, Ssc importSsc,
			GspGroup importGspGroup, Account importHhdcAccount,
			Account importSupplierAccount, Boolean importHasImportKwh,
			Boolean importHasImportKvarh, Boolean importHasExportKwh,
			Boolean importHasExportKvarh, Integer importAgreedSupplyCapacity,
			String exportMpanStr, Ssc exportSsc, GspGroup exportGspGroup,
			Account exportHhdcAccount, Account exportSupplierAccount,
			Boolean exportHasImportKwh, Boolean exportHasImportKvarh,
			Boolean exportHasExportKwh, Boolean exportHasExportKvarh,
			Integer exportAgreedSupplyCapacity) throws HttpException {
		if (importMpan == null) {
			if (importMpanStr != null && importMpanStr.length() != 0) {
				setImportMpan(new Mpan(this, importMpanStr, importSsc,
						importGspGroup, importHhdcAccount,
						importSupplierAccount, importHasImportKwh,
						importHasImportKvarh, importHasExportKwh,
						importHasExportKvarh, importAgreedSupplyCapacity));
				mpans.add(getImportMpan());
			}
		} else {
			if (importMpanStr == null || importMpanStr.length() == 0) {
				mpans.remove(importMpan);
				setImportMpan(null);
			} else {
				importMpan.update(importMpanStr, importSsc, importGspGroup,
						importHhdcAccount, importSupplierAccount,
						importHasImportKwh, importHasImportKvarh,
						importHasExportKwh, importHasExportKvarh,
						importAgreedSupplyCapacity);
			}
		}
		if (exportMpan == null) {
			if (exportMpanStr != null && exportMpanStr.length() != 0) {
				setExportMpan(new Mpan(this, exportMpanStr, exportSsc,
						exportGspGroup, exportHhdcAccount,
						exportSupplierAccount, exportHasImportKwh,
						exportHasImportKvarh, exportHasExportKwh,
						exportHasExportKvarh, exportAgreedSupplyCapacity));
				mpans.add(getExportMpan());
			}
		} else {
			if (exportMpanStr == null || exportMpanStr.length() == 0) {
				mpans.remove(exportMpan);
				setExportMpan(null);
			} else {
				exportMpan.update(exportMpanStr, exportSsc, exportGspGroup,
						exportHhdcAccount, exportSupplierAccount,
						exportHasImportKwh, exportHasImportKvarh,
						exportHasExportKwh, exportHasExportKvarh,
						exportAgreedSupplyCapacity);
			}
		}
		if (importMpan == null && exportMpan == null) {
			throw new UserException(document(),
					"A supply generation must have at least one MPAN.");
		}
		if (importMpan != null) {
			if (!importMpan.getTop().getLlfc().getIsImport()) {
				throw new UserException(document(),
						"The import line loss factor '"
								+ importMpan.getTop().getLlfc()
								+ "' says that the MPAN is actually export.");
			}
		}
		if (exportMpan != null) {
			if (exportMpan.getTop().getLlfc().getIsImport()) {
				throw new UserException(
						"Problem with the export MPAN with core '"
								+ exportMpan.getCore()
								+ "'. The Line Loss Factor '"
								+ exportMpan.getTop().getLlfc()
								+ "' says that the MPAN is actually import.");
			}
		}
		if (importMpan != null && exportMpan != null) {
			if (importHhdcAccount != null
					&& exportHhdcAccount != null
					&& !importHhdcAccount.getContract().getId().equals(
							exportHhdcAccount.getContract().getId())) {
				throw new UserException(
						"The HHDC for the import and export MPANs must be the same.");
			}
			if (!importMpan.getCore().getDso().equals(
					exportMpan.getCore().getDso())) {
				throw new UserException(
						"Two MPAN generations on the same supply must have the same DSO.");
			}
			if (!importMpan.getTop().getLlfc().getVoltageLevel().equals(
					exportMpan.getTop().getLlfc().getVoltageLevel())) {
				throw new UserException(
						"The voltage level indicated by the Line Loss Factor must be the same for both the MPANs.");
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
			 * says that there should be an export MPAN, but there isn't one."); } }
			 */

			if (getExportMpan() != null && getImportMpan() != null) {
				int code = getImportMpan().getTop().getLlfc().getCode();
				if (code != 520 && code != 550 && code != 580) {
					throw new UserException(
							"The DSO is 22, there's an export MPAN and the Line Loss Factor of the import MPAN "
									+ getImportMpan()
									+ " can only be 520, 550 or 580.");
				}
			}
		}
		Hiber.flush();
		// more optimization possible here, doesn't necessarily need to check
		// data.
		synchronizeChannel(true, true);
		synchronizeChannel(true, false);
		synchronizeChannel(false, true);
		synchronizeChannel(false, false);
		getSupply().onSupplyGenerationChange(getStartDate(), getFinishDate());
		Hiber.flush();
	}

	private void synchronizeChannel(boolean isImport, boolean isKwh)
			throws HttpException {
		boolean importHasChannel = importMpan == null ? false : importMpan
				.hasChannel(isImport, isKwh);
		boolean exportHasChannel = exportMpan == null ? false : exportMpan
				.hasChannel(isImport, isKwh);
		if ((importHasChannel || exportHasChannel)
				&& getChannel(isImport, isKwh) == null) {
			insertChannel(isImport, isKwh);
		}
		if (!importHasChannel && !exportHasChannel
				&& getChannel(isImport, isKwh) != null) {
			deleteChannel(isImport, isKwh);
		}
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

	/*
	 * public Account getHhdcAccount(boolean isImport, boolean isKwh) throws
	 * HttpException { Account account = null; if (importMpan != null) { account =
	 * importMpan.getHhdcAccount(isImport, isKwh); } if (account == null &&
	 * exportMpan != null) { account = exportMpan.getHhdcAccount(isImport,
	 * isKwh); } return account; }
	 */
	public HhdcContract getHhdcContract() throws HttpException {
		for (Mpan mpan : getMpans()) {
			if (mpan.getHhdcAccount() != null) {
				return HhdcContract.getHhdcContract(mpan.getHhdcAccount()
						.getContract().getId());
			}
		}
		return null;
	}

	public MpanCore getMpanCore(boolean isImport, boolean isKwh)
			throws HttpException {
		MpanCore mpanCore = null;
		if (importMpan != null && importMpan.getHhdcAccount() != null) {
			mpanCore = importMpan.getCore();
		}
		if (mpanCore == null && exportMpan != null
				&& exportMpan.getHhdcAccount() != null) {
			mpanCore = exportMpan.getCore();
		}
		return mpanCore;
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
			Meter meter) throws HttpException {
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
		setMeter(meter);
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

	public void update(HhEndDate startDate, HhEndDate finishDate, Meter meter)
			throws HttpException {
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
					.getStartDate(), startDate.getPrevious(), meter);
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
							.getMeter());
		}
		internalUpdate(startDate, finishDate, meter);
		Hiber.flush();
		HhEndDate checkFinishDate = null;
		if (originalFinishDate != null && finishDate != null) {
			checkFinishDate = finishDate.getDate().after(
					originalFinishDate.getDate()) ? finishDate
					: originalFinishDate;
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
		for (Channel channel : channels) {
			element.appendChild(channel.toXml(doc));
		}
		return element;
	}

	Channel insertChannel(boolean isImport, boolean isKwh) throws HttpException {
		boolean hasAccount = false;
		for (Mpan mpan : getMpans()) {
			if (mpan.getHhdcAccount() != null) {
				hasAccount = true;
				break;
			}
		}
		if (!hasAccount) {
			throw new UserException(
					"You can't add a hh data channel to a supply generation if neither of the MPANs has an HHDC account.");
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
				"siteSupplyGenerations", new XmlTree("site")).put("meter").put(
				"supply", new XmlTree("source")));
		source.appendChild(generationElement);
		for (Mpan mpan : mpans) {
			Element mpanElement = (Element) mpan.toXml(doc, new XmlTree("core")
					.put(
							"top",
							new XmlTree("mtc").put("llfc").put("ssc").put(
									"gspGroup")).put("hhdcAccount",
							new XmlTree("contract", new XmlTree("party"))).put(
							"supplierAccount",
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
			/*
			 * for (InvoiceMpan invoiceMpan : (List<InvoiceMpan>) Hiber
			 * .session() .createQuery( "from InvoiceMpan invoiceMpan where
			 * invoiceMpan.mpan = :mpan") .setEntity("mpan", mpan).list()) {
			 * mpanElement.appendChild(invoiceMpan.toXml(doc, new XmlTree(
			 * "invoice", new XmlTree("batch", new XmlTree("service", new
			 * XmlTree("provider")))))); }
			 */
		}
		// Organization organization = organization();
		/*
		 * for (Dce dce : (List<Dce>) Hiber.session().createQuery( "from Dce
		 * dce where dce.organization = :organization")
		 * .setEntity("organization", organization).list()) { Element dceElement =
		 * dce.toXml(doc); source.appendChild(dceElement); for (HhdcContract
		 * dceService : (List<HhdcContract>) Hiber .session() .createQuery(
		 * "from DceService service where service.provider = :dce")
		 * .setEntity("dce", dce).list()) {
		 * dceElement.appendChild(dceService.toXml(doc)); } }
		 */
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
		return doc;
	}

	void deleteMpans() throws HttpException {
		for (Mpan mpan : mpans) {
			mpan.delete();
		}
		mpans.clear();
	}

	public void httpPost(Invocation inv) throws HttpException {
		try {
			if (inv.hasParameter("delete")) {
				supply.deleteGeneration(this);
				Hiber.commit();
				inv.sendSeeOther(supply.getUri());
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
				String importMpanStr = null;
				Ssc importSsc = null;
				GspGroup importGspGroup = null;
				Integer importAgreedSupplyCapacity = null;
				Date startDate = inv.getDate("start-date");
				Date finishDate = null;
				String meterSerialNumber = inv.getString("meter-serial-number");
				HhdcContract importHhdcContract = null;
				Account importHhdcAccount = null;
				SupplierContract importSupplierContract = null;
				Account importSupplierAccount = null;
				boolean importHasImportKwh = false;
				boolean importHasImportKvarh = false;
				boolean importHasExportKwh = false;
				boolean importHasExportKvarh = false;
				boolean isEnded = inv.getBoolean("is-ended");
				if (isEnded) {
					finishDate = inv.getDate("finish-date");
				}
				boolean hasImportMpan = inv.getBoolean("has-import-mpan");

				if (hasImportMpan) {
					String importMpanCoreStr = inv
							.getString("import-mpan-core");
					Long importPcId = inv.getLong("import-pc-id");
					String importLlfcCodeStr = inv
							.getString("import-llfc-code");
					String importMtcCode = inv.getString("import-mtc-code");
					String importSscCode = inv.getString("import-ssc-code");
					Long importGspGroupId = inv.getLong("import-gsp-group-id");
					if (!inv.isValid()) {
						throw new UserException(document());
					}
					Pc importPc = Pc.getPc(importPcId);
					if (importSscCode.trim().length() > 0) {
						importSsc = Ssc.getSsc(importSscCode);
					}
					importGspGroup = GspGroup.getGspGroup(importGspGroupId);
					importMpanStr = importPc.codeAsString() + importMtcCode
							+ importLlfcCodeStr + importMpanCoreStr;
					importAgreedSupplyCapacity = inv
							.getInteger("import-agreed-supply-capacity");
					importHasImportKwh = inv
							.getBoolean("import-has-import-kwh");
					importHasImportKvarh = inv
							.getBoolean("import-has-import-kvarh");
					importHasExportKwh = inv
							.getBoolean("import-has-export-kwh");
					importHasExportKvarh = inv
							.getBoolean("import-has-export-kvarh");
					if (importHasImportKwh || importHasImportKvarh
							|| importHasExportKwh || importHasExportKvarh) {
						String importHhdcContractName = inv
								.getString("import-hhdc-contract-name");
						if (importHhdcContractName.length() != 0) {
							importHhdcContract = HhdcContract
									.getHhdcContract(importHhdcContractName);
							String importHhdcAccountReference = inv
									.getString("import-hhdc-account-reference");
							importHhdcAccount = importHhdcContract
									.getAccount(importHhdcAccountReference);
						}
					}
					String importSupplierContractName = inv
							.getString("import-supplier-contract-name");
					importSupplierContract = SupplierContract
							.getSupplierContract(importSupplierContractName);
					String importSupplierAccountReference = inv
							.getString("import-supplier-account-reference");
					importSupplierAccount = importSupplierContract
							.getAccount(importSupplierAccountReference);
				}
				String exportMpanStr = null;
				Ssc exportSsc = null;
				GspGroup exportGspGroup = null;
				Integer exportAgreedSupplyCapacity = null;
				Account exportHhdcAccount = null;
				HhdcContract exportHhdcContract = null;
				Account exportSupplierAccount = null;
				SupplierContract exportSupplierContract = null;
				boolean exportHasImportKwh = false;
				boolean exportHasImportKvarh = false;
				boolean exportHasExportKwh = false;
				boolean exportHasExportKvarh = false;
				boolean hasExportMpan = inv.getBoolean("has-export-mpan");
				if (hasExportMpan) {
					String exportMpanCoreStr = inv
							.getString("export-mpan-core");
					Long exportPcId = inv.getLong("export-pc-id");
					String llfcCodeStr = inv.getString("export-llfc-code");
					String exportMtcCode = inv.getString("export-mtc-code");
					String exportSscCode = inv.getString("export-ssc-code");
					if (!inv.isValid()) {
						throw new UserException();
					}
					if (exportSscCode.trim().length() > 0) {
						exportSsc = Ssc.getSsc(exportSscCode);
					}
					Long exportGspGroupId = inv.getLong("export-gsp-group-id");
					Pc exportPc = Pc.getPc(exportPcId);
					exportMpanStr = exportPc.codeAsString() + exportMtcCode
							+ llfcCodeStr + exportMpanCoreStr;
					exportGspGroup = GspGroup.getGspGroup(exportGspGroupId);
					exportAgreedSupplyCapacity = inv
							.getInteger("export-agreed-supply-capacity");
					exportHasImportKwh = inv
							.getBoolean("export-has-import-kwh");
					exportHasImportKvarh = inv
							.getBoolean("export-has-import-kvarh");
					exportHasExportKwh = inv
							.getBoolean("export-has-export-kwh");
					exportHasExportKvarh = inv
							.getBoolean("export-has-export-kvarh");
					if (exportHasImportKwh || exportHasImportKvarh
							|| exportHasExportKwh || exportHasExportKvarh) {
						String exportHhdcContractName = inv
								.getString("export-hhdc-contract-name");
						if (exportHhdcContractName.length() != 0) {
							exportHhdcContract = HhdcContract
									.getHhdcContract(exportHhdcContractName);
							String exportHhdcAccountReference = inv
									.getString("export-hhdc-account-reference");
							exportHhdcAccount = exportHhdcContract
									.getAccount(exportHhdcAccountReference);
						}
					}
					String exportSupplierContractName = inv
							.getString("export-supplier-contract-name");
					exportSupplierContract = SupplierContract
							.getSupplierContract(exportSupplierContractName);
					String exportSupplierAccountReference = inv
							.getString("export-supplier-account-reference");
					exportSupplierAccount = exportSupplierContract
							.getAccount(exportSupplierAccountReference);
				}
				addOrUpdateMpans(importMpanStr, importSsc, importGspGroup,
						importHhdcAccount, importSupplierAccount,
						importHasImportKwh, importHasImportKvarh,
						importHasExportKwh, importHasExportKvarh,
						importAgreedSupplyCapacity, exportMpanStr, exportSsc,
						exportGspGroup, exportHhdcAccount,
						exportSupplierAccount, exportHasImportKwh,
						exportHasImportKvarh, exportHasExportKwh,
						exportHasExportKvarh, exportAgreedSupplyCapacity);
				Meter meter = null;
				if (meterSerialNumber != null
						&& meterSerialNumber.length() != 0) {
					meter = supply.findMeter(meterSerialNumber);
					if (meter == null) {
						meter = supply.insertMeter(meterSerialNumber);
					}
				}
				update(new HhEndDate(startDate), finishDate == null ? null
						: new HhEndDate(finishDate), meter);
				Hiber.commit();
				inv.sendOk(document());
			}
		} catch (HttpException e) {
			e.setDocument(document());
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

	/*
	 * public RegisterRead insertRegisterRead(RegisterReadRaw rawRegisterRead,
	 * Invoice invoice) throws HttpException { Mpan importMpan =
	 * getImportMpan(); Mpan exportMpan = getExportMpan(); RegisterRead read =
	 * null; if (importMpan != null &&
	 * importMpan.getMpanRaw().equals(rawRegisterRead.getMpanRaw())) { read =
	 * invoice.insertRead(importMpan, rawRegisterRead); } else if (exportMpan !=
	 * null && exportMpan.getMpanRaw().equals(rawRegisterRead.getMpanRaw())) {
	 * read = invoice.insertRead(exportMpan, rawRegisterRead); } else { throw
	 * new UserException("For the supply " + getId() + " neither the import MPAN " +
	 * importMpan + " or the export MPAN " + exportMpan + " match the register
	 * read MPAN " + rawRegisterRead.getMpanRaw() + "."); } return read; }
	 */
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
	 * @SuppressWarnings("unchecked") private void resolveChannelSnags(String
	 * description, HhEndDate from, HhEndDate to) throws HttpException { for
	 * (Channel channel : (List<Channel>) Hiber .session() .createQuery( "from
	 * Channel channel where channel.supplyGeneration.supply = :supply and
	 * channel.supplyGeneration.fromDate <= :to and
	 * channel.supplyGeneration.toDate >= :from")) {
	 * channel.resolveSnag(description, from, to); } }
	 */
	/*
	 * @SuppressWarnings("unchecked") private void resolveChannelSnags(boolean
	 * isImport, boolean isKwh, String description, HhEndDate from, HhEndDate
	 * to) throws HttpException { for (Channel channel : (List<Channel>) Hiber
	 * .session() .createQuery( "from Channel channel where
	 * channel.supplyGeneration.supply = :supply and channel.isImport =
	 * :isImport and channel.isKwh = :isKwh and
	 * channel.supplyGeneration.fromDate <= :to and
	 * channel.supplyGeneration.toDate >= :from") .setEntity("supply",
	 * this).setBoolean("isImport", isImport) .setBoolean("isKwh", isKwh)
	 * .setTimestamp("from", from.getDate()).setTime("to", to.getDate()).list()) {
	 * channel.resolveSnag(description, from, to); } }
	 */

	public void checkForMissing(HhEndDate from, HhEndDate to)
			throws HttpException {
		for (Channel channel : channels) {
			channel.checkForMissing(from, to);
		}
	}

	public void checkForMissingFromLatest(HhEndDate to) throws HttpException {
		for (Channel channel : channels) {
			channel.checkForMissingFromLatest(to);
		}
	}

	/*
	 * private void checkForMissing(HhEndDate from, HhEndDate to) throws
	 * HttpException { if (from == null) { from = getStartDate(); } if
	 * (from.getDate() .before(getStartDate().getDate())) {
	 * resolveChannelSnags(ChannelSnag.SNAG_MISSING, from,
	 * getStartDate().getPrevious()); from = getStartDate(); } if (to == null) {
	 * to = getCheckToDate(isImport, isKwh); } Calendar cal =
	 * MonadDate.getCalendar(); HhEndDate lastGenerationDate =
	 * getGenerationLast().getFinishDate(); if (lastGenerationDate != null &&
	 * to.getDate().after(lastGenerationDate.getDate())) {
	 * resolveChannelSnags(isImport, isKwh, ChannelSnag.SNAG_MISSING,
	 * lastGenerationDate.getNext(), to); to = lastGenerationDate; } if
	 * (from.getDate().after(to.getDate())) { return; }
	 * 
	 * Query query = Hiber .session() .createQuery( "select count(*) from
	 * HhDatum datum where datum.channel = :channel and datum.endDate.date >=
	 * :startDate and datum.endDate.date <= :finishDate") .setEntity("channel",
	 * this); List<SupplyGeneration> generations = getGenerations(from, to);
	 * for (int i = 0; i < generations.size(); i++) { SupplyGeneration
	 * generation = generations.get(i); Channel channel =
	 * generation.getChannel(isImport, isKwh); if (channel == null) { continue; }
	 * HhdcContract hhdcContract = generation.getHhdcContract(); HhEndDate
	 * generationStartDate = i == 0 ? from : generations.get(i) .getStartDate();
	 * HhEndDate generationFinishDate = i == generations.size() - 1 ? to :
	 * generation.getFinishDate(); if (hhdcContract == null) {
	 * channel.resolveSnag(ChannelSnag.SNAG_MISSING, generationStartDate,
	 * generationFinishDate); } else { HhEndDate spanStartDate =
	 * generationStartDate; HhEndDate spanFinishDate = generationFinishDate;
	 * 
	 * boolean finished = false; while (!finished) { long present = (Long)
	 * query.setTimestamp("startDate",
	 * spanStartDate.getDate()).setTimestamp("finishDate",
	 * spanFinishDate.getDate()).uniqueResult(); if (present == 0) {
	 * channel.addChannelSnag(ChannelSnag.SNAG_MISSING, spanStartDate,
	 * spanFinishDate, false); spanStartDate =
	 * HhEndDate.getNext(spanFinishDate); spanFinishDate = generationFinishDate;
	 * if (spanStartDate.getDate().after( spanFinishDate.getDate())) { finished =
	 * true; } } else { long shouldBe = (long) (spanFinishDate.getDate()
	 * .getTime() - spanStartDate.getDate().getTime() + 1000 * 60 * 30) / (1000 *
	 * 60 * 30); if (present == shouldBe) { spanStartDate =
	 * HhEndDate.getNext(spanFinishDate); spanFinishDate = generationFinishDate;
	 * if (spanStartDate.getDate().after( spanFinishDate.getDate())) { finished =
	 * true; } } else { spanFinishDate = new HhEndDate(new Date(HhEndDate
	 * .roundDown(cal, spanStartDate.getDate() .getTime() +
	 * (spanFinishDate.getDate() .getTime() - spanStartDate
	 * .getDate().getTime()) / 2))); } } } } } }
	 */
}