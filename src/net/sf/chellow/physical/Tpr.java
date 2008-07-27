package net.sf.chellow.physical;

import java.util.HashSet;
import java.util.Set;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Tpr extends PersistentEntity {
	static public Tpr findTpr(String code) {
		return (Tpr) Hiber.session().createQuery(
				"from Tpr tpr where tpr.code = :code").setString("code", code)
				.uniqueResult();
	}

	static public Tpr getTpr(String code) throws HttpException {
		Tpr tpr = findTpr(code);
		if (tpr == null) {
			throw new UserException("Can't find a TPR with code '" + code
					+ "'.");
		}
		return tpr;
	}

	static public Tpr getTpr(long id) throws NotFoundException,
			InternalException {
		Tpr tpr = (Tpr) Hiber.session().get(Tpr.class, id);
		if (tpr == null) {
			throw new NotFoundException();
		}
		return tpr;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add TPRs.");
		Mdd mdd = new Mdd(sc, "TimePatternRegime", new String[] {
				"Time Pattern Regime Id", "Tele-switch/Clock Indicator",
				"GMT Indicator" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Hiber.session().save(
					new Tpr(values[0], values[1].equals("S"), values[2]
							.equals("Y")));
			Hiber.close();
		}
		Debug.print("Finished adding TPRs.");
	}

	private String code;
	private boolean isTeleswitch;
	private boolean isGmt;

	private Set<ClockInterval> clockIntervals;

	private Set<MeasurementRequirement> measurementRequirements;

	public Tpr() {
	}

	public Tpr(String code, boolean isTeleswitch, boolean isGmt) {
		setClockIntervals(new HashSet<ClockInterval>());
		setCode(code);
		setIsTeleswitch(isTeleswitch);
		setIsGmt(isGmt);
	}

	public Set<ClockInterval> getClockIntervals() {
		return clockIntervals;
	}

	void setClockIntervals(Set<ClockInterval> clockIntervals) {
		this.clockIntervals = clockIntervals;
	}

	public Set<MeasurementRequirement> getMeasurementRequirements() {
		return measurementRequirements;
	}

	void setMeasurementRequirements(
			Set<MeasurementRequirement> measurementRequirements) {
		this.measurementRequirements = measurementRequirements;
	}

	String getCode() {
		return code;
	}

	void setCode(String code) {
		this.code = code;
	}

	public boolean getIsTeleswitch() {
		return isTeleswitch;
	}

	void setIsTeleswitch(boolean isTeleswitch) {
		this.isTeleswitch = isTeleswitch;
	}

	public boolean getIsGmt() {
		return isGmt;
	}

	void setIsGmt(boolean isGmt) {
		this.isGmt = isGmt;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (ClockIntervals.URI_ID.equals(uriId)) {
			return new ClockIntervals(this);
		} else {
			throw new NotFoundException();
		}
	}

	public MonadUri getUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("measurementRequirements",
				new XmlTree("ssc")).put("clockIntervals")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public ClockInterval insertClockInterval(int dayOfWeek, int startDay,
			int startMonth, int endDay, int endMonth, int startHour,
			int startMinute, int endHour, int endMinute) {
		ClockInterval interval = new ClockInterval(this, dayOfWeek, startDay,
				startMonth, endDay, endMonth, startHour, startMinute, endHour,
				endMinute);
		Hiber.session().save(interval);
		Hiber.session().flush();
		return interval;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "tpr");

		element.setAttribute("code", code);
		element.setAttribute("is-teleswitch", String.valueOf(isTeleswitch));
		element.setAttribute("is-gmt", String.valueOf(isGmt));
		return element;
	}

	public String toString() {
		return "Code: " + code + " Is Teleswitch?: " + isTeleswitch
				+ " Is GMT?: " + isGmt;
	}
}
