package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
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

import com.Ostermiller.util.CSVParser;

public class ClockInterval extends PersistentEntity {
	static public Tpr findTpr(int code) {
		return (Tpr) Hiber.session().createQuery(
				"from Tpr tpr where tpr.code = :code").setInteger("code", code)
				.uniqueResult();
	}

	static public Tpr getTpr(String code) throws InternalException,
			UserException {
		try {
			return getTpr(Integer.parseInt(code));
		} catch (NumberFormatException e) {
			throw new UserException("Problem parsing code: " + e.getMessage());
		}
	}

	static public Tpr getTpr(int code) throws InternalException, UserException {
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

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Participant.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource("net/sf/chellow/physical/ClockInterval.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length < 8
					|| !titles[0].trim().equals("Time Pattern Regime Id")
					|| !titles[1].trim().equals("Day of the Week Id")
					|| !titles[2].trim().equals("Start Day")
					|| !titles[3].trim().equals("Start Month")
					|| !titles[4].trim().equals("End Day")
					|| !titles[5].trim().equals("End Month")
					|| !titles[6].trim().equals("Start Time")
					|| !titles[7].trim().equals("End Time")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Time Pattern Regime Id, Day of the Week Id, Start Day, Start Month, End Day, End Month, Start Time, End Time");
			}
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Hiber.session().save(
						new ClockInterval(Tpr.getTpr(values[0]), Integer
								.parseInt(values[1]), Integer
								.parseInt(values[2]), Integer
								.parseInt(values[3]), Integer
								.parseInt(values[4]), Integer
								.parseInt(values[5]), Integer
								.parseInt(values[6].substring(0, 2)), Integer
								.parseInt(values[6].substring(3)), Integer
								.parseInt(values[7].substring(0, 2)), Integer
								.parseInt(values[7].substring(3))));
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
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

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("sscs").put("lines")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("clock-interval");
		Element element = (Element) super.toXml(doc);
		element.setAttribute("day-of-week", String.valueOf(dayOfWeek));
		element.setAttribute("start-date", String.valueOf(startDay));
		element.setAttribute("start-date", String.valueOf(startDay));
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