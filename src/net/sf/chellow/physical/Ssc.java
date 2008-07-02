package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import com.Ostermiller.util.CSVParser;

public class Ssc extends PersistentEntity {
	public static Ssc insertSsc(String code, Date from, Date to,
			String description, boolean isImport) throws InternalException,
			HttpException {
		Ssc ssc = new Ssc(code, from, to, description, isImport);
		Hiber.session().save(ssc);
		Hiber.flush();
		return ssc;
	}

	public static Ssc getSsc(String code) throws HttpException,
			InternalException {
		Ssc ssc = (Ssc) Hiber.session().createQuery(
				"from Ssc ssc where ssc.code = :code").setString("code", code)
				.uniqueResult();
		if (ssc == null) {
			throw new UserException("There isn't an SSC with code: " + code
					+ ".");
		}
		return ssc;
	}

	public static Ssc getSsc(long id) throws HttpException, InternalException {
		Ssc ssc = (Ssc) Hiber.session().get(Ssc.class, id);
		if (ssc == null) {
			throw new UserException("There isn't an SSC with id: " + id + ".");
		}
		return ssc;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Participant.class.getClassLoader();
			CSVParser parser = new CSVParser(
					new InputStreamReader(
							classLoader
									.getResource(
											"net/sf/chellow/physical/StandardSettlementConfiguration.csv")
									.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length < 7
					|| !titles[0].trim().equals(
							"Standard Settlement Configuration Id")
					|| !titles[1].trim().equals(
							"Effective From Settlement Date {SSC}")
					|| !titles[2].trim().equals(
							"Effective To Settlement Date {SSC}")
					|| !titles[3].trim().equals(
							"Standard Settlement Configuration Desc")
					|| !titles[4].trim().equals(
							"Standard Settlement Configuraton Type")
					|| !titles[5].trim().equals("Teleswitch User Id")
					|| !titles[6].trim().equals("Teleswitch Group Id")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Standard Settlement Configuration Id , Effective From Settlement Date {SSC}, Effective To Settlement Date {SSC}, Standard Settlement Configuration Desc, Standard Settlement Configuraton Type, Teleswitch User Id, Teleswitch Group Id");
			}
			SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy",
					Locale.UK);
			dateFormat.setCalendar(new GregorianCalendar(TimeZone
					.getTimeZone("GMT"), Locale.UK));
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				String toStr = values[2];
				insertSsc(values[0], dateFormat.parse(values[1]), toStr
						.length() == 0 ? null : dateFormat.parse(toStr),
						values[3], values[4].equals("I"));
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private String code;
	private Date validFrom;
	private Date validTo;
	private String description;
	private boolean isImport;
	private Set<MeasurementRequirement> mrs;

	public Ssc() {
	}

	public Ssc(String code, Date validFrom, Date validTo, String description,
			boolean isImport) throws HttpException {
		setCode(code);
		setValidFrom(validFrom);
		setValidTo(validTo);
		setDescription(description);
		setIsImport(isImport);
	}

	public String getCode() {
		return code;
	}

	void setCode(String code) {
		this.code = code;
	}

	public Date getValidFrom() {
		return validFrom;
	}

	void setValidFrom(Date validFrom) {
		this.validFrom = validFrom;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date validTo) {
		this.validTo = validTo;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public boolean getIsImport() {
		return isImport;
	}

	void setIsImport(boolean isImport) {
		this.isImport = isImport;
	}

	public Set<MeasurementRequirement> getMeasurementRequirements() {
		return mrs;
	}

	void setMeasurementRequirements(Set<MeasurementRequirement> mrs) {
		this.mrs = mrs;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("measurementRequirements",
				new XmlTree("tpr"))));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		setTypeName("ssc");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		MonadDate fromDate = new MonadDate(validFrom);
		fromDate.setLabel("from");
		element.appendChild(fromDate.toXml(doc));
		if (validTo != null) {
			MonadDate toDate = new MonadDate(validTo);
			toDate.setLabel("to");
			element.appendChild(toDate.toXml(doc));
		}
		return element;
	}

	public MeasurementRequirement insertMeasurementRequirement(Tpr tpr)
			throws HttpException {
		MeasurementRequirement mr = new MeasurementRequirement(this, tpr);
		Hiber.session().save(mr);
		Hiber.session().flush();
		return mr;
	}
}
