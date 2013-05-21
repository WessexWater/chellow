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
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import org.hibernate.Query;
import org.hibernate.ScrollableResults;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.GeneralImport;
import java.math.BigDecimal;

public class Era extends PersistentEntity {

	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("update")) {
			String mpanCore = GeneralImport.addField(csvElement, "MPAN Core",
					values, 0);
			mpanCore = Era.normalizeMpanCore(mpanCore);
			String dateStr = GeneralImport.addField(csvElement, "Date", values,
					1);
			Supply supply = Supply.getSupply(mpanCore);
			Era era = supply.getEra(dateStr.length() == 0 ? null
					: new HhStartDate(dateStr));

			if (era == null) {
				throw new UserException("There isn't an era at this date.");
			}
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 2);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish date", values, 3);
			Contract mopContract = null;
			String mopContractName = GeneralImport.addField(csvElement,
					"MOP Contract", values, 4);
			if (mopContractName.equals(GeneralImport.NO_CHANGE)) {
				mopContract = era.getMopContract();
			} else {
				mopContract = Contract.getMopContract(mopContractName);
			}
			String mopAccount = GeneralImport.addField(csvElement,
					"MOP Account", values, 5);
			if (mopAccount.equals(GeneralImport.NO_CHANGE)) {
				mopAccount = era.getMopAccount();
			}
			Contract hhdcContract = null;
			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 6);
			if (hhdcContractName.equals(GeneralImport.NO_CHANGE)) {
				hhdcContract = era.getHhdcContract();
			} else {
				hhdcContract = Contract.getHhdcContract(hhdcContractName);
			}
			String hhdcAccount = GeneralImport.addField(csvElement,
					"HHDC account", values, 7);
			if (hhdcAccount.equals(GeneralImport.NO_CHANGE)) {
				hhdcAccount = era.getHhdcAccount();
			}
			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh?", values, 8);
			boolean hasImportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? era.getChannel(true,
					true) != null : Boolean.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh?", values, 9);
			boolean hasImportKvarh = hasImportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? era.getChannel(true,
					false) != null : Boolean.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh?", values, 10);
			boolean hasExportKwh = hasExportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? era.getChannel(false,
					true) != null : Boolean.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh?", values, 11);
			boolean hasExportKvarh = hasExportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? era.getChannel(false,
					false) != null : Boolean.parseBoolean(hasExportKvarhStr);
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
					if (hasChannel && era.getChannel(isImport, isKwh) == null) {
						era.insertChannel(isImport, isKwh);
					}
					if (!hasChannel && era.getChannel(isImport, isKwh) != null) {
						era.deleteChannel(isImport, isKwh);
					}
				}
			}
			String msn = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 12);
			if (msn.equals(GeneralImport.NO_CHANGE)) {
				msn = era.getMsn();
			}
			String pcCode = GeneralImport.addField(csvElement, "Profile Class",
					values, 13);
			Pc pc = null;
			if (pcCode.equals(GeneralImport.NO_CHANGE)) {
				pc = era.getPc();
			} else {
				pc = Pc.getPc(pcCode);
			}

			String mtcCode = GeneralImport.addField(csvElement,
					"Meter Timeswitch Class", values, 14);
			if (mtcCode.equals(GeneralImport.NO_CHANGE)) {
				mtcCode = era.getMtc().toString();
			}

			String copCode = GeneralImport.addField(csvElement, "CoP", values,
					15);
			Cop cop = null;
			if (pcCode.equals(GeneralImport.NO_CHANGE)) {
				cop = era.getCop();
			} else {
				cop = Cop.getCop(copCode);
			}

			Ssc ssc = null;
			String sscCode = GeneralImport.addField(csvElement, "SSC", values,
					16);
			if (sscCode.equals(GeneralImport.NO_CHANGE)) {
				ssc = era.getSsc();
			} else {
				ssc = sscCode.length() == 0 ? null : Ssc.getSsc(sscCode);
			}

			String impMpanCore = GeneralImport.addField(csvElement,
					"Import MPAN Core", values, 17);
			String impLlfcCode = null;
			Integer impSc = null;
			Contract impSupplierContract = null;
			String impSupplierAccount = null;
			if (impMpanCore.equals(GeneralImport.NO_CHANGE)) {
				impMpanCore = era.getImpMpanCore();
			} else if (impMpanCore.length() == 0) {
				impMpanCore = null;
			}
			if (impMpanCore != null) {
				impLlfcCode = GeneralImport.addField(csvElement, "Import LLFC",
						values, 18);
				if (impLlfcCode.equals(GeneralImport.NO_CHANGE)) {
					impLlfcCode = era.getImpMpanCore() == null ? null : era
							.getImpLlfc().getCode();
				}
				String impScStr = GeneralImport.addField(csvElement,
						"Import Agreed Supply Capacity", values, 19);
				if (impScStr.equals(GeneralImport.NO_CHANGE)) {
					impSc = era.getImpSc();
				} else {
					try {
						impSc = Integer.parseInt(impScStr);
					} catch (NumberFormatException e) {
						throw new UserException(
								"The import agreed supply capacity must be an integer. "
										+ e.getMessage());
					}
				}
				String impSupplierContractName = GeneralImport.addField(
						csvElement, "Import Supplier Contract", values, 20);
				if (impSupplierContractName.equals(GeneralImport.NO_CHANGE)) {
					impSupplierContract = era.getImpSupplierContract();
				} else {
					impSupplierContract = Contract
							.getSupplierContract(impSupplierContractName);
				}
				impSupplierAccount = GeneralImport.addField(csvElement,
						"Import Supplier Account", values, 21);
				if (impSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
					impSupplierAccount = era.getImpSupplierAccount();
				}
			}
			String expMpanCore = null;
			String expLlfcCode = null;
			Contract expSupplierContract = null;
			String expSupplierAccount = null;
			Integer expSc = null;
			if (values.length > 22) {
				expMpanCore = GeneralImport.addField(csvElement,
						"Eport MPAN Core", values, 22);
				if (expMpanCore.equals(GeneralImport.NO_CHANGE)) {
					expMpanCore = era.getExpMpanCore();
				} else if (expMpanCore.length() == 0) {
					expMpanCore = null;
				}
				if (expMpanCore != null) {
					expLlfcCode = GeneralImport.addField(csvElement,
							"Export LLFC", values, 23);
					if (expLlfcCode.equals(GeneralImport.NO_CHANGE)) {
						expLlfcCode = era.getExpMpanCore() == null ? null : era
								.getExpLlfc().getCode();
					}
					String expScStr = GeneralImport.addField(csvElement,
							"Export Agreed Supply Capacity", values, 24);
					if (expScStr.equals(GeneralImport.NO_CHANGE)) {
						expSc = era.getExpSc();
					} else {
						try {
							expSc = new Integer(expScStr);
						} catch (NumberFormatException e) {
							throw new UserException(
									"The export supply capacity must be an integer. "
											+ e.getMessage());
						}
					}
					String expSupplierContractName = GeneralImport.addField(
							csvElement, "Export Supplier Contract", values, 25);
					if (expSupplierContractName.equals(GeneralImport.NO_CHANGE)) {
						expSupplierContract = era.getExpSupplierContract();
					} else {
						expSupplierContract = Contract
								.getSupplierContract(expSupplierContractName);
					}
					expSupplierAccount = GeneralImport.addField(csvElement,
							"Export Supplier Account", values, 26);
					if (expSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
						expSupplierAccount = era.getExpSupplierAccount();
					}
				}
			}
			supply.updateEra(
					era,
					startDateStr.equals(GeneralImport.NO_CHANGE) ? era
							.getStartDate() : new HhStartDate(startDateStr),
					finishDateStr.length() == 0 ? null : (finishDateStr
							.equals(GeneralImport.NO_CHANGE) ? era
							.getFinishDate() : new HhStartDate(finishDateStr)),
					mopContract, mopAccount, hhdcContract, hhdcAccount, msn,
					pc, mtcCode, cop, ssc, impMpanCore, impLlfcCode,
					impSupplierContract, impSupplierAccount, impSc,
					expMpanCore, expLlfcCode, expSupplierContract,
					expSupplierAccount, expSc);
		} else if (action.equals("delete")) {
			String mpanCore = GeneralImport.addField(csvElement, "MPAN Core",
					values, 0);
			String dateStr = GeneralImport.addField(csvElement, "Date", values,
					1);

			Era era = Era.getEra(mpanCore, dateStr.length() == 0 ? null
					: new HhStartDate(dateStr));
			if (era == null) {
				throw new UserException("There isn't an era at this date.");
			}
			era.getSupply().deleteEra(era);
		} else if (action.equals("insert")) {
			String mpanCore = GeneralImport.addField(csvElement, "MPAN Core",
					values, 0);
			String startDateStr = GeneralImport.addField(csvElement,
					"Start date", values, 1);
			HhStartDate startDate = startDateStr.length() == 0 ? null
					: new HhStartDate(startDateStr);
			Supply supply = Supply.getSupply(mpanCore);
			Era existingEra = supply.getEra(startDate);
			if (existingEra == null) {
				Era firstEra = supply.getEraFirst();
				if (startDate.before(firstEra.getStartDate())) {
					existingEra = firstEra;
				}
			}
			if (existingEra == null) {
				throw new UserException(
						"The start date is after end of the supply.");
			}

			String siteCode = GeneralImport.addField(csvElement, "Site Code",
					values, 2);
			Site physicalSite = null;
			List<Site> logicalSites = new ArrayList<Site>();
			if (siteCode.equals(GeneralImport.NO_CHANGE)) {
				for (SiteEra ssgen : existingEra.getSiteEras()) {
					if (ssgen.getIsPhysical()) {
						physicalSite = ssgen.getSite();
					} else {
						logicalSites.add(ssgen.getSite());
					}
				}
			} else {
				physicalSite = Site.getSite(siteCode);
			}

			String mopContractName = GeneralImport.addField(csvElement,
					"MOP Contract", values, 3);
			Contract mopContract = null;
			if (mopContractName.equals(GeneralImport.NO_CHANGE)) {
				mopContract = existingEra.getMopContract();
			} else if (mopContractName.length() > 0) {
				mopContract = Contract.getMopContract(mopContractName);
			}
			String mopAccount = GeneralImport.addField(csvElement,
					"MOP Account Reference", values, 4);
			if (mopAccount.equals(GeneralImport.NO_CHANGE)) {
				mopAccount = existingEra.getMopAccount();
			}

			String hhdcContractName = GeneralImport.addField(csvElement,
					"HHDC Contract", values, 5);
			Contract hhdcContract = null;
			if (hhdcContractName.equals(GeneralImport.NO_CHANGE)) {
				hhdcContract = existingEra.getHhdcContract();
			} else if (hhdcContractName.length() > 0) {
				hhdcContract = Contract.getHhdcContract(hhdcContractName);
			}
			String hhdcAccount = GeneralImport.addField(csvElement,
					"HHDC Account Reference", values, 6);
			if (hhdcAccount.equals(GeneralImport.NO_CHANGE)) {
				hhdcAccount = existingEra.getHhdcAccount();
			}

			String hasImportKwhStr = GeneralImport.addField(csvElement,
					"Has HH import kWh", values, 7);
			boolean hasImportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? existingEra.getChannel(
					true, true) != null : Boolean.parseBoolean(hasImportKwhStr);
			String hasImportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH import kVArh", values, 8);
			boolean hasImportKvarh = hasImportKvarhStr
					.equals(GeneralImport.NO_CHANGE) ? existingEra.getChannel(
					true, false) != null : Boolean
					.parseBoolean(hasImportKvarhStr);
			String hasExportKwhStr = GeneralImport.addField(csvElement,
					"Has HH export kWh", values, 9);
			boolean hasExportKwh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? existingEra.getChannel(
					false, true) != null : Boolean
					.parseBoolean(hasExportKwhStr);
			String hasExportKvarhStr = GeneralImport.addField(csvElement,
					"Has HH export kVArh", values, 10);
			boolean hasExportKvarh = hasImportKwhStr
					.equals(GeneralImport.NO_CHANGE) ? existingEra.getChannel(
					false, false) != null : Boolean
					.parseBoolean(hasExportKvarhStr);

			String msn = GeneralImport.addField(csvElement,
					"Meter Serial Number", values, 11);
			if (msn.equals(GeneralImport.NO_CHANGE)) {
				msn = existingEra.getMsn();
			}

			String pcStr = GeneralImport.addField(csvElement, "Profile Class",
					values, 12);
			Pc pc = null;

			if (pcStr.equals(GeneralImport.NO_CHANGE)) {
				pc = existingEra.getPc();
			} else {
				pc = Pc.getPc(pcStr);
			}

			String mtcCode = GeneralImport.addField(csvElement,
					"Meter Timeswitch Class", values, 13);
			if (mtcCode.equals(GeneralImport.NO_CHANGE)) {
				mtcCode = existingEra.getMtc().toString();
			}

			Cop cop = null;
			String copStr = GeneralImport.addField(csvElement, "CoP", values,
					14);
			if (copStr.equals(GeneralImport.NO_CHANGE)) {
				cop = existingEra.getCop();
			} else {
				cop = Cop.getCop(copStr);
			}

			Ssc ssc = null;
			String sscCode = GeneralImport.addField(csvElement,
					"Standard Settlement Configuration", values, 15);
			if (sscCode.equals(GeneralImport.NO_CHANGE)) {
				ssc = existingEra.getSsc();
			} else if (sscCode.length() > 0) {
				ssc = Ssc.getSsc(sscCode);
			}

			String impMpanCore = GeneralImport.addField(csvElement,
					"Import MPAN Core", values, 16);
			if (impMpanCore.equals(GeneralImport.NO_CHANGE)) {
				impMpanCore = existingEra.getImpMpanCore();
			} else if (impMpanCore.length() == 0) {
				impMpanCore = null;
			}

			Contract impSupplierContract = null;
			String impSupplierAccount = null;
			Integer impSc = null;
			String impLlfcCode = null;
			String impScStr = null;

			if (impMpanCore != null) {
				impLlfcCode = GeneralImport.addField(csvElement,
						"Import Line Loss Factor Class", values, 17);
				if (impLlfcCode.equals(GeneralImport.NO_CHANGE)) {
					if (existingEra.getImpMpanCore() == null) {
						throw new UserException(
								"There ins't an existing import MPAN.");
					} else {
						impLlfcCode = existingEra.getImpLlfc().getCode();
					}
				}
				impScStr = GeneralImport.addField(csvElement,
						"Import Agreed Supply Capacity", values, 18);
				if (impScStr.equals(GeneralImport.NO_CHANGE)) {
					impSc = existingEra.getImpSc();
				} else {
					try {
						impSc = Integer.parseInt(impScStr);
					} catch (NumberFormatException e) {
						throw new UserException(
								"The import agreed supply capacity must be an integer. "
										+ e.getMessage());
					}
				}
				String impSupplierContractName = GeneralImport.addField(
						csvElement, "Import Supplier Contract", values, 19);
				if (impSupplierContractName.equals(GeneralImport.NO_CHANGE)) {
					impSupplierContract = existingEra.getImpSupplierContract();
				} else {
					impSupplierContract = Contract
							.getSupplierContract(impSupplierContractName);
				}
				impSupplierAccount = GeneralImport.addField(csvElement,
						"Import Supplier Account Reference", values, 20);
				if (impSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
					impSupplierAccount = existingEra.getImpSupplierAccount();
				}
			}

			String expMpanCore = null;
			String expLlfcCode = null;
			Contract expSupplierContract = null;
			String expSupplierAccount = null;
			Integer expSc = null;

			if (values.length > 21) {
				expMpanCore = GeneralImport.addField(csvElement, "Export MPAN",
						values, 21);
				if (expMpanCore.equals(GeneralImport.NO_CHANGE)) {
					expMpanCore = existingEra.getExpMpanCore();
				} else if (expMpanCore.length() == 0) {
					expMpanCore = null;
				}

				if (expMpanCore != null) {
					expLlfcCode = GeneralImport.addField(csvElement,
							"Export LLFC", values, 22);
					if (expLlfcCode.equals(GeneralImport.NO_CHANGE)) {
						if (existingEra.getExpMpanCore() == null) {
							throw new UserException(
									"There isn't an existing export MPAN.");
						} else {
							expLlfcCode = existingEra.getExpLlfc().getCode();
						}
					}

					String expScStr = GeneralImport.addField(csvElement,
							"Export Agreed Supply Capacity", values, 23);
					if (expScStr.equals(GeneralImport.NO_CHANGE)) {
						expSc = existingEra.getExpSc();
					} else {
						try {
							expSc = new Integer(expScStr);
						} catch (NumberFormatException e) {
							throw new UserException(
									"The export supply capacity must be an integer. "
											+ e.getMessage());
						}
					}

					String expSupplierContractName = GeneralImport.addField(
							csvElement, "Export Supplier Contract", values, 24);
					if (expSupplierContractName.equals(GeneralImport.NO_CHANGE)) {
						expSupplierContract = existingEra
								.getExpSupplierContract();
					} else {
						expSupplierContract = Contract
								.getSupplierContract(expSupplierContractName);
					}
					expSupplierAccount = GeneralImport.addField(csvElement,
							"Export Supplier Account", values, 25);
					if (expSupplierAccount.equals(GeneralImport.NO_CHANGE)) {
						expSupplierAccount = existingEra
								.getExpSupplierAccount();
					}
				}
			}
			supply.insertEra(physicalSite, logicalSites, startDate,
					mopContract, mopAccount, hhdcContract, hhdcAccount, msn,
					pc, mtcCode, cop, ssc, impMpanCore, impLlfcCode,
					impSupplierContract, impSupplierAccount, impSc,
					expMpanCore, expLlfcCode, expSupplierContract,
					expSupplierAccount, expSc, hasImportKwh, hasImportKvarh,
					hasExportKwh, hasExportKvarh);
		}
	}

	static public Era getEra(String mpanCore, HhStartDate date) {
		if (date == null) {
			return (Era) Hiber
					.session()
					.createQuery(
							"from Era era where (era.impMpanCore = :mpanCore or era.expMpanCore = :mpanCore) and era.finishDate is null)")
					.setString("mpanCore", mpanCore).uniqueResult();
		} else {
			return (Era) Hiber
					.session()
					.createQuery(
							"from Era era where (era.impMpanCore = :mpanCore or era.expMpanCore = :mpanCore) and era.startDate.date <= :date and (era.finishDate.date >= :date or era.finishDate.date is null)")
					.setString("mpanCore", mpanCore)
					.setTimestamp("date", date.getDate()).uniqueResult();
		}
	}

	static public String normalizeMpanCore(String core) {
		core = core.replace(" ", "");
		if (core.length() != 13) {
			throw new UserException("The MPAN core (" + core
					+ ") must contain exactly 13 digits.");
		}
		for (char ch : core.toCharArray()) {
			if (!Character.isDigit(ch)) {
				throw new UserException(
						"Each character of an MPAN must be a digit.");
			}
		}

		int[] primes = { 3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43 };
		int sum = 0;
		for (int i = 0; i < primes.length; i++) {
			sum += Character.getNumericValue(core.charAt(i)) * primes[i];
		}
		int checkInt = sum % 11 % 10;
		int actualCheck = Character.getNumericValue(core.charAt(12));
		if (checkInt != actualCheck) {
			throw new UserException("The check digit is incorrect.");
		}
		return core.substring(0, 2) + " " + core.substring(2, 6) + " "
				+ core.substring(6, 10) + " " + core.substring(10, 13);
	}

	private Supply supply;

	private Set<SiteEra> siteEras;

	private Set<Channel> channels;

	private HhStartDate startDate;

	private HhStartDate finishDate;
	private Contract mopContract;
	private String mopAccount;

	private Contract hhdcContract;
	private String hhdcAccount;
	private String msn;
	private Pc pc;
	private Mtc mtc;
	private Cop cop;
	private Ssc ssc;
	private Llfc impLlfc;
	private Integer impSc;
	private Contract impSupplierContract;
	private String impSupplierAccount;
	private String impMpanCore;
	private String expMpanCore;
	private Llfc expLlfc;
	private Integer expSc;
	private Contract expSupplierContract;
	private String expSupplierAccount;

	Era() {
	}

	Era(Supply supply, HhStartDate startDate, HhStartDate finishDate,
			Contract mopContract, String mopAccount, Contract hhdcContract,
			String hhdcAccount, String msn, Pc pc, String mtcCode, Cop cop,
			Ssc ssc) throws HttpException {
		setChannels(new HashSet<Channel>());
		setSupply(supply);
		setSiteEras(new HashSet<SiteEra>());
		setPc(pc);
		Mtc anMtc = (Mtc) Hiber.session()
				.createQuery("from Mtc mtc where mtc.code = :code")
				.setInteger("code", Integer.parseInt(mtcCode)).setMaxResults(1)
				.uniqueResult();
		if (anMtc == null) {
			throw new UserException("MTC not recognized.");
		}
		setMtc(anMtc);
		setCop(cop);
		setSsc(ssc);
		setStartDate(startDate);
		setFinishDate(finishDate);
		setMopContract(mopContract);
		setMopAccount(mopAccount);
		setHhdcContract(hhdcContract);
		setHhdcAccount(hhdcAccount);
		setMsn(msn);
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Supply getSupply() {
		return supply;
	}

	public Set<SiteEra> getSiteEras() {
		return siteEras;
	}

	protected void setSiteEras(Set<SiteEra> siteEras) {
		this.siteEras = siteEras;
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

	public Contract getMopContract() {
		return mopContract;
	}

	void setMopContract(Contract mopContract) {
		this.mopContract = mopContract;
	}

	public String getMopAccount() {
		return mopAccount;
	}

	void setMopAccount(String mopAccount) {
		this.mopAccount = mopAccount;
	}

	public Contract getHhdcContract() {
		return hhdcContract;
	}

	void setHhdcContract(Contract hhdcContract) {
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

	public String getMsn() {
		return msn;
	}

	void setMsn(String msn) {
		this.msn = msn;
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

	public Set<Channel> getChannels() {
		return channels;
	}

	void setChannels(Set<Channel> channels) {
		this.channels = channels;
	}

	public String getImpMpanCore() {
		return impMpanCore;
	}

	public void setImpMpanCore(String impMpanCore) {
		this.impMpanCore = impMpanCore;
	}

	public String getExpMpanCore() {
		return expMpanCore;
	}

	public void setExpMpanCore(String expMpanCore) {
		this.expMpanCore = expMpanCore;
	}

	public Llfc getImpLlfc() {
		return impLlfc;
	}

	public void setImpLlfc(Llfc impLlfc) {
		this.impLlfc = impLlfc;
	}

	public Integer getImpSc() {
		return impSc;
	}

	public void setImpSc(Integer impSc) {
		this.impSc = impSc;
	}

	public Contract getImpSupplierContract() {
		return impSupplierContract;
	}

	public void setImpSupplierContract(Contract impSupplierContract) {
		this.impSupplierContract = impSupplierContract;
	}

	public String getImpSupplierAccount() {
		return impSupplierAccount;
	}

	public void setImpSupplierAccount(String impSupplierAccount) {
		this.impSupplierAccount = impSupplierAccount;
	}

	public Llfc getExpLlfc() {
		return expLlfc;
	}

	public void setExpLlfc(Llfc expLlfc) {
		this.expLlfc = expLlfc;
	}

	public Integer getExpSc() {
		return expSc;
	}

	public void setExpSc(Integer expSc) {
		this.expSc = expSc;
	}

	public Contract getExpSupplierContract() {
		return expSupplierContract;
	}

	public void setExpSupplierContract(Contract expSupplierContract) {
		this.expSupplierContract = expSupplierContract;
	}

	public String getExpSupplierAccount() {
		return expSupplierAccount;
	}

	public void setExpSupplierAccount(String expSupplierAccount) {
		this.expSupplierAccount = expSupplierAccount;
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

	public void attachSite(Site site) throws HttpException {
		attachSite(site, false);
	}

	public void attachSite(Site site, boolean isLocation) throws HttpException {
		boolean alreadyThere = false;
		for (SiteEra siteEra : siteEras) {
			if (siteEra.getSite().equals(site)) {
				alreadyThere = true;
				break;
			}
		}
		if (alreadyThere) {
			throw new UserException(
					"The site is already attached to this supply.");
		} else {
			SiteEra siteEra = new SiteEra(site, this, false);
			siteEras.add(siteEra);
			site.attachSiteEra(siteEra);
		}
		if (isLocation) {
			setPhysicalLocation(site);
		}
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getEditUri() throws HttpException {
		return supply.getErasInstance().getEditUri().resolve(getUriId())
				.append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Channels.URI_ID.equals(uriId)) {
			return new Channels(this);
		} else {
			throw new NotFoundException();
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "era");
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		if (hhdcAccount != null) {
			element.setAttribute("hhdc-account", hhdcAccount);
		}
		if (mopAccount != null) {
			element.setAttribute("mop-account", mopAccount);
		}
		element.setAttribute("msn", msn);
		if (impMpanCore != null) {
			element.setAttribute("imp-mpan-core", impMpanCore);
			Element supElem = impSupplierContract.toXml(doc);
			element.appendChild(supElem);
			supElem.setAttribute("is-import", Boolean.TRUE.toString());
			element.setAttribute("imp-supplier-account", impSupplierAccount);
			element.setAttribute("imp-sc", Integer.toString(impSc));
		}
		if (expMpanCore != null) {
			element.setAttribute("exp-mpan-core", expMpanCore);
			Element supElem = expSupplierContract.toXml(doc);
			element.appendChild(supElem);
			supElem.setAttribute("is-import", Boolean.FALSE.toString());
			element.setAttribute("exp-supplier-account", expSupplierAccount);
			element.setAttribute("exp-sc", Integer.toString(expSc));
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
		channel.addSnag(Snag.SNAG_MISSING, getStartDate(), getFinishDate());
		return channel;
	}

	public void update(HhStartDate startDate, HhStartDate finishDate,
			Contract mopContract, String mopAccount, Contract hhdcContract,
			String hhdcAccount, String msn, Pc pc, String mtcCode, Cop cop,
			Ssc ssc) throws HttpException {
		String impLlfcCode = null;
		String expLlfcCode = null;
		if (impMpanCore != null) {
			impLlfcCode = impLlfc.getCode();
		}
		if (expMpanCore != null) {
			expLlfcCode = expLlfc.getCode();
		}
		update(startDate, finishDate, mopContract, mopAccount, hhdcContract,
				hhdcAccount, msn, pc, mtcCode, cop, ssc, impMpanCore,
				impLlfcCode, impSupplierContract, impSupplierAccount, impSc,
				expMpanCore, expLlfcCode, expSupplierContract,
				expSupplierAccount, expSc);
	}

	public void update(HhStartDate startDate, HhStartDate finishDate)
			throws HttpException {
		if (startDate.equals(this.startDate)
				&& HhStartDate.isEqual(finishDate, this.finishDate)) {
			return;
		} else {
			update(startDate, finishDate, mopContract, mopAccount,
					hhdcContract, hhdcAccount, msn, pc, mtc.toString(), cop,
					ssc);
		}
	}

	public void update(HhStartDate startDate, HhStartDate finishDate,
			Contract mopContract, String mopAccount, Contract hhdcContract,
			String hhdcAccount, String msn, Pc pc, String mtcCode, Cop cop,
			Ssc ssc, String impMpanCore, String impLlfcCode,
			Contract impSupplierContract, String impSupplierAccount,
			Integer impSc, String expMpanCore, String expLlfcCode,
			Contract expSupplierContract, String expSupplierAccount,
			Integer expSc) throws HttpException {
		if (startDate.after(finishDate)) {
			throw new UserException(
					"The era start date can't be after the finish date.");
		}
		Era previousEra = (Era) Hiber
				.session()
				.createQuery(
						"from Era era where era.supply = :supply and era != :era and era.startDate.date < :startDate order by era.startDate.date desc")
				.setEntity("supply", supply).setEntity("era", this)
				.setTimestamp("startDate", startDate.getDate())
				.setMaxResults(1).uniqueResult();
		Era nextEra = null;
		if (finishDate != null) {
			nextEra = (Era) Hiber
					.session()
					.createQuery(
							"from Era era where era.supply = :supply and era != :era and era.startDate.date > :startDate order by era.startDate.date")
					.setEntity("supply", supply).setEntity("era", this)
					.setTimestamp("startDate", startDate.getDate())
					.setMaxResults(1).uniqueResult();
		}

		setMsn(msn);
		setPc(pc);
		setSsc(ssc);

		if (impMpanCore == null) {
			setImpMpanCore(null);
			if (impLlfcCode != null) {
				throw new UserException(
						"If the import MPAN core is null, the import LLFC must also be null.");
			}
			setImpLlfc(null);
			if (impSupplierContract != null) {
				throw new UserException(
						"If the import MPAN core is null, the import supplier contract must also be null.");
			}
			setImpSupplierContract(null);
			if (impSupplierAccount != null) {
				throw new UserException(
						"If the import MPAN core is null, the import supplier account must also be null.");
			}
			setImpSupplierAccount(null);
			if (impSc != null) {
				throw new UserException(
						"If the import MPAN core is null, the import supply capacity must also be null.");
			}
			setImpSc(null);
		} else {
			impMpanCore = normalizeMpanCore(impMpanCore);
			if (!impMpanCore.substring(0, 2).equals(
					supply.getDnoContract().getParty().getDnoCode())) {
				throw new UserException(
						"The DNO of the import MPAN core must match the supply's DNO.");
			}
			setImpMpanCore(impMpanCore);
			if (impLlfcCode == null) {
				throw new UserException(
						"If the import MPAN core is present, the import LLFC must also be present.");
			}
			setImpLlfc(Llfc.getLlfc(supply.getDnoContract(), impLlfcCode));
			if (!getImpLlfc().getIsImport()) {
				throw new UserException(document(),
						"The import line loss factor '" + getImpLlfc()
								+ "' says that the MPAN is actually export.");
			}
			if (impSupplierContract == null) {
				throw new UserException(
						"If the import MPAN core is present, the import supplier contract must also be present.");
			}
			setImpSupplierContract(impSupplierContract);
			if (impSupplierAccount == null) {
				throw new UserException(
						"If the import MPAN core is present, the import supplier account must also be present.");
			}
			setImpSupplierAccount(impSupplierAccount);
			if (impSupplierContract.getStartRateScript().getStartDate()
					.after(startDate)) {
				throw new UserException(
						"The import supplier contract starts after the supply era.");
			}
			if (HhStartDate.isBefore(impSupplierContract.getFinishRateScript()
					.getFinishDate(), finishDate)) {
				throw new UserException(
						"The import supplier contract finishes before the supply era.");
			}

			if (impSc == null) {
				throw new UserException(
						"If the import MPAN core is present, the import supply capacity must also be present.");
			}
			setImpSc(impSc);
		}
		Hiber.flush();
		if (expMpanCore == null) {
			setExpMpanCore(null);
			if (expLlfcCode != null) {
				throw new UserException(
						"If the export MPAN core is null, the export LLFC must also be null.");
			}
			setExpLlfc(null);
			if (expSupplierContract != null) {
				throw new UserException(
						"If the export MPAN core is null, the export supplier contract must also be null.");
			}
			setExpSupplierContract(null);
			if (expSupplierAccount != null) {
				throw new UserException(
						"If the export MPAN core is null, the export supplier account must also be null.");
			}
			setExpSupplierAccount(null);
			if (expSc != null) {
				throw new UserException(
						"If the export MPAN core is null, the export supply capacity must also be null.");
			}
			setExpSc(null);
		} else {
			expMpanCore = normalizeMpanCore(expMpanCore);
			if (!expMpanCore.substring(0, 2).equals(
					supply.getDnoContract().getParty().getDnoCode())) {
				throw new UserException(
						"The DNO of the export MPAN core must match the supply's DNO.");
			}
			setExpMpanCore(expMpanCore);
			if (expLlfcCode == null) {
				throw new UserException(
						"If the export MPAN core is present, the export LLFC must also be present.");
			}
			setExpLlfc(Llfc.getLlfc(supply.getDnoContract(), expLlfcCode));
			if (getExpLlfc().getIsImport()) {
				throw new UserException(
						"Problem with the export MPAN with core '"
								+ expMpanCore + "'. The Line Loss Factor '"
								+ getExpLlfc().getCode()
								+ "' says that the MPAN is actually import.");
			}
			if (expSupplierContract == null) {
				throw new UserException(
						"If the export MPAN core is present, the export supplier contract must also be present.");
			}
			setExpSupplierContract(expSupplierContract);
			if (expSupplierAccount == null) {
				throw new UserException(
						"If the export MPAN core is present, the export supplier account must also be present.");
			}
			setExpSupplierAccount(expSupplierAccount);
			if (expSupplierContract.getStartRateScript().getStartDate()
					.after(startDate)) {
				throw new UserException(
						"The export supplier contract starts after the supply era.");
			}
			if (HhStartDate.isBefore(expSupplierContract.getFinishRateScript()
					.getFinishDate(), finishDate)) {
				throw new UserException(
						"The export supplier contract finishes before the supply era.");
			}

			if (expSc == null) {
				throw new UserException(
						"If the export MPAN core is present, the export supply capacity must also be present.");
			}
			setExpSc(expSc);
		}

		if (impMpanCore == null && expMpanCore == null) {
			throw new UserException(document(),
					"A supply era must have at least one MPAN.");
		}
		if (impMpanCore != null && expMpanCore != null) {
			if (!getImpLlfc().getVoltageLevel().equals(
					getExpLlfc().getVoltageLevel())) {
				throw new UserException(
						"The voltage level indicated by the Line Loss Factor must be the same for both the MPANs.");
			}
		}
		setMtc(Mtc.getMtc(supply.getDnoContract(), mtcCode));
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

		if (previousEra == null) {
			if (((Long) Hiber
					.session()
					.createQuery(
							"select count(*) from HhDatum datum where datum.channel.era.supply  = :supply and datum.startDate.date < :date")
					.setEntity("supply", supply)
					.setTimestamp("date", startDate.getDate()).uniqueResult()) > 0) {
				throw new UserException(
						"There are HH data before the start of the updated supply.");
			}
		} else {
			boolean isOverlap = false;
			if (impMpanCore != null) {
				String prevImpMpanCore = previousEra.getImpMpanCore();
				if (prevImpMpanCore != null
						&& impMpanCore.equals(prevImpMpanCore)) {
					isOverlap = true;
				}
			}
			if (!isOverlap && expMpanCore != null) {
				String prevExpMpanCore = previousEra.getExpMpanCore();
				if (prevExpMpanCore != null
						&& expMpanCore.equals(prevExpMpanCore)) {
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
		if (nextEra == null) {
			if (finishDate != null
					&& ((Long) Hiber
							.session()
							.createQuery(
									"select count(*) from HhDatum datum where datum.channel.era.supply  = :supply and datum.startDate.date > :date")
							.setEntity("supply", supply)
							.setTimestamp("date", finishDate.getDate())
							.uniqueResult()) > 0) {
				throw new UserException("There are HH data after " + finishDate
						+ ", the end of the updated supply.");
			}
		} else {
			boolean isOverlap = false;
			if (impMpanCore != null) {
				String nextImpMpanCore = nextEra.getImpMpanCore();
				if (nextImpMpanCore != null
						&& impMpanCore.equals(nextImpMpanCore)) {
					isOverlap = true;
				}
			}
			if (!isOverlap && expMpanCore != null) {
				String nextExpMpanCore = nextEra.getExpMpanCore();
				if (nextExpMpanCore != null
						&& expMpanCore.equals(nextExpMpanCore)) {
					isOverlap = true;
				}
			}
			if (!isOverlap) {
				throw new UserException(
						"MPAN cores can't change without an overlapping period.");
			}
		}

		if (hhdcContract == null) {
			throw new UserException("The HHDC contract can't be null.");
		}
		hhdcAccount = hhdcAccount == null ? null : hhdcAccount.trim();
		if (hhdcAccount == null || hhdcAccount.length() == 0) {
			throw new UserException(
					"If there's a HHDC contract, there must be an account reference.");
		}
		HhStartDate hhdcContractStartDate = hhdcContract.getStartRateScript()
				.getStartDate();
		if (hhdcContractStartDate.after(startDate)) {
			throw new UserException(
					"The HHDC contract starts after the supply era.");
		}
		HhStartDate hhdcContractFinishDate = hhdcContract.getFinishRateScript()
				.getFinishDate();
		if (HhStartDate.isBefore(hhdcContractFinishDate, finishDate)) {
			throw new UserException("The HHDC contract " + hhdcContract.getId()
					+ " finishes before the supply era.");
		}
		Hiber.flush();
		setHhdcAccount(hhdcAccount);
		setHhdcContract(hhdcContract);
		Hiber.flush();

		if (mopContract == null) {
			mopAccount = null;
		} else {
			mopAccount = mopAccount == null ? null : mopAccount.trim();
			if (mopAccount == null || mopAccount.length() == 0) {
				throw new UserException(
						"If there's a MOP contract, there must be an account reference.");
			}
			HhStartDate mopContractStartDate = mopContract.getStartRateScript()
					.getStartDate();
			if (mopContractStartDate.after(startDate)) {
				throw new UserException(
						"The MOP contract starts after the supply era.");
			}
			HhStartDate mopContractFinishDate = mopContract
					.getFinishRateScript().getFinishDate();
			if (HhStartDate.isBefore(mopContractFinishDate, finishDate)) {
				throw new UserException("The MOP contract "
						+ mopContract.getId()
						+ " finishes before the supply era.");
			}
		}

		if (pc.getCode().equals("00") && ssc != null) {
			throw new UserException(
					"A supply with Profile Class 00 can't have a Standard Settlement Configuration.");
		}
		if (!pc.getCode().equals("00") && ssc == null) {
			throw new UserException(
					"A NHH supply must have a Standard Settlement Configuration.");
		}

		setSsc(ssc);
		Hiber.flush();
		setMopAccount(mopAccount);
		setMopContract(mopContract);
		Hiber.flush();

		for (Channel channel : channels) {
			channel.onEraChange();
		}
		Hiber.flush();

		// See if we have to move hh data from one era to the other
		for (Boolean isImport : new Boolean[] { true, false }) {
			for (Boolean isKwh : new Boolean[] { true, false }) {
				Channel targetChannel = getChannel(isImport, isKwh);
				Query query = Hiber
						.session()
						.createQuery(
								"select datum.startDate, datum.value, datum.status from HhDatum datum where datum.channel.era.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.startDate.date >= :from"
										+ (finishDate == null ? ""
												: " and datum.startDate.date <= :to")
										+ (targetChannel == null ? ""
												: " and datum.channel != :targetChannel"))
						.setEntity("supply", supply)
						.setBoolean("isImport", isImport)
						.setBoolean("isKwh", isKwh)
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
						throw new UserException("There is no channel for the "
								+ (isImport ? "import" : "export") + " "
								+ (isKwh ? "kWh" : "kVArh")
								+ " HH datum starting " + groupStart.toString()
								+ " to move to in the era starting "
								+ startDate + ", finishing " + finishDate + ".");
					}
					Query channelUpdate = Hiber
							.session()
							.createSQLQuery(
									"update hh_datum set channel_id = :targetChannelId from channel, era where hh_datum.start_date >= :startDate and channel.id = hh_datum.channel_id and era.id = channel.era_id and channel.is_import = :isImport and channel.is_kwh = :isKwh and era.supply_id = :supplyId"
											+ (finishDate == null ? ""
													: " and hh_datum.start_date <= :finishDate"))
							.setLong("supplyId", supply.getId())
							.setBoolean("isImport", isImport)
							.setBoolean("isKwh", isKwh)
							.setLong("targetChannelId", targetChannel.getId())
							.setTimestamp("startDate", startDate.getDate());
					if (finishDate != null) {
						channelUpdate.setTimestamp("finishDate",
								finishDate.getDate());
					}
					channelUpdate.executeUpdate();
					HhStartDate groupFinish = groupStart;
					HhStartDate estStart = null;
					HhStartDate estFinish = null;

					hhData.beforeFirst();
					while (hhData.next()) {
						HhStartDate hhStartDate = (HhStartDate) hhData.get(0);
						if (groupFinish.getNext().before(hhStartDate)) {
							targetChannel.deleteSnag(Snag.SNAG_MISSING,
									groupStart, groupFinish);
							groupStart = groupFinish = hhStartDate;
						} else {
							groupFinish = hhStartDate;
						}
						if (((BigDecimal) hhData.get(1)).doubleValue() < 0) {
							targetChannel.addSnag(Snag.SNAG_NEGATIVE,
									hhStartDate, hhStartDate);
						}
						if ((Character) hhData.get(2) != HhDatum.ACTUAL) {
							if (estStart == null) {
								estStart = hhStartDate;
							}
							estFinish = hhStartDate;
						}

						if (estStart != null && !hhStartDate.equals(estFinish)) {
							targetChannel.addSnag(Snag.SNAG_ESTIMATED,
									estStart, estFinish);
							estStart = null;
						}
					}
					targetChannel.deleteSnag(Snag.SNAG_MISSING, groupStart,
							groupFinish);
					if (estStart != null) {
						targetChannel.addSnag(Snag.SNAG_ESTIMATED, estStart,
								estFinish);
					}
					hhData.close();
				}
			}
		}
		Hiber.flush();
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
		for (Snag snag : (List<Snag>) Hiber.session()
				.createQuery("from Snag snag where snag.channel = :channel")
				.setEntity("channel", channel).list()) {
			snag.delete();
		}
		channels.remove(channel);
		Hiber.session().flush();
	}

	public void setPhysicalLocation(Site site) throws HttpException {
		SiteEra targetSiteSupply = null;
		for (SiteEra siteSupply : siteEras) {
			if (site.equals(siteSupply.getSite())) {
				targetSiteSupply = siteSupply;
			}
		}
		if (targetSiteSupply == null) {
			throw new UserException("The site isn't attached to this supply.");
		}
		for (SiteEra siteSupply : siteEras) {
			siteSupply.setIsPhysical(siteSupply.equals(targetSiteSupply));
		}
		Hiber.flush();
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element eraElement = (Element) toXml(
				doc,
				new XmlTree("siteEras", new XmlTree("site")).put("pc")
						.put("impLlfc").put("expLlfc").put("mtc").put("cop")
						.put("ssc")
						.put("supply", new XmlTree("source").put("gspGroup"))
						.put("mopContract", new XmlTree("party"))
						.put("hhdcContract", new XmlTree("party")));
		source.appendChild(eraElement);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(MonadDate.getHoursXml(doc));
		source.appendChild(HhStartDate.getHhMinutesXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (Pc pc : (List<Pc>) Hiber.session()
				.createQuery("from Pc pc order by pc.code").list()) {
			source.appendChild(pc.toXml(doc));
		}
		for (Cop cop : (List<Cop>) Hiber.session()
				.createQuery("from Cop cop order by cop.code").list()) {
			source.appendChild(cop.toXml(doc));
		}
		for (GspGroup group : (List<GspGroup>) Hiber.session()
				.createQuery("from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'M' order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'C' order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'X' order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		source.setAttribute("num-eras",
				Integer.toString(supply.getEras().size()));
		return doc;
	}

	public Channels getChannelsInstance() {
		return new Channels(this);
	}

	void delete() throws HttpException {
		List<SiteEra> ssGens = new ArrayList<SiteEra>();
		for (SiteEra ssGen : siteEras) {
			ssGens.add(ssGen);
		}
		for (SiteEra ssGen : ssGens) {
			siteEras.remove(ssGen);
			Hiber.flush();
			ssGen.getSite().detachSiteEra(ssGen);
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

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		Hiber.session().setReadOnly(this, false);
		Document doc = document();
		try {
			if (inv.hasParameter("delete")) {
				supply.deleteEra(this);
				Hiber.commit();
				inv.sendSeeOther(new Eras(supply).getEditUri());
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
				Date startDate = inv.getDateTime("start");
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
				Contract mopContract = null;
				Contract hhdcContract = null;
				Contract importSupplierContract = null;
				String importSupplierAccount = null;
				boolean isEnded = inv.getBoolean("is-ended");
				if (isEnded) {
					Date finishDateRaw = inv.getDateTime("finish");
					if (!inv.isValid()) {
						throw new UserException();
					}
					finishDate = new HhStartDate(finishDateRaw);
				}
				String mopAccount = null;
				if (mopContractId != null) {
					mopContract = Contract.getMopContract(mopContractId);
					mopAccount = inv.getString("mop-account");
				}
				String hhdcAccount = null;
				if (hhdcContractId != null) {
					hhdcContract = Contract.getHhdcContract(hhdcContractId);
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

					importSupplierContract = Contract
							.getSupplierContract(importSupplierContractId);
				}
				String exportMpanCoreStr = null;
				String exportLlfcCode = null;
				Integer exportAgreedSupplyCapacity = null;
				String exportSupplierAccount = null;
				Contract exportSupplierContract = null;
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
					exportSupplierContract = Contract
							.getSupplierContract(exportSupplierContractId);
				}
				supply.updateEra(this, new HhStartDate(startDate), finishDate,
						mopContract, mopAccount, hhdcContract, hhdcAccount,
						meterSerialNumber, pc, mtcCode, cop, ssc,
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

	public void detachSite(Site site) throws HttpException {
		if (siteEras.size() < 2) {
			throw new UserException(
					"A supply has to be attached to at least one site.");
		}
		SiteEra siteEra = (SiteEra) Hiber
				.session()
				.createQuery(
						"from SiteEra siteEra where siteEra.era = :era and siteEra.site = :site")
				.setEntity("era", this).setEntity("site", site).uniqueResult();
		if (siteEra == null) {
			throw new UserException(
					"Can't detach this site, as it wasn't attached in the first place.");
		}
		siteEras.remove(siteEra);
		siteEras.iterator().next().setIsPhysical(true);
		Hiber.flush();
		site.detachSiteEra(siteEra);
		Hiber.flush();
	}

}
