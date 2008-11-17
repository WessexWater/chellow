package net.sf.chellow.ui;

import java.io.IOException;
import java.io.Reader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.logging.Level;

import javax.xml.stream.XMLEventReader;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.events.XMLEvent;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.SupplierContract;
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
import net.sf.chellow.physical.Site;
import net.sf.chellow.physical.SiteSupplyGeneration;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplyGeneration;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class GeneralImport extends Thread implements Urlable, XmlDescriber {
	public static final String NO_CHANGE = "{no change}";

	private boolean halt = false;

	private Document doc = MonadUtils.newSourceDocument();

	private Element source = doc.getDocumentElement();
	Element csvElement = null;
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
			//errors.add(new MonadMessage(
			//		"There are errors that need to be corrected before "
			//				+ "the file can be imported."));
			if (csvElement != null) {
				source.appendChild(csvElement);
			}
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

	private void processItem(String[] allValues) throws HttpException {
		String action = allValues[0].trim().toLowerCase();
		String type = allValues[1].trim().toLowerCase();
		csvElement = doc.createElement("csvLine");
		// try {
		csvElement.setAttribute("number", String.valueOf(lineNumber));
		addField(csvElement, "Action", allValues[0]);
		addField(csvElement, "Type", allValues[1]);
		if (!action.equals("insert") && !action.equals("update")
				&& !action.equals("delete")) {
			throw new UserException("The 'Action' field can "
					+ "only be 'insert', 'update', 'delete'.");
		}
		String[] values = Arrays.copyOfRange(allValues, 2, allValues.length);
		if (type.equals("site")) {
			Site.generalImport(action, values, csvElement);
		} else if (type.equals("site-supply-generation")) {
			SiteSupplyGeneration.generalImport(action, values, csvElement);
		} else if (type.equals("supply")) {
			Supply.generalImport(action, values, csvElement);
		} else if (type.equals("supply-generation")) {
			SupplyGeneration.generalImport(action, values, csvElement);
		} else if (type.equals("supplier-account")) {
			Account.generalImportSupplier(action, values, csvElement);
		} else if (type.equals("hhdc-account")) {
			Account.generalImportHhdc(action, values, csvElement);
		} else if (type.equals("report")) {
			Report.generalImport(action, values, csvElement);
		} else if (type.equals("hhdc-contract")) {
			HhdcContract.generalImport(action, values, csvElement);
		} else if (type.equals("supplier-contract")) {
			SupplierContract.generalImport(action, values, csvElement);
		} else if (type.equals("hh-datum")) {
			HhDatum.generalImport(action, values, csvElement);
		} else {
			throw new UserException(
					"The 'Type' field can only "
							+ "be 'site', 'supply', 'hhdc', 'report' or 'supplier-account'.");
		}
	}

	public static String addField(Element csvElement, String name, String value) {
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