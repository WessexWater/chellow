package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.text.DateFormat;
import java.text.ParseException;
import java.util.Date;
import java.util.Locale;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
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

	static public Ssc getSsc(String code) throws HttpException,
			InternalException {
		try {
			return getSsc(Integer.parseInt(code.trim()));
		} catch (NumberFormatException e) {
			throw new UserException("Problem parsing code: " + e.getMessage());
		}
	}

	public static Ssc getSsc(int code) throws HttpException, InternalException {
		Ssc ssc = (Ssc) Hiber.session().createQuery(
				"from Ssc ssc where ssc.code = :code").setInteger("code", code)
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
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				insertSsc(values[0], dateFormat.parse(values[1]), dateFormat
						.parse(values[2]), values[3], values[4].equals("I"));
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

	private Date from;
	private Date to;
	private String description;
	private boolean isImport;
	private Set<MeasurementRequirement> mrs;

	public Ssc() {
	}

	public Ssc(String code, Date from, Date to, String description,
			boolean isImport) throws InternalException, HttpException {
		setCode(code);
		setFrom(from);
		setTo(to);
		setDescription(description);
		setIsImport(isImport);
		// setTprs(new HashSet<Tpr>());
		// if (tprString != null && tprString.trim().length() > 0) {
		// for (String tprCode : tprString.split(",")) {
		// Tpr tpr = Tpr.getTpr(tprCode);
		// tprs.add(tpr);
		// }
		// }
	}

	public String getCode() {
		return code;
	}

	void setCode(String code) {
		this.code = code;
	}

	public Date getFrom() {
		return from;
	}

	void setFrom(Date from) {
		this.from = from;
	}

	public Date getTo() {
		return to;
	}

	void setTo(Date to) {
		this.to = to;
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

	/*
	 * public Set<Tpr> getTprs() { return tprs; }
	 * 
	 * void setTprs(Set<Tpr> tprs) { this.tprs = tprs; }
	 */
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

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("tprs")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		setTypeName("ssc");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code.toString());
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
