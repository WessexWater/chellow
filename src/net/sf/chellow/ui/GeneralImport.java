package net.sf.chellow.ui;

import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.logging.Level;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import javax.xml.stream.XMLEventReader;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.events.XMLEvent;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.DsoContract;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.NonCoreContract;
import net.sf.chellow.billing.RateScript;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.hhimport.HhDatumRaw;
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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhDatum;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Site;
import net.sf.chellow.physical.SiteSupplyGeneration;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.physical.User;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class GeneralImport extends Thread implements Urlable, XmlDescriber {
	public static void printXmlLine(PrintWriter pw, String[] values) {
		pw.println("  <line>");
		for (String value : values) {
			pw.println("    <value><![CDATA["
					+ value.replace("<![CDATA[", "&lt;![CDATA[").replace("]]>",
							"]]&gt;") + "]]></value>");
		}
		pw.println("  </line>");
	}

	public static final String NO_CHANGE = "{no change}";

	private boolean halt = false;

	private Document doc = MonadUtils.newSourceDocument();

	private Element source = doc.getDocumentElement();

	Element csvElement = null;

	private List<MonadMessage> errors = new ArrayList<MonadMessage>();

	private Digester digester;

	private int lineNumber;

	private MonadUri uri;

	public GeneralImport(MonadUri uri, InputStream is, String extension)
			throws HttpException {
		super("Import");
		this.uri = uri;
		if (extension.equals("zip")) {
			ZipInputStream zin;
			try {
				zin = new ZipInputStream(new BufferedInputStream(is));
				ZipEntry entry = zin.getNextEntry();
				if (entry == null) {
					throw new UserException(null,
							"Can't find an entry within the zip file.");
				} else {
					is = zin;
					String name = entry.getName();
					extension = name.substring(name.length() - 3);
				}
			} catch (IOException e) {
				throw new InternalException(e);
			}
		}
		Reader reader;
		try {
			reader = new InputStreamReader(is, "UTF-8");
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		}
		digester = new Digester(reader, extension);
		String[] titles = digester.getLine();

		if (titles.length < 2
				|| !titles[0].trim().toLowerCase().equals("action")
				|| !titles[1].trim().toLowerCase().equals("type")) {
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
		long totalHhTime = 0;
		List<Boolean> halt = Collections
				.synchronizedList(new ArrayList<Boolean>());
		halt.add(false);
		try {
			String[] allValues = digester.getLine();
			List<HhDatumRaw> hhData = new ArrayList<HhDatumRaw>();
			while (allValues != null && !shouldHalt()) {
				if (allValues.length < 2) {
					throw new UserException(
							"There must be an 'Action' field followed "
									+ "by a 'Type' field.");
				}
				String action = allValues[0].trim().toLowerCase();
				String type = allValues[1].trim().toLowerCase();
				if (type.equals("hh-datum")) {
					try {
						long startProchh = System.currentTimeMillis();
						// Debug.print("Type is hh-datum");
						if (action.equals("insert")) {
							String mpanCore = allValues[2];
							boolean isImport = Boolean
									.parseBoolean(allValues[4]);
							boolean isKwh = Boolean.parseBoolean(allValues[5]);
							HhEndDate endDate = new HhEndDate(allValues[3]);
							String hhString = allValues[6].trim();
							if (hhString.endsWith(",")) {
								hhString = hhString + " ";
							}
							String[] vals = hhString.split(",");
							if (vals.length % 2 != 0) {
								throw new UserException("There must be an even number of values in the list of hh data.");
							}
							for (int i = 0; i < vals.length; i += 2) {
								// Debug.print("action is insert");
								String bigDecimal = vals[i];
								if (bigDecimal.length() > 0) {
									Character status = null;
									String statusString = vals[i + 1].trim();
									if (statusString.length() > 0) {
										status = statusString.charAt(0);
									}
									hhData
											.add(new HhDatumRaw(mpanCore,
													isImport, isKwh, endDate,
													new BigDecimal(bigDecimal),
													status));
								}
								// Debug.print("size " + hhData.size());
								endDate = endDate.getNext();
							}
							HhDatum.insert(hhData.iterator(), halt);
							hhData.clear();
						}
						/*
						 * else { HhDatum.generalImport(action, allValues); }
						 */
						totalHhTime = totalHhTime + System.currentTimeMillis()
								- startProchh;
					} catch (UserException e) {
						StringBuilder message = new StringBuilder(
								"Problem loading a HH datum with values: ");
						for (String value : allValues) {
							message.append(value + ", ");
						}
						throw new UserException(message + ". Message: "
								+ e.getMessage());
					}
				} else {
					csvElement = doc.createElement("csvLine");
					// try {
					addField(csvElement, "Action", allValues, 0);
					addField(csvElement, "Type", allValues, 1);
					if (!action.equals("insert") && !action.equals("update")
							&& !action.equals("delete")) {
						throw new UserException("The 'Action' field can "
								+ "only be 'insert', 'update', 'delete'.");
					}
					String[] values = Arrays.copyOfRange(allValues, 2,
							allValues.length);

					if (type.equals("site")) {
						Site.generalImport(action, values, csvElement);
					} else if (type.equals("site-supply-generation")) {
						SiteSupplyGeneration.generalImport(action, values,
								csvElement);
					} else if (type.equals("supply")) {
						Supply.generalImport(action, values, csvElement);
					} else if (type.equals("supply-generation")) {
						SupplyGeneration.generalImport(action, values,
								csvElement);
					} else if (type.equals("supplier-account")) {
						Account.generalImportSupplier(action, values,
								csvElement);
					} else if (type.equals("hhdc-account")) {
						Account.generalImportHhdc(action, values, csvElement);
					} else if (type.equals("report")) {
						Report.generalImport(action, values, csvElement);
					} else if (type.equals("hhdc-contract")) {
						HhdcContract.generalImport(action, values, csvElement);
					} else if (type.equals("hhdc-contract-rate-script")) {
						RateScript
								.generalImportHhdc(action, values, csvElement);
					} else if (type.equals("non-core-contract")) {
						NonCoreContract.generalImport(action, values,
								csvElement);
					} else if (type.equals("non-core-contract-rate-script")) {
						RateScript.generalImportNonCore(action, values,
								csvElement);
					} else if (type.equals("supplier-contract")) {
						SupplierContract.generalImport(action, values,
								csvElement);
					} else if (type.equals("supplier-contract-rate-script")) {
						RateScript.generalImportSupplier(action, values,
								csvElement);
					} else if (type.equals("user")) {
						User.generalImport(action, values, csvElement);
					} else if (type.equals("dso-contract")) {
						DsoContract.generalImport(action, values, csvElement);
					} else if (type.equals("dso-contract-rate-script")) {
						RateScript.generalImportDso(action, values, csvElement);
					} else {
						throw new UserException("The type " + type
								+ " isn't recognized.");
					}
					csvElement = null;
				}
				Hiber.close();
				allValues = digester.getLine();
			}

			if (!hhData.isEmpty()) {
				// Debug.print("not empty, so adding.");
				HhDatum.insert(hhData.iterator(), halt);
				Hiber.close();
			}

			if (shouldHalt()) {
				errors.add(new MonadMessage("The import has been cancelled."));
			} else {
				source.appendChild(new MonadMessage(
						"The file has been imported successfully.").toXml(doc));
			}
		} catch (HttpException e) {
			String message = e.getMessage();
			if (message == null) {
				message = HttpException.getStackTraceString(e);
			}
			errors.add(new MonadMessage(message));
			// errors.add(new MonadMessage(
			// "There are errors that need to be corrected before "
			// + "the file can be imported."));
			if (csvElement != null) {
				csvElement.setAttribute("number", String.valueOf(lineNumber));
				source.appendChild(csvElement);
			}
			if (e instanceof InternalException) {
				ChellowLogger.getLogger().log(Level.SEVERE,
						"From header import process", e);
			}
		} catch (Throwable e) {
			errors.add(new MonadMessage("Programmer Exception: "
					+ HttpException.getStackTraceString(e)));
			ChellowLogger.getLogger().log(Level.SEVERE,
					"From header import process", e);
		} finally {
			Hiber.rollBack();
			Hiber.close();
		}
		// Debug.print("TotalTimeHH " + totalHhTime);
	}

	public static String addField(Element csvElement, String name,
			String[] values, int index) throws HttpException {
		if (index > values.length - 1) {
			throw new UserException("Another field called " + name
					+ " needs to be added on the end.");
		}
		String value = values[index];
		Document doc = csvElement.getOwnerDocument();
		Element field = doc.createElement("Field");
		csvElement.appendChild(field);
		field.setAttribute("name", name);
		field.setTextContent(value);
		return value;
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
								values.add(value.toString().replace(
										"&lt;![CDATA[", "<![CDATA[").replace(
										"]]&gt;", "]]>"));
								inValue = false;
							} else if (inValue && e.isCharacters()) {
								value.append(e.asCharacters().getData());
							}
							e = r.nextEvent();
							lineNumber = e.getLocation().getLineNumber();
						}
					} catch (XMLStreamException e) {
						throw new InternalException(e);
					}
				}
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