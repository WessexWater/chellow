package net.sf.chellow.ui;

import java.io.IOException;
import java.io.Reader;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;

import javax.xml.stream.XMLEventReader;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.events.XMLEvent;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.Debug;
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
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Meter;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.Site;
import net.sf.chellow.physical.Source;
import net.sf.chellow.physical.Ssc;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplyGeneration;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import com.Ostermiller.util.CSVParser;

public class GeneralImport extends Thread implements Urlable, XmlDescriber {
	private static final String NO_CHANGE = "{no change}";

	private boolean halt = false;

	private Document doc = MonadUtils.newSourceDocument();

	private Element source = doc.getDocumentElement();
	private List<MonadMessage> errors = new ArrayList<MonadMessage>();
	private Digester digester;

	private int lineNumber;

	private MonadUri uri;

	public GeneralImport(MonadUri uri, Reader reader, String extension)
			throws HttpException {
		super("Import");
		this.uri = uri;
		digester = new Digester(reader, extension);
		String[] titles = digester.getLine();

		if (titles.length < 2
				|| !titles[0].trim().toLowerCase().equals("action")
				|| !titles[1].trim().toLowerCase().equals("type")) {
			Debug.print("Titles " + titles.length);
			throw new UserException(
					"The first line of the CSV must contain the titles "
							+ "'Action, Type'.");
		}
	}

	private synchronized void halt() {
		halt = true;
	}

	private synchronized boolean shouldHalt() {
		return halt;
	}

	public int getLineNumber() {
		return lineNumber;
	}

	public void run() {
		// Element source = (Element) doc.getFirstChild();
		try {
			for (String[] values = digester.getLine(); values != null
					&& !shouldHalt(); values = digester.getLine()) {
				// lineNumber = digester.getLastLineNumber();
				if (values.length < 2) {
					throw new UserException(
							"There must be an 'Action' field followed "
									+ "by a 'Type' field.");
				}
				processItem(values);
				Hiber.close();
			}
			if (shouldHalt()) {
				errors.add(new MonadMessage("The import has been cancelled."));
			} else {
				source.appendChild(new MonadMessage(
						"The file has been imported successfully.").toXml(doc));
			}
		} catch (HttpException e) {
			errors.add(new MonadMessage(e.getMessage()));
			errors.add(new MonadMessage(
					"There are errors that need to be corrected before "
							+ "the file can be imported."));
		} catch (Throwable e) {
			errors.add(new MonadMessage("Programmer Exception: " + e.getClass()
					+ " " + e.getMessage()));
			ChellowLogger.getLogger().log(Level.SEVERE,
					"From header import process", e);
		} finally {
			Hiber.rollBack();
			Hiber.close();
		}
	}

