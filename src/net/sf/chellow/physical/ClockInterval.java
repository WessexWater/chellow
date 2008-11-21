package net.sf.chellow.physical;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ClockInterval extends PersistentEntity {
	static public ClockInterval getClockInterval(long id) throws HttpException {
		ClockInterval interval = (ClockInterval) Hiber.session().get(
				ClockInterval.class, id);
		if (interval == null) {
			throw new NotFoundException();
		}
		return interval;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Clock Intervals.");
		Mdd mdd = new Mdd(sc, "ClockInterval",
				new String[] { "Time Pattern Regime Id", "Day of the Week Id",
						"Start Day", "Start Month", "End Day", "End Month",
						"Start Time", "End Time" });
		String tprCode = null;
		Tpr tpr = null;
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			String newTprCode = values[0];
			if (!newTprCode.equals(tprCode)) {
				tpr = Tpr.getTpr(newTprCode);
				tprCode = newTprCode;
			}
			tpr.insertClockInterval(Integer.parseInt(values[1]), Integer
					.parseInt(values[2]), Integer.parseInt(values[3]), Integer
					.parseInt(values[4]), Integer.parseInt(values[5]), Integer
					.parseInt(values[6].substring(0, 2)), Integer
					.parseInt(values[6].substring(3)), Integer
					.parseInt(values[7].substring(0, 2)), Integer
					.parseInt(values[7].substring(3)));
			Hiber.close();
		}
		Debug.print("Finished adding Clock Intervals.");
	}

	private Tpr tpr;
	private int dayOfWeek;
	private int startDay;
	private int startMonth;
	private int endDay;
	private int endMonth;
	private int startHour;
	private int startMinute;
	private int endHour;
	private int endMinute;

	public ClockInterval() {
	}

	public ClockInterval(Tpr tpr, int dayOfWeek, int startDay, int startMonth,
			int endDay, int endMonth, int startHour, int startMinute,
			int endHour, int endMinute) {
		setTpr(tpr);
		setDayOfWeek(dayOfWeek);
		setStartDay(startDay);
		setStartMonth(startMonth);
		setEndDay(endDay);
		setEndMonth(endMonth);
		setStartHour(startHour);
		setStartMinute(startMinute);
		setEndHour(endHour);
		setEndMinute(endMinute);
	}

	public Tpr getTpr() {
		return tpr;
	}

	void setTpr(Tpr tpr) {
		this.tpr = tpr;
	}

	public int getDayOfWeek() {
		return dayOfWeek;
	}

	void setDayOfWeek(int dayOfWeek) {
		this.dayOfWeek = dayOfWeek;
	}

	public int getStartDay() {
		return startDay;
	}

	void setStartDay(int startDay) {
		this.startDay = startDay;
	}

	public int getStartMonth() {
		return startMonth;
	}

	void setStartMonth(int startMonth) {
		this.startMonth = startMonth;
	}

	public int getEndDay() {
		return endDay;
	}

	void setEndDay(int endDay) {
		this.endDay = endDay;
	}

	public int getEndMonth() {
		return endMonth;
	}

	void setEndMonth(int endMonth) {
		this.endMonth = endMonth;
	}

	public int getStartHour() {
		return startHour;
	}

	void setStartHour(int startHour) {
		this.startHour = startHour;
	}

	public int getStartMinute() {
		return startMinute;
	}

	void setStartMinute(int startMinute) {
		this.startMinute = startMinute;
	}

	public int getEndHour() {
		return endHour;
	}

	void setEndHour(int endHour) {
		this.endHour = endHour;
	}

	public int getEndMinute() {
		return endMinute;
	}

	void setEndMinute(int endMinute) {
		this.endMinute = endMinute;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getUri() throws InternalException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("tpr")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "clock-interval");
		element.setAttribute("day-of-week", String.valueOf(dayOfWeek));
		element.setAttribute("start-day", String.valueOf(startDay));
		element.setAttribute("start-month", String.valueOf(startMonth));
		element.setAttribute("end-day", String.valueOf(endDay));
		element.setAttribute("end-month", String.valueOf(endMonth));
		element.setAttribute("start-hour", String.valueOf(startHour));
		element.setAttribute("start-minute", String.valueOf(startMinute));
		element.setAttribute("end-hour", String.valueOf(endHour));
		element.setAttribute("end-minute", String.valueOf(endMinute));
		return element;
	}
}