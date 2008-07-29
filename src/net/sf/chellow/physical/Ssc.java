package net.sf.chellow.physical;

import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Date;
import java.util.Set;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
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

public class Ssc extends PersistentEntity {
	public static Ssc getSsc(String code) throws HttpException {
		// canonicalize
		int codeInt = Integer.parseInt(code);
		NumberFormat numberFormat = new DecimalFormat("0000");
		String codeStr = numberFormat.format(codeInt);
		Ssc ssc = (Ssc) Hiber.session().createQuery(
				"from Ssc ssc where ssc.code = :code").setString("code",
				codeStr).uniqueResult();
		if (ssc == null) {
			throw new UserException("There isn't an SSC with code: " + code
					+ ".");
		}
		return ssc;
	}

	public static Ssc getSsc(long id) throws HttpException {
		Ssc ssc = (Ssc) Hiber.session().get(Ssc.class, id);
		if (ssc == null) {
			throw new UserException("There isn't an SSC with id: " + id + ".");
		}
		return ssc;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add SSCs.");
		Mdd mdd = new Mdd(sc, "StandardSettlementConfiguration", new String[] {
				"Standard Settlement Configuration Id",
				"Effective From Settlement Date {SSC}",
				"Effective To Settlement Date {SSC}",
				"Standard Settlement Configuration Desc",
				"Standard Settlement Configuraton Type", "Teleswitch User Id",
				"Teleswitch Group Id" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Ssc ssc = new Ssc(values[0], mdd.toDate(values[1]), mdd
					.toDate(values[2]), values[3], values[4].equals("I"));
			Hiber.session().save(ssc);
			Hiber.close();
		}
		Debug.print("Finished adding SSCs.");
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

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "ssc");

		element.setAttribute("code", code);
		element.setAttribute("is-import", Boolean.toString(isImport));
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