	private void processItem(String[] values) throws HttpException {
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
					Site.insertSite(code, name);
				} else {
					site = Site.getSite(code);
					if (site == null) {
						throw new UserException(
								"There is no site with this code.");
					}
					if (action.equals("delete")) {
						Site.deleteSite(site);
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
					csvElement.appendChild(getField("Source Code", sourceCode));
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
					String importSscCode = values[8];
					csvElement
							.appendChild(getField("Import SSC", importSscCode));
					String importAgreedSupplyCapacityStr = values[9];
					csvElement.appendChild(getField(
							"Import Agreed Supply Capacity",
							importAgreedSupplyCapacityStr));
					String importHhdcContractName = values[10];
					csvElement.appendChild(getField("Import HHDC Contract",
							importHhdcContractName));
					String importHhdcAccountReference = values[11];
					csvElement.appendChild(getField("Import HHDC Account",
							importHhdcAccountReference));
					String importSupplierContractName = values[12];
					csvElement.appendChild(getField(
							"Import supplier contract name",
							importSupplierContractName));
					String importSupplierAccountReference = values[13];
					csvElement.appendChild(getField(
							"Import supplier account reference",
							importSupplierAccountReference));
					String exportMpanStr = values[14];
					csvElement.appendChild(getField("Export MPAN",
							exportMpanStr));
					String exportSscCode = values[15];
					csvElement
							.appendChild(getField("Export SSC", exportSscCode));
					String exportAgreedSupplyCapacityStr = values[16];
					csvElement.appendChild(getField(
							"Export Agreed Supply Capacity",
							exportAgreedSupplyCapacityStr));
					String exportHhdcContractName = values[17];
					csvElement.appendChild(getField("Export HHDC contract",
							exportHhdcContractName));
					String exportHhdcAccountReference = values[18];
					csvElement.appendChild(getField("Export HHDC account",
							exportHhdcAccountReference));
					String exportSupplierContractName = values[19];
					csvElement.appendChild(getField(
							"Export supplier contract name",
							exportSupplierContractName));
					String exportSupplierAccountReference = values[20];
					csvElement.appendChild(getField(
							"Export supplier account reference",
							exportSupplierAccountReference));
					Site site = Site.getSite(siteCode);
					site.insertSupply(supplyName, meterSerialNumber,
							importMpanStr, importSscCode,
							importHhdcContractName, importHhdcAccountReference,
							importSupplierContractName,
							importSupplierAccountReference,
							importAgreedSupplyCapacityStr, exportMpanStr,
							exportSscCode, exportHhdcContractName,
							exportHhdcAccountReference,
							exportSupplierContractName,
							exportSupplierAccountReference,
							exportAgreedSupplyCapacityStr, HhEndDate
									.roundUp(new MonadDate(startDateStr)
											.getDate()), sourceCode);
				} else if (action.equals("update")) {
					if (values.length < 5) {
						throw new UserException(
								"There aren't enough fields in this row");
					}
					String mpanCoreStr = values[2];
					csvElement.appendChild(getField("MPAN Core", mpanCoreStr));
					String sourceCode = values[3];
					csvElement.appendChild(getField("Source Code", sourceCode));
					String supplyName = values[4];
					csvElement.appendChild(getField("Supply Name", supplyName));
					Supply supply = MpanCore.getMpanCore(mpanCoreStr)
							.getSupply();
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
					Supply supply = MpanCore.getMpanCore(mpanCoreStr)
							.getSupply();
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
					boolean importHasImportKwh = false;
					boolean importHasImportKvarh = false;
					boolean importHasExportKwh = false;
					boolean importHasExportKvarh = false;
					String importSscCode = values[8];
					csvElement
							.appendChild(getField("Import SSC", importSscCode));
					Ssc importSsc = null;
					String importAgreedSupplyCapacityStr = values[9];
					csvElement.appendChild(getField(
							"Import Agreed Supply Capacity",
							importAgreedSupplyCapacityStr));
					Integer importAgreedSupplyCapacity = null;
					Mpan existingImportMpan = supplyGeneration.getImportMpan();
					HhdcContract importHhdcContract = null;
					Account importHhdcAccount = null;
					SupplierContract importSupplierContract = null;
					Account importSupplierAccount = null;
					if (importMpanStr.equals(NO_CHANGE)) {
						importMpanStr = existingImportMpan == null ? null
								: existingImportMpan.toString();
					}
					if (importMpanStr != null) {
						if (importSscCode.equals(NO_CHANGE)) {
							if (existingImportMpan == null) {
								throw new UserException(
										"There isn't an existing import MPAN.");
							} else {
								importSsc = existingImportMpan.getTop()
										.getSsc();
							}
						} else {
							importSsc = importSscCode.length() == 0 ? null
									: Ssc.getSsc(importSscCode);
						}
						if (importAgreedSupplyCapacityStr.equals(NO_CHANGE)) {
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
						String importHasImportKwhStr = values[10];
						csvElement.appendChild(getField("Import is import kWh",
								importHasImportKwhStr));
						importHasImportKwh = importHasImportKwhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasImportKwh()
								: Boolean.parseBoolean(importHasImportKwhStr);
						String importHasImportKvarhStr = values[11];
						csvElement.appendChild(getField(
								"Import is import kVArh",
								importHasImportKvarhStr));
						importHasImportKvarh = importHasImportKvarhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasImportKvarh()
								: Boolean.parseBoolean(importHasImportKvarhStr);
						String importHasExportKwhStr = values[12];
						csvElement.appendChild(getField("Import is export kWh",
								importHasExportKwhStr));
						importHasExportKwh = importHasExportKwhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasExportKwh()
								: Boolean.parseBoolean(importHasExportKwhStr);
						String importHasExportKvarhStr = values[13];
						csvElement.appendChild(getField(
								"Import is export kVArh",
								importHasExportKvarhStr));
						importHasExportKvarh = importHasExportKvarhStr
								.equals(NO_CHANGE) ? existingImportMpan == null ? false
								: existingImportMpan.getHasExportKvarh()
								: Boolean.parseBoolean(importHasExportKvarhStr);
						if (importHasImportKwh || importHasImportKvarh
								|| importHasExportKwh || importHasExportKvarh) {
							/*
							 * String importHhdceStr = values[13];
							 * csvElement.appendChild(getField("Import DCE",
							 * importHhdceStr)); if
							 * (importHhdceStr.equals(NO_CHANGE)) { if
							 * (existingImportMpan.getHhdceContract() == null) {
							 * throw new UserException( "There isn't an existing
							 * DCE contract"); } else { importHhdce =
							 * existingImportMpan
							 * .getHhdceContract().getProvider(); } } else {
							 * importHhdce = Provider.getProvider(
							 * importHhdceStr, MarketRole.HHDC); }
							 */
							String importHhdcContractName = values[14];
							csvElement.appendChild(getField(
									"Import HHDC Contract",
									importHhdcContractName));
							if (importHhdcContractName.equals(NO_CHANGE)) {
								if (existingImportMpan == null) {
									throw new UserException(
											"There isn't an existing HHDC contract");
								}
								Account account = existingImportMpan
										.getHhdcAccount();
								if (account == null) {
									throw new UserException(
											"There isn't an existing HHDC contract");
								}
								importHhdcContract = HhdcContract
										.getHhdcContract(account.getContract()
												.getId());
							} else {
								importHhdcContract = HhdcContract
										.getHhdcContract(importHhdcContractName);
							}
							String importHhdcAccountReference = values[15];
							csvElement.appendChild(getField(
									"Import HHDC account reference",
									importHhdcAccountReference));
							if (importHhdcAccountReference.equals(NO_CHANGE)) {
								if (existingImportMpan == null) {
									throw new UserException(
											"There isn't an existing import HHDC account");
								}
								Account account = existingImportMpan
										.getHhdcAccount();
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
						String importContractSupplierName = values[16];
						csvElement.appendChild(getField(
								"Import Supplier Contract",
								importContractSupplierName));
						if (importContractSupplierName.equals(NO_CHANGE)) {
							if (existingImportMpan == null) {
								throw new UserException(
										"There isn't an existing import supplier.");
							}
							Account account = existingImportMpan
									.getSupplierAccount();
							if (account == null) {
								throw new UserException(
										"There isn't an existing import supplier.");
							}
							importSupplierContract = SupplierContract
									.getSupplierContract(account.getContract()
											.getId());
						} else {
							importSupplierContract = SupplierContract
									.getSupplierContract(importContractSupplierName);
						}
						String importSupplierAccountReference = values[17];
						csvElement.appendChild(getField(
								"Import Supplier Account Reference",
								importSupplierAccountReference));
						if (importSupplierAccountReference.equals(NO_CHANGE)) {
							if (existingImportMpan == null) {
								throw new UserException(
										"There isn't an existing import supplier account.");
							}
							Account account = existingImportMpan
									.getSupplierAccount();
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
					String exportMpanStr = values[18];
					csvElement
							.appendChild(getField("Eport MPAN", exportMpanStr));
					String exportSscCode = values[19];
					Ssc exportSsc = null;
					boolean exportHasImportKwh = false;
					boolean exportHasImportKvarh = false;
					boolean exportHasExportKwh = false;
					boolean exportHasExportKvarh = false;
					String exportAgreedSupplyCapacityStr = values[20];
					csvElement.appendChild(getField(
							"Export Agreed Supply Capacity",
							exportAgreedSupplyCapacityStr));
					Mpan existingExportMpan = supplyGeneration.getExportMpan();
					Integer exportAgreedSupplyCapacity = null;
					if (exportMpanStr.equals(NO_CHANGE)) {
						exportMpanStr = existingExportMpan == null ? null
								: existingExportMpan.toString();
					}
					Account exportHhdcAccount = null;
					SupplierContract exportSupplierContract = null;
					Account exportAccountSupplier = null;
					if (exportMpanStr != null) {
						if (exportSscCode.equals(NO_CHANGE)) {
							if (existingExportMpan == null) {
								throw new UserException(
										"There isn't an existing export MPAN.");
							} else {
								exportSsc = existingExportMpan.getTop()
										.getSsc();
							}
						} else {
							exportSsc = exportSscCode.length() == 0 ? null
									: Ssc.getSsc(exportSscCode);
						}
						if (exportAgreedSupplyCapacityStr.equals(NO_CHANGE)) {
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
						String exportHasImportKwhStr = values[21];
						csvElement.appendChild(getField("Export is import kWh",
								exportHasImportKwhStr));
						exportHasImportKwh = exportHasImportKwhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasImportKwh()
								: Boolean.parseBoolean(exportHasImportKwhStr);
						String exportHasImportKvarhStr = values[22];
						csvElement.appendChild(getField(
								"Export is import kVArh",
								exportHasImportKvarhStr));
						exportHasImportKvarh = exportHasImportKvarhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasImportKvarh()
								: Boolean.parseBoolean(exportHasImportKvarhStr);
						String exportHasExportKwhStr = values[23];
						csvElement.appendChild(getField("Export is export kWh",
								exportHasExportKwhStr));
						exportHasExportKwh = exportHasExportKwhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasExportKwh()
								: Boolean.parseBoolean(exportHasExportKwhStr);
						String exportHasExportKvarhStr = values[24];
						csvElement.appendChild(getField(
								"Export is export kVArh",
								exportHasExportKvarhStr));
						exportHasExportKvarh = exportHasExportKvarhStr
								.equals(NO_CHANGE) ? existingExportMpan == null ? false
								: existingExportMpan.getHasExportKvarh()
								: Boolean.parseBoolean(exportHasExportKvarhStr);
						HhdcContract exportHhdcContract = null;
						if (exportHasImportKwh || exportHasImportKvarh
								|| exportHasExportKwh || exportHasExportKvarh) {
							String exportHhdcContractName = values[25];
							if (exportHhdcContractName.equals(NO_CHANGE)) {
								if (existingExportMpan == null) {
									throw new UserException(
											"There isn't an existing export HHDC contract.");
								}
								Account account = existingExportMpan
										.getHhdcAccount();
								if (account == null) {
									throw new UserException(
											"There isn't an existing export HHDC contract.");
								}
								exportHhdcContract = HhdcContract
										.getHhdcContract(account.getContract()
												.getId());
							} else {
								exportHhdcContract = HhdcContract
										.getHhdcContract(exportHhdcContractName);
							}
							String exportHhdcAccountReference = values[26];
							csvElement.appendChild(getField(
									"Export HHDC account",
									exportHhdcAccountReference));
							if (exportHhdcAccountReference.equals(NO_CHANGE)) {
								if (existingExportMpan == null) {
									throw new UserException(
											"There isn't an existing export supplier account.");
								}
								Account account = existingExportMpan
										.getHhdcAccount();
								if (account == null) {
									throw new UserException(
											"There isn't an existing export supplier account.");
								}
								exportHhdcAccount = existingExportMpan
										.getHhdcAccount();
							} else {
								exportHhdcAccount = exportHhdcContract
										.getAccount(exportHhdcAccountReference);
							}
						}
						String exportContractSupplierName = values[27];
						csvElement.appendChild(getField(
								"Export Supplier Contract",
								exportContractSupplierName));
						if (exportContractSupplierName.equals(NO_CHANGE)) {
							if (existingExportMpan == null) {
								throw new UserException(
										"There isn't an existing export supplier contract.");
							}
							Account account = existingExportMpan
									.getSupplierAccount();
							if (account == null) {
								throw new UserException(
										"There isn't an existing export supplier contract.");
							}
							exportSupplierContract = SupplierContract
									.getSupplierContract(account.getContract()
											.getId());
						} else {
							exportSupplierContract = SupplierContract
									.getSupplierContract(exportContractSupplierName);
						}
						String exportSupplierAccountReference = values[28];
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
					supplyGeneration.addOrUpdateMpans(importMpanStr, importSsc,
							importHhdcAccount, importSupplierAccount,
							importHasImportKwh, importHasImportKvarh,
							importHasExportKwh, importHasExportKvarh,
							importAgreedSupplyCapacity, exportMpanStr,
							exportSsc, exportHhdcAccount,
							exportAccountSupplier, exportHasImportKwh,
							exportHasImportKvarh, exportHasExportKwh,
							exportHasExportKvarh, exportAgreedSupplyCapacity);
				}
			} else if (type.equals("supplier-account")) {
				if (values.length < 4) {
					throw new UserException(
							"There aren't enough fields in this row");
				}
				String supplierContractName = values[2];
				csvElement.appendChild(getField("Contract",
						supplierContractName));
				SupplierContract supplierContract = SupplierContract
						.getSupplierContract(supplierContractName);
				String supplierAccountReference = values[3];
				csvElement.appendChild(getField("Reference",
						supplierAccountReference));
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
			} else if (type.equals("hhdc-account")) {
				if (values.length < 4) {
					throw new UserException(
							"There aren't enough fields in this row");
				}
				String hhdcContractName = values[2];
				csvElement.appendChild(getField("Contract", hhdcContractName));
				HhdcContract hhdcContract = HhdcContract
						.getHhdcContract(hhdcContractName);
				String hhdcAccountReference = values[3];
				csvElement.appendChild(getField("Reference",
						hhdcAccountReference));
				if (action.equals("insert")) {
					hhdcContract.insertAccount(hhdcAccountReference);
				} else {
					Account hhdcAccount = hhdcContract
							.getAccount(hhdcAccountReference);
					if (action.equals("delete")) {
						hhdcContract.deleteAccount(hhdcAccount);
					} else if (action.equals("update")) {
						String newReference = values[4];
						csvElement.appendChild(getField("New Reference",
								newReference));
						hhdcAccount.update(newReference);
					}
				}
			} else if (type.equals("report")) {
				if (values.length < 5) {
					throw new UserException(
							"There aren't enough fields in this row");
				}
				String name = values[2];
				csvElement.appendChild(getField("Name", name));
				if (action.equals("insert")) {
					String script = values[3];
					csvElement.appendChild(getField("Script", script));
					String template = values[4];
					csvElement.appendChild(getField("Template", template));
					Report.insertReport(name, script, template);
				} else if (action.equals("update")) {
					/*
					 * String script = values[3];
					 * csvElement.appendChild(getField("Script", script));
					 * String template = values[4];
					 * csvElement.appendChild(getField("Template", template));
					 * Report report = Report.getReport(name);
					 */
				}
			} else {
				throw new UserException(
						"The 'Type' field can only "
								+ "be 'site', 'supply', 'hhdc', 'report' or 'supplier-account'.");
			}
		} catch (HttpException e) {
			String message = e.getMessage();
			if (message == null) {
				message = "There has been a problem: "
						+ e.getStackTraceString();
			}
			csvElement.appendChild(new MonadMessage(message).toXml(doc));
			source.appendChild(csvElement);
			throw e;
		}
	}

	private Element getField(String name, String value) {
		Element field = doc.createElement("Field");
		field.setAttribute("name", name);
		field.setTextContent(value);
		return field;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException {
		return uri;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document document = (Document) doc.cloneNode(true);
		Element source = document.getDocumentElement();
		Element processElement = toXml(document);
		source.appendChild(processElement);
		for (MonadMessage message : errors) {
			source.appendChild(message.toXml(document));
		}
		Hiber.close();
		inv.sendOk(document);
	}

	public void httpPost(Invocation inv) throws HttpException {
		halt();
		inv.sendSeeOther(getUri());
	}

	public void httpDelete(Invocation inv) throws HttpException {
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("general-import");
		element.setAttribute("uri", uri.toString());
		element.setAttribute("id", getUriId().toString());
		if (isAlive()) {
			element.setAttribute("progress", "Reached line number "
					+ getLineNumber() + ".");
		}
		return element;
	}

	public List<MonadMessage> getErrors() {
		return errors;
	}

	public UriPathElement getUriId() throws HttpException {
		String uriString = uri.toString();
		uriString = uriString.substring(0, uriString.length() - 1);
		return new UriPathElement(uriString.substring(uriString
				.lastIndexOf("/") + 1));
	}

	public Node toXml(Document doc, XmlTree tree) throws HttpException {
		return null;
	}

	private class Digester {
		private CSVParser shredder = null;
		private XMLEventReader r;

		Digester(Reader reader, String extension) throws HttpException {
			if (extension.equals("csv")) {
				shredder = new CSVParser(reader);
				shredder.setCommentStart("#;!");
				shredder.setEscapes("nrtf", "\n\r\t\f");

			} else if (extension.equals("xml")) {
				XMLInputFactory factory = XMLInputFactory.newInstance();
				try {
					r = factory.createXMLEventReader(reader);
				} catch (XMLStreamException e) {
					throw new InternalException(e);
				}
			} else {
				throw new UserException("The file extension was '" + extension
						+ "' but only csv or xml is recognized.");
			}
		}

		/*
		 * public int getLineNumber() throws HttpException { return lineNumber;
		 * 
		 * if (shredder == null) { try { return
		 * r.peek().getLocation().getLineNumber(); } catch (XMLStreamException
		 * e) { throw new InternalException(e); } } else { return
		 * shredder.getLastLineNumber(); } }
		 */

		public String[] getLine() throws HttpException {
			if (shredder == null) {
				Debug.print("starting to get a line.");
				List<String> values = new ArrayList<String>();
				if (r.hasNext()) {
					try {
						boolean inValue = false;
						XMLEvent e = r.nextEvent();
						lineNumber = e.getLocation().getLineNumber();
						StringBuilder value = null;
						while (!e.isEndDocument()
								&& !(e.isEndElement() && e.asEndElement()
										.getName().getLocalPart()
										.equals("line"))) {
							if (e.isStartElement()
									&& e.asStartElement().getName()
											.getLocalPart().equals("value")) {
								value = new StringBuilder();
								inValue = true;
							} else if (e.isEndElement()
									&& e.asEndElement().getName()
											.getLocalPart().equals("value")) {
								values.add(value.toString());
								inValue = false;
							} else if (inValue && e.isCharacters()) {
								Debug.print("Adding value "
										+ e.asCharacters().getData());
								value.append(e.asCharacters().getData());
							}
							e = r.nextEvent();
							lineNumber = e.getLocation().getLineNumber();
						}
					} catch (XMLStreamException e) {
						throw new InternalException(e);
					}
				}
				Debug.print("finish getting a line");
				if (values.isEmpty()) {
					return null;
				} else {
					return values.toArray(new String[0]);
				}
			} else {
				try {
					String[] line = shredder.getLine();
					lineNumber = shredder.getLastLineNumber();
					return line;
				} catch (IOException e) {
					throw new InternalException(e);
				}
			}
		}
	}
}