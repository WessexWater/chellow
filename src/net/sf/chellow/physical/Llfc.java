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

import java.text.DecimalFormat;
import java.util.Date;
import java.util.List;

import javax.servlet.ServletContext;

import net.sf.chellow.billing.Dso;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Llfc extends PersistentEntity {
	static public Llfc getLlfc(Long id) throws HttpException {
		Llfc llfc = (Llfc) Hiber.session().get(Llfc.class, id);
		if (llfc == null) {
			throw new UserException("There is no LLFC with that id.");
		}
		return llfc;
	}

	@SuppressWarnings("unchecked")
	static public List<Llfc> find(Provider dso, Pc profileClass,
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
	static public List<Llfc> find(Provider dso, Pc profileClass)
			throws HttpException {
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

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add LLFCs.");
		try {
			Mdd mdd = new Mdd(sc, "LineLossFactorClass", new String[] {
					"Market Participant Id", "Market Participant Role Code",
					"Effective From Date {MPR}", "Line Loss Factor Class Id",
					"Effective From Settlement Date {LLFC}",
					"Line Loss Factor Class Description",
					"MS Specific LLF Class Indicator",
					"Effective To Settlement Date {LLFC}" });
			for (String[] values = mdd.getLine(); values != null; values = mdd
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
				boolean isSubstation = description.contains("S/S")
						|| description.contains("sub")
						|| description.contains("Substation");
				String indicator = values[6];
				boolean isImport = indicator.equals("A")
						|| indicator.equals("B");
				Date validFrom = mdd.toDate(values[4]);
				Date validTo = mdd.toDate(values[7]);
				Hiber.session().save(
						new Llfc(Dso.getDso(Participant
								.getParticipant(participantCode)), Integer
								.parseInt(values[3]), description, vLevel,
								isSubstation, isImport, validFrom, validTo));
				Hiber.close();
			}
		} catch (NumberFormatException e) {
			throw new InternalException(e);
		}
		Debug.print("Finished adding LLFCs.");
	}

	private Dso dso;

	private int code;

	private String description;

	private VoltageLevel voltageLevel;

	private boolean isSubstation;

	private boolean isImport;

	private Date validFrom;
	private Date validTo;

	Llfc() {
	}

	public Llfc(Dso dso, int code, String description,
			VoltageLevel voltageLevel, boolean isSubstation, boolean isImport,
			Date validFrom, Date validTo) throws HttpException {
		setDso(dso);
		setCode(code);
		setDescription(description);
		setVoltageLevel(voltageLevel);
		setIsSubstation(isSubstation);
		setIsImport(isImport);
		setValidFrom(validFrom);
		setValidTo(validTo);
	}

	public Dso getDso() {
		return dso;
	}

	public void setDso(Dso dso) {
		this.dso = dso;
	}

	public int getCode() {
		return code;
	}

	void setCode(int code) {
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

	public Date getValidFrom() {
		return validFrom;
	}

	void setValidFrom(Date from) {
		this.validFrom = from;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date to) {
		this.validTo = to;
	}
	
	public String codeAsString() {
		DecimalFormat llfcFormat = new DecimalFormat("000");
		return llfcFormat.format(code);
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "llfc");
		element.setAttribute("code", codeAsString());
		element.setAttribute("description", description);
		element.setAttribute("is-substation", Boolean.toString(isSubstation));
		element.setAttribute("is-import", Boolean.toString(isImport));
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

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("dso").put("voltageLevel")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws HttpException {
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

	public MpanTop insertMpanTop(Pc pc, Mtc mtc, Ssc ssc, Date from, Date to)
			throws HttpException {
		MpanTop top = new MpanTop(pc, mtc, this, ssc, from, to);
		Hiber.session().save(top);
		Hiber.flush();
		return top;
	}
	
	public String toString() {
		return code + " - " + description + " (DSO "
		+ (dso.getCode()) + ")";
	}
}