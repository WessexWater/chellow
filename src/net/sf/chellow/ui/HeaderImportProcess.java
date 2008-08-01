package net.sf.chellow.ui;

import java.io.IOException;
import java.io.InputStreamReader;
import java.util.logging.Level;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadBoolean;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Meter;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.MpanTop;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.Site;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.Ssc;
import net.sf.chellow.physical.SscCode;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplyGeneration;

import org.apache.commons.fileupload.FileItem;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class HeaderImportProcess extends Thread implements Urlable,
		XmlDescriber {
	private static final String NO_CHANGE = "{no change}";

	private boolean halt = false;

	private Document doc = MonadUtils.newSourceDocument();

	private Element source = doc.getDocumentElement();

	private CSVParser shredder;

	private int lineNumber;

	private MonadUri uri;

	public HeaderImportProcess(MonadUri uri, FileItem item)
			throws InternalException, HttpException, DeployerException {
		super("Import");
		this.uri = uri;
		if (item.getSize() == 0) {
			throw new UserException("File has zero length");
		}
		try {
			shredder = new CSVParser(new InputStreamReader(item
					.getInputStream(), "UTF-8"));
			shredder.setCommentStart("#;!");
			shredder.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = shredder.getLine();

			if (titles.length < 2
					|| !titles[0].trim().toLowerCase().equals("action")
					|| !titles[1].trim().toLowerCase().equals("type")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "'Action, Type'.");
			}
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	private synchronized void halt() {
		halt = true;
	}

	private synchronized boolean shouldHalt() {
		return halt;
	}

	private synchronized int getLineNumber() {
		return lineNumber;
	}

	private synchronized void setLineNumber(int lineNumber) {
		this.lineNumber = lineNumber;
	}

	public void run() {
		Element source = (Element) doc.getFirstChild();
		Organization organization;
		try {
			organization = getOrganization();
			for (String[] values = shredder.getLine(); values != null
					&& !shouldHalt(); values = shredder.getLine()) {
				setLineNumber(shredder.lastLineNumber());
				if (values.length < 2) {
					throw new UserException(
							"There must be an 'Action' field followed "
									+ "by a 'Type' field.");
				}
				processItem(organization, values);
				Hiber.close();
			}
			if (shouldHalt()) {
				source.appendChild(new MonadMessage(
						"The import has been cancelled.").toXml(doc));
			} else {
				source.appendChild(new MonadMessage(
						"The file has been imported successfully.").toXml(doc));
			}
		} catch (HttpException e) {
			source.appendChild(new MonadMessage(
					"There are errors that need to be corrected before "
							+ "the file can be imported.").toXml(doc));
		} catch (Throwable e) {
			source.appendChild(new MonadMessage("Programmer Exception: "
					+ e.getClass() + " " + e.getMessage()).toXml(doc));
			ChellowLogger.getLogger().log(Level.SEVERE,
					"From header import process", e);
		} finally {
			Hiber.rollBack();
			Hiber.close();
		}
	}

	private void processItem(Organization organization, String[] values)
			throws InternalException, DeployerException, HttpException,
			DesignerException {
		String action = values[0].trim().toLowerCase();
		String type = values[1].trim().toLowerCase();
		Element csvElement = doc.createElement("csvLine");
		try {
			csvElement.setAttribute("number", String.valueOf(lineNumber));
			csvElement.appendChild(getField("Action", values[0]));
			csvElement.appendChild(getField("Type", values[1]));
			if (!action.equals("insert") && !action.equals("update")
					&& !action.equals("delete")) {
				throw new UserException("The 'Action' field can "
						+ "only be 'insert', 'update', 'delete'.");
			}
			if (type.equals("site")) {
				if (values.length < 3) {
					throw new UserException(
							"There aren't enough fields in this row");
				}
				Site site = null;
				String code = values[2];
				csvElement.appendChild(getField("Site Code", code));
				if (action.equals("insert")) {
					String name = values[3];
					csvElement.appendChild(getField("Site name", name));
					organization.insertSite(code, name);
				} else {
					site = organization.getSite(code);
					if (site == null) {
						throw new UserException(
								"There is no site with this code.");
					}
					if (action.equals("delete")) {
						organization.deleteSite(site);
					} else if (action.equals("update")) {
						String newCode = values[3];
						csvElement.appendChild(getField("New Site Code",
								newCode));
						String name = values[4];
						csvElement.appendChild(getField("New site name", name));
						site.update(newCode, name);
					}
				}
			} else if (type.equals("supply")) {
				if (action.equals("insert")) {
					if (values.length < 21) {
						throw new UserException(
								"There aren't enough fields in this row");
					}
					String siteCode = values[2];
					csvElement.appendChild(getField("Site Code", siteCode));
					String sourceCode = values[3];
					csvElement.appendChild(getField("Source Code",
							sourceCode));
					String supplyName = values[4];
					csvElement.appendChild(getField("Supply Name", supplyName));
					String startDateStr = values[5];
					csvElement
							.appendChild(getField("Start date", startDateStr));
					String meterSerialNumber = values[6];
					csvElement.appendChild(getField("Meter Serial Number",
							meterSerialNumber));
					String importMpanStr = values[7];
					csvElement.appendChild(getField("Import MPAN",
							importMpanStr));
					MpanRaw importMpanRaw = null;
					if (importMpanStr.length() != 0) {
						importMpanRaw = new MpanRaw("import", importMpanStr);
					}
					Integer importAgreedSupplyCapacity = null;
					HhdcContract importHhdcContract = null;
					Account importHhdceAccount = null;
					SupplierContract importSupplierContract = null;
					Account importSupplierAccount = null;
					Ssc importSsc = null;
					
					if (importMpanRaw != null) {
						String importSscStr = values[8];
						csvElement.appendChild(getField("Import SSC", importSscStr));
						importSsc = importSscStr.equals("null") ? null : Ssc.getSsc(new SscCode(Integer.parseInt(importSscStr)));
						String importAgreedSupplyCapacityStr = values[8];
						csvElement.appendChild(getField(
								"Import Agreed Supply Capacity",
								importAgreedSupplyCapacityStr));
						importAgreedSupplyCapacity = new Integer(
								importAgreedSupplyCapacityStr);
						String importHhdcContractName = values[9];
						csvElement.appendChild(getField("Import HHDC Contract",
								importHhdcContractName));
						importHhdcContract = importHhdcContractName == null ? null
								: organization.getHhdcContract(
										importHhdcContractName);
						String importHhdceAccountReference = values[10];
						csvElement.appendChild(getField("Import HHDC Account",
								importHhdceAccountReference));
						importHhdceAccount = importHhdcContract.getAccount(importHhdceAccountReference);
						String importSupplierContractName = values[11];
						csvElement.appendChild(getField(
								"Import supplier contract name",
								importSupplierContractName));
						importSupplierContract = organization
								.getSupplierContract(importSupplierContractName);
						String importSupplierAccountReference = values[12];
						csvElement.appendChild(getField(
								"Import supplier account reference",
								importSupplierAccountReference));
						importSupplierAccount = importSupplierContract.getAccount(importSupplierAccountReference);
					}
					HhdcContract exportHhdceContract = null;
					Account exportHhdceAccount = null;
					SupplierContract exportSupplierContract = null;
					Account exportAccountSupplier = null;
					Integer exportAgreedSupplyCapacity = null;
					MpanRaw exportMpanRaw = null;
					Ssc exportSsc = null;
					String exportMpanStr = values[14];
					csvElement.appendChild(getField("Export MPAN",
							exportMpanStr));
					if (exportMpanStr.length() != 0) {
						exportMpanRaw = new MpanRaw("export", exportMpanStr);
					}
					if (exportMpanRaw != null) {
						String exportSscStr = values[15];
						csvElement.appendChild(getField("Export SSC", exportSscStr));
						exportSsc = exportSscStr.equals("null") ? null : Ssc.getSsc(new SscCode(exportSscStr));
						String exportAgreedSupplyCapacityStr = values[15];
						csvElement.appendChild(getField(
								"Export Agreed Supply Capacity",
								exportAgreedSupplyCapacityStr));
						exportAgreedSupplyCapacity = new Integer(
								exportAgreedSupplyCapacityStr);
						String exportHhdcContractName = values[16];
						csvElement.appendChild(getField("Export HHDC contract",
								exportHhdcContractName));
						exportHhdceContract = exportHhdcContractName.length() == 0 ? null
								: organization.getHhdcContract(exportHhdcContractName);
						String exportHhdcAccountReference = values[17];
						csvElement.appendChild(getField("Export HHDC account",
								exportHhdcAccountReference));
						exportHhdceAccount = exportHhdceContract.getAccount(exportHhdcAccountReference);
						String exportSupplierContractName = values[18];
						csvElement.appendChild(getField(
								"Export supplier contract name",
								exportSupplierContractName));
						exportSupplierContract = organization
								.getSupplierContract(exportSupplierContractName);
						String exportAccountSupplierReference = values[19];
						csvElement.appendChild(getField(
								"Export supplier account reference",
								exportAccountSupplierReference));
						exportAccountSupplier = exportSupplierContract.getAccount(exportAccountSupplierReference);
					}
					Site site = organization.getSite(siteCode);
					site.insertSupply(supplyName, meterSerialNumber,
							importMpanRaw, importSsc, importHhdceAccount,
							importSupplierAccount,
							true, true, false, true,
							importAgreedSupplyCapacity, exportMpanRaw, exportSsc,
							exportHhdceAccount, exportAccountSupplier,
							 false, true, true, true,
							exportAgreedSupplyCapacity, HhEndDate
									.roundUp(new MonadDate(startDateStr)
											.getDate()), sourceCode, null);
				} else if (action.equals("update")) {
					if (values.length < 5) {
						throw new UserException(
								"There aren't enough fields in this row");
					}
					String mpanCoreStr = values[2];
					csvElement.appendChild(getField("MPAN Core", mpanCoreStr));
					String sourceCode = values[3];
					csvElement.appendChild(getField("Source Code",
							sourceCode));
					String supplyName = values[4];
					csvElement.appendChild(getField("Supply Name", supplyName));
					Supply supply = organization.getMpanCore(
							new MpanCoreRaw(mpanCoreStr)).getSupply();
					supply.update(supplyName.equals(NO_CHANGE) ? supply
							.getName() : supplyName, sourceCode
							.equals(NO_CHANGE) ? supply.getSource() : Source
							.getSource(sourceCode));
				}
			} else if (type.equals("supply-generation")) {
				if (action.equals("update")) {
					if (values.length < 29) {
						throw new UserException(
								"There aren't enough fields in this row");
					}
					String mpanCoreStr = values[2];
					csvElement.appendChild(getField("MPAN Core", mpanCoreStr));
					String dateStr = values[3];
					csvElement.appendChild(getField("Date", dateStr));
					Supply supply = organization.getMpanCore(
							new MpanCoreRaw(mpanCoreStr)).getSupply();
					String startDateStr = values[4];
					csvElement
							.appendChild(getField("Start date", startDateStr));
					String finishDateStr = values[5];
					csvElement.appendChild(getField("Finish date",
							finishDateStr));
					SupplyGeneration supplyGeneration = supply
							.getGeneration(dateStr.length() == 0 ? null
									: new HhEndDate(dateStr));
					if (supplyGeneration == null) {
						throw new UserException(
								"There isn't a generation at this date.");
					}
					String meterSerialNumber = values[6];
					Meter meter = null;
					if (meterSerialNumber.length() != 0) {
						meter = supply.findMeter(meterSerialNumber);
						if (meter == null) {
							meter = supply.insertMeter(meterSerialNumber);
						}
					}
					supplyGeneration.update(
							startDateStr.equals(NO_CHANGE) ? supplyGeneration
									.getStartDate() : new HhEndDate("start",
									startDateStr),
							finishDateStr.length() == 0 ? null : (finishDateStr
									.equals(NO_CHANGE) ? supplyGeneration
									.getFinishDate() : new HhEndDate("finish",
									finishDateStr)), meter);
					String importMpanStr = values[7];
					csvElement.appendChild(getField("Import MPAN",
							importMpanStr));
					MpanTop importMpanTop = null;
					MpanCore importMpanCore = null;
					boolean importHasImportKwh = false;
					boolean importHasImportKvarh = false;
					boolean importHasExportKwh = false;
					boolean importHasExportKvarh = false;
					String importAgreedSupplyCapacityStr = values[8];
					csvElement.appendChild(getField(
							"Import Agreed Supply Capacity",
							importAgreedSupplyCapacityStr));
					Integer importAgreedSupplyCapacity = null;
					Mpan existingImportMpan = supplyGeneration.getImportMpan();
					HhdcContract importHhdceContract = null;
					Account importHhdceAccount = null;
					SupplierContract importSupplierContract = null;
					Account importSupplierAccount = null;
					if (importMpanStr.equals(NO_CHANGE)) {
						importMpanTop = existingImportMpan == null ? null
								: existingImportMpan.getMpanTop();
						importMpanCore = existingImportMpan == null ? null
								: existingImportMpan.getMpanCore();
					} else {
						MpanRaw importMpanRaw = new MpanRaw(importMpanStr);
						importMpanTop = importMpanRaw.getMpanTop();
						importMpanCore = importMpanRaw
								.getMpanCore(organization);
					}
					if (importMpanTop != null) {
						if (importAgreedSupplyCapacityStr.equals(NO_CHANGE)) {
							if (existingImportMpan == null) {
								throw new UserException(
										"There isn't an existing import MPAN.");
							} else {
								importAgreedSupplyCapacity = existingImportMpan
										.getAgreedSupplyCapacity();
							}
						} else {
							importAgreedSupplyCapacity = Integer
									.parseInt(importAgreedSupplyCapacityStr);
						}
						String importHasImportKwhStr = values[9];
						csvElement.appendChild(getField("Import is import kWh",
								importHasImportKwhStr));
						importHasImportKwh = importHasImportKwhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasImportKwh()
								: new MonadBoolean(importHasImportKwhStr)
										.getBoolean();
						String importHasImportKvarhStr = values[10];
						csvElement.appendChild(getField(
								"Import is import kVArh",
								importHasImportKvarhStr));
						importHasImportKvarh = importHasImportKvarhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasImportKvarh()
								: new MonadBoolean(importHasImportKvarhStr)
										.getBoolean();
						String importHasExportKwhStr = values[11];
						csvElement.appendChild(getField("Import is export kWh",
								importHasExportKwhStr));
						importHasExportKwh = importHasExportKwhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasExportKwh()
								: new MonadBoolean(importHasExportKwhStr)
										.getBoolean();
						String importHasExportKvarhStr = values[12];
						csvElement.appendChild(getField(
								"Import is export kVArh",
								importHasExportKvarhStr));
						importHasExportKvarh = importHasExportKvarhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasExportKvarh()
								: new MonadBoolean(importHasExportKvarhStr)
										.getBoolean();
						if (importHasImportKwh || importHasImportKvarh
								|| importHasExportKwh || importHasExportKvarh) {
							/*
							String importHhdceStr = values[13];
							csvElement.appendChild(getField("Import DCE",
									importHhdceStr));
							if (importHhdceStr.equals(NO_CHANGE)) {
								if (existingImportMpan.getHhdceContract() == null) {
									throw new UserException(
											"There isn't an existing DCE contract");
								} else {
									importHhdce = existingImportMpan
											.getHhdceContract().getProvider();
								}
							} else {
								importHhdce = Provider.getProvider(
										importHhdceStr, MarketRole.HHDC);
							}
							*/
							String importHhdceContractName = values[13];
							if (importHhdceContractName.equals(NO_CHANGE)) {
								if (existingImportMpan == null
										|| existingImportMpan
												.getHhdceContract() == null) {
									throw new UserException(
											"There isn't an existing HHDCE contract");
								} else {
importHhdceContract = existingImportMpan.getHhdceContract();								}
							} else {
								importHhdceContract = organization
										.getHhdcContract(importHhdceContractName);
							}
							String importHhdceAccountReference = values[14];
							importHhdceAccount = importHhdceContract.getAccount(importHhdceAccountReference);
						}
						String importContractSupplierName = values[15];
						csvElement.appendChild(getField(
								"Import Supplier Contract",
								importContractSupplierName));
						if (importContractSupplierName.equals(NO_CHANGE)) {
							if (existingImportMpan == null) {
								throw new UserException(
										"There isn't an existing import supplier.");
							}
							importSupplierContract = existingImportMpan
									.getSupplierContract();
						} else {
							importSupplierContract = organization
									.getSupplierContract(importContractSupplierName);
						}

						String importSupplierAccountReference = values[16];
						csvElement.appendChild(getField(
								"Import Supplier Account",
								importSupplierAccountReference));
						if (importSupplierAccountReference.equals(NO_CHANGE)) {
							if (existingImportMpan == null) {
								throw new UserException(
										"There isn't an existing import supplier.");
							}
							importSupplierAccount = existingImportMpan
									.getSupplierAccount();
						} else {
							importSupplierAccount = importSupplierContract
									.getAccount(importSupplierAccountReference);
						}
					}
					String exportMpanStr = values[18];
					csvElement
							.appendChild(getField("Eport MPAN", exportMpanStr));
					MpanTop exportMpanTop = null;
					MpanCore exportMpanCore = null;
					boolean exportHasImportKwh = false;
					boolean exportHasImportKvarh = false;
					boolean exportHasExportKwh = false;
					boolean exportHasExportKvarh = false;
					String exportAgreedSupplyCapacityStr = values[21];
					csvElement.appendChild(getField(
							"Export Agreed Supply Capacity",
							exportAgreedSupplyCapacityStr));
					Mpan existingExportMpan = supplyGeneration.getExportMpan();
					Integer exportAgreedSupplyCapacity = null;
					if (exportMpanStr.equals(NO_CHANGE)) {
						exportMpanTop = existingExportMpan == null ? null
								: existingExportMpan.getMpanTop();
						exportMpanCore = existingExportMpan == null ? null
								: existingExportMpan.getMpanCore();
					} else {
						MpanRaw exportMpanRaw = new MpanRaw(exportMpanStr);
						exportMpanTop = exportMpanRaw.getMpanTop();
						exportMpanCore = exportMpanRaw
								.getMpanCore(organization);
					}
					Account exportHhdceAccount = null;
					SupplierContract exportSupplierContract = null;
					Account exportAccountSupplier = null;
					if (exportMpanTop != null) {
						if (exportAgreedSupplyCapacityStr.equals(NO_CHANGE)) {
							if (existingExportMpan == null) {
								throw new UserException(
										"There isn't an existing export MPAN.");
							} else {

								exportAgreedSupplyCapacity = existingExportMpan
										.getAgreedSupplyCapacity();
							}
						} else {
							exportAgreedSupplyCapacity = new Integer(
									exportAgreedSupplyCapacityStr);
						}
						String exportHasImportKwhStr = values[19];
						csvElement.appendChild(getField("Export is import kWh",
								exportHasImportKwhStr));
						exportHasImportKwh = exportHasImportKwhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasImportKwh()
								: new MonadBoolean(exportHasImportKwhStr)
										.getBoolean();
						String exportHasImportKvarhStr = values[20];
						csvElement.appendChild(getField(
								"Export is import kVArh",
								exportHasImportKvarhStr));
						exportHasImportKvarh = exportHasImportKvarhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasImportKvarh()
								: new MonadBoolean(exportHasImportKvarhStr)
										.getBoolean();
						String exportHasExportKwhStr = values[21];
						csvElement.appendChild(getField("Export is export kWh",
								exportHasExportKwhStr));
						exportHasExportKwh = exportHasExportKwhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasExportKwh()
								: new MonadBoolean(exportHasExportKwhStr)
										.getBoolean();
						String exportHasExportKvarhStr = values[22];
						csvElement.appendChild(getField(
								"Export is export kVArh",
								exportHasExportKvarhStr));
						exportHasExportKvarh = exportHasExportKvarhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasExportKvarh()
								: new MonadBoolean(exportHasExportKvarhStr)
										.getBoolean();
						HhdcContract exportHhdceContract = null;
						if (exportHasImportKwh || exportHasImportKvarh
								|| exportHasExportKwh || exportHasExportKvarh) {
							String exportHhdceContractName = values[24];
							if (exportHhdceContractName.equals(NO_CHANGE)) {
								if (existingExportMpan == null) {
									throw new UserException(
											"There isn't an existing export DCE contract.");
								} else {
									exportHhdceContract = existingExportMpan
											.getHhdceContract();
								}
							} else {
								exportHhdceContract = organization.getHhdcContract(exportHhdceContractName);
							}
							String exportHhdceAccountReference = values[23];
							csvElement.appendChild(getField("Export DCE account",
									exportHhdceAccountReference));
							if (exportHhdceAccountReference.equals(NO_CHANGE)) {
								if (existingExportMpan == null
										|| existingExportMpan
												.getHhdceContract() == null) {
									throw new UserException(
											"There isn't an existing export supplier.");
								} else {
									exportHhdceAccount = existingExportMpan.getHhdceAccount();
								}
							} else {
								exportHhdceAccount = exportHhdceContract.getAccount(exportHhdceAccountReference);
							}
						}
						String exportContractSupplierName = values[25];
						csvElement.appendChild(getField(
								"Export Supplier Contract",
								exportContractSupplierName));
						if (exportContractSupplierName.equals(NO_CHANGE)) {
							if (existingExportMpan == null) {
								throw new UserException(
										"There isn't an existing export supplier contract.");
							}
							exportSupplierContract = existingExportMpan
									.getSupplierContract();
						} else {
							exportSupplierContract = organization.getSupplierContract(exportContractSupplierName);
						}
						String exportSupplierAccountReference = values[26];
						csvElement.appendChild(getField(
								"Export Supplier Account",
								exportSupplierAccountReference));
						if (exportSupplierAccountReference.equals(NO_CHANGE)) {
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
					supplyGeneration.addOrUpdateMpans(importMpanTop,
							importMpanCore, importHhdceAccount,
							importSupplierAccount,
							importHasImportKwh, importHasImportKvarh,
							importHasExportKwh, importHasExportKvarh,
							importAgreedSupplyCapacity, exportMpanTop,
							exportMpanCore, exportHhdceAccount,
							exportAccountSupplier,
							exportHasImportKwh, exportHasImportKvarh,
							exportHasExportKwh, exportHasExportKvarh,
							exportAgreedSupplyCapacity);
				}
			} else if (type.equals("supplier-account")) {
				if (values.length < 4) {
					throw new UserException(
							"There aren't enough fields in this row");
				}
				String supplierContractName = values[2];
				csvElement.appendChild(getField("Contract", supplierContractName));
				SupplierContract supplierContract = organization.getSupplierContract(supplierContractName);
				String supplierAccountReference = values[3];
				csvElement.appendChild(getField("Reference", supplierAccountReference));
				if (action.equals("insert")) {
					supplierContract.insertAccount(supplierAccountReference);
				} else {
					Account supplierAccount = supplierContract
							.getAccount(supplierAccountReference);
					if (action.equals("delete")) {
						supplierContract.deleteAccount(supplierAccount);
					} else if (action.equals("update")) {
						String newReference = values[4];
						csvElement.appendChild(getField("New Reference",
								newReference));
						supplierAccount.update(newReference);
					}
				}
			} else {
				throw new UserException("The 'Type' field can only "
						+ "be 'site', 'supply' or 'supplier-account'.");
			}
		} catch (HttpException e) {
			String message = e.getMessage();
			if (message != null) {
				csvElement.appendChild(new MonadMessage(message).toXml(doc));
				source.appendChild(csvElement);
			}
			throw e;
		}
	}

	private Element getField(String name, String value) {
		Element field = doc.createElement("Field");
		field.setAttribute("name", name);
		field.setTextContent(value);
		return field;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException {
		return uri;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document document = (Document) doc.cloneNode(true);
		Element source = document.getDocumentElement();
		Element processElement = (Element) toXml(document);
		source.appendChild(processElement);
		processElement.appendChild(getOrganization().toXml(document));
		Hiber.close();
		inv.sendOk(document);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		halt();
		inv.sendSeeOther(getUri());
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = doc.createElement("header-import-process");
		element.setAttribute("uri", uri.toString());
		element.setAttribute("id", getUriId().toString());
		if (isAlive()) {
			element.setAttribute("progress", "Reached line number "
					+ getLineNumber() + ".");
		}
		return element;
	}

	public UriPathElement getUriId() throws InternalException, HttpException {
		String uriString = uri.toString();
		uriString = uriString.substring(0, uriString.length() - 1);
		return new UriPathElement(uriString.substring(uriString
				.lastIndexOf("/") + 1));
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		return null;
	}

	public Organization getOrganization() throws HttpException,
			InternalException {
		return (Organization) Chellow.dereferenceUri(uri.toUri().resolve(
				"../.."));
	}
}