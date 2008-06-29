/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.physical;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.text.DateFormat;
import java.text.ParseException;
import java.util.Date;
import java.util.List;
import java.util.Locale;

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
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class Llfc extends PersistentEntity {
	static public Llfc getLlf(Long id) throws InternalException, HttpException {
		Llfc llf = (Llfc) Hiber.session().get(Llfc.class, id);
		if (llf == null) {
			throw new UserException("There is no mpan generation with that id.");
		}
		return llf;
	}

	@SuppressWarnings("unchecked")
	static public List<Llfc> find(Dso dso, Pc profileClass,
			boolean isSubstation, boolean isImport, VoltageLevel voltageLevel)
			throws InternalException, HttpException {
		try {
			return (List<Llfc>) Hiber
					.session()
					.createQuery(
							"from Llf llf where llf.dso = :dso and llf.profileClass = :profileClass and llf.isSubstation.boolean = :isSubstation and llf.isImport.boolean = :isImport and llf.voltageLevel = :voltageLevel")
					.setEntity("dso", dso).setEntity("profileClass",
							profileClass).setBoolean("isSubstation",
							isSubstation).setBoolean("isImport", isImport)
					.setEntity("voltageLevel", voltageLevel).list();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	@SuppressWarnings("unchecked")
	static public List<Llfc> find(Dso dso, Pc profileClass)
			throws InternalException, HttpException {
		try {
			return (List<Llfc>) Hiber
					.session()
					.createQuery(
							"from Llf llf where llf.dso = :dso and llf.profileClass = :profileClass order by llf.code.string")
					.setEntity("dso", dso).setEntity("profileClass",
							profileClass).list();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Llfc.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource(
							"net/sf/chellow/physical/LineLossFactorClass.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 4
					|| !titles[0].trim().equals("Market Participant Id")
					|| !titles[1].trim().equals("Market Participant Role Code")
					|| !titles[2].trim().equals("Effective From Date {MPR}")
					|| !titles[3].trim().equals("Line Loss Factor Class Id")
					|| !titles[4].trim().equals(
							"Effective From Settlement Date {LLFC}")
					|| !titles[5].trim().equals(
							"Line Loss Factor Class Description")
					|| !titles[6].trim().equals(
							"MS Specific LLF Class Indicator")
					|| !titles[7].trim().equals(
							"Effective To Settlement Date {LLFC}")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Market Participant Id, Market Participant Role Code, Effective From Date {MPR}, Line Loss Factor Class Id, Effective From Settlement Date {LLFC}, Line Loss Factor Class Description, MS Specific LLF Class Indicator, Effective To Settlement Date {LLFC}.");
			}
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				String participantCode = values[0];
				String description = values[5];
				VoltageLevel vLevel = null;
				if (description.contains(VoltageLevel.EHV)) {
					vLevel = VoltageLevel.getVoltageLevel(VoltageLevel.EHV);
				} else if (description.contains(VoltageLevel.HV)) {
					vLevel = VoltageLevel.getVoltageLevel(VoltageLevel.HV);
				} else {
					vLevel = VoltageLevel.getVoltageLevel(VoltageLevel.LV);
				}
				boolean isSubstation = (participantCode.equals("SWEB") && description
						.contains("S/S"))
						|| (!participantCode.equals("SWEB") && description
								.contains("sub"));
				String indicator = values[6];
				boolean isImport = indicator.equals("A")
						|| indicator.equals("B");
				Hiber.session().save(
						new Llfc(Dso.getDso(participantCode), Integer
								.parseInt(values[3]), description, vLevel,
								isSubstation, isImport, dateFormat
										.parse(values[2]), dateFormat
										.parse(values[4])));
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (NumberFormatException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private Dso dso;

	private LlfcCode code;

	private String description;

	private VoltageLevel voltageLevel;

	private boolean isSubstation;

	private boolean isImport;

	private Date from;
	private Date to;

	Llfc() {
	}

	public Llfc(Dso dso, int code, String description,
			VoltageLevel voltageLevel, boolean isSubstation, boolean isImport,
			Date from, Date to) throws HttpException {
		setDso(dso);
		setCode(new LlfcCode(code));
		setDescription(description);
		setVoltageLevel(voltageLevel);
		setIsSubstation(isSubstation);
		setIsImport(isImport);
		setFrom(from);
		setTo(to);
	}

	public Dso getDso() {
		return dso;
	}

	public void setDso(Dso dso) {
		this.dso = dso;
	}

	public LlfcCode getCode() {
		return code;
	}

	void setCode(LlfcCode code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public VoltageLevel getVoltageLevel() {
		return voltageLevel;
	}

	public void setVoltageLevel(VoltageLevel voltageLevel) {
		this.voltageLevel = voltageLevel;
	}

	public boolean getIsSubstation() {
		return isSubstation;
	}

	public void setIsSubstation(boolean isSubstation) {
		this.isSubstation = isSubstation;
	}

	public boolean getIsImport() {
		return isImport;
	}

	protected void setIsImport(boolean isImport) {
		this.isImport = isImport;
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

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("llf");
		Element element = (Element) super.toXml(doc);
		element.setAttribute("code", code.toString());
		element.setAttribute("description", description);
		element.setAttribute("is-substation", Boolean.toString(isSubstation));
		element.setAttribute("is-import", Boolean.toString(isImport));
		MonadDate fromDate = new MonadDate(from);
		fromDate.setLabel("from");
		MonadDate toDate = new MonadDate(to);
		toDate.setLabel("to");
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("dso").put("voltageLevel")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
	/*
	 * public void attachProfileClass(ProfileClass profileClass) throws
	 * UserException, ProgrammerException { if
	 * (profileClasses.contains(profileClass)) { throw UserException
	 * .newInvalidParameter("This profile class is already attached to this line
	 * loss factor."); } profileClasses.add(profileClass); }
	 * 
	 * public void addMeterTimeswitches(String codes) throws
	 * ProgrammerException, UserException { for (String code : codes.split(",")) {
	 * addMeterTimeswitch(code); } }
	 */
	
	public MpanTop insertMpanTop(Pc pc, Mtc mtc, Ssc ssc) throws HttpException {
		MpanTop top = new MpanTop(pc, mtc, this, ssc);
		Hiber.session().save(top);
		Hiber.flush();
		return top;
	}
}