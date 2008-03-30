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

import java.text.NumberFormat;
import java.util.List;
import java.util.Locale;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class LineLossFactor extends PersistentEntity {
	static public LineLossFactor insertLineLossFactor(Dso dso, int code,
			String description, String voltageLevel, boolean isSubstation,
			boolean isImport) throws ProgrammerException, UserException {
		LineLossFactor lineLossFactor = new LineLossFactor(dso, code,
				description, VoltageLevel.getVoltageLevel(new VoltageLevelCode(
						voltageLevel)), isSubstation, isImport);
		Hiber.session().save(lineLossFactor);
		return lineLossFactor;
	}

	static public LineLossFactor getLineLossFactor(MonadLong id)
			throws ProgrammerException, UserException {
		try {
			LineLossFactor lineLossFactor = (LineLossFactor) Hiber.session()
					.get(LineLossFactor.class, id.getLong());
			if (lineLossFactor == null) {
				throw UserException
						.newOk("There is no mpan generation with that id.");
			}
			return lineLossFactor;
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	/*
	 * static public LineLossFactor getLineLossFactor(Dso dso, int
	 * lineLossFactorCode) throws ProgrammerException, UserException { if
	 * (lineLossFactorCode == null) { throw new
	 * ProgrammerException("lineLossFactorCode can't be null."); } try {
	 * LineLossFactor lineLossFactor = (LineLossFactor) Hiber .session()
	 * .createQuery( "from LineLossFactor llf where llf.dso = :dso and
	 * llf.code.integer = :lineLossFactorCode") .setEntity("dso",
	 * dso).setInteger("lineLossFactorCode",
	 * lineLossFactorCode.getInteger()).uniqueResult(); if (lineLossFactor ==
	 * null) { throw UserException .newInvalidParameter("There is no Line Loss
	 * Factor with DSO: " + dso + " and Line Loss Factor Code: " +
	 * lineLossFactorCode + "."); } return lineLossFactor; } catch
	 * (HibernateException e) { throw new ProgrammerException(e); } }
	 */
	public static String codeAsString(int code) {
		NumberFormat format = NumberFormat.getIntegerInstance(Locale.UK);
		format.setMinimumIntegerDigits(3);
		return format.format(code);
	}

	@SuppressWarnings("unchecked")
	static public List<LineLossFactor> find(Dso dso, ProfileClass profileClass,
			boolean isSubstation, boolean isImport, VoltageLevel voltageLevel)
			throws ProgrammerException, UserException {
		try {
			return (List<LineLossFactor>) Hiber
					.session()
					.createQuery(
							"from LineLossFactor llf where llf.dso = :dso and llf.profileClass = :profileClass and llf.isSubstation.boolean = :isSubstation and llf.isImport.boolean = :isImport and llf.voltageLevel = :voltageLevel")
					.setEntity("dso", dso).setEntity("profileClass",
							profileClass).setBoolean("isSubstation",
							isSubstation).setBoolean("isImport", isImport)
					.setEntity("voltageLevel", voltageLevel).list();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	@SuppressWarnings("unchecked")
	static public List<LineLossFactor> find(Dso dso, ProfileClass profileClass)
			throws ProgrammerException, UserException {
		try {
			return (List<LineLossFactor>) Hiber
					.session()
					.createQuery(
							"from LineLossFactor llf where llf.dso = :dso and llf.profileClass = :profileClass order by llf.code.string")
					.setEntity("dso", dso).setEntity("profileClass",
							profileClass).list();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	private Dso dso;

	private int code;

	private String description;

	private VoltageLevel voltageLevel;

	private boolean isSubstation;

	private boolean isImport;

	LineLossFactor() {
		setTypeName("line-loss-factor");
	}

	public LineLossFactor(Dso dso, int code, String description,
			VoltageLevel voltageLevel, boolean isSubstation, boolean isImport)
			throws ProgrammerException, UserException {
		this();
		this.dso = dso;
		setCode(code);
		if (description == null) {
			throw new ProgrammerException("The description can't be null.");
		}
		setDescription(description);
		update(voltageLevel, isSubstation, isImport);
		// setMeterTimeswitches(new HashSet<MeterTimeswitch>());
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

	/*
	 * public MeterTimeswitch addMeterTimeswitch(String code) throws
	 * ProgrammerException, UserException { MeterTimeswitch meterTimeswitch;
	 * meterTimeswitch = MeterTimeswitch.getMeterTimeswitch(getDso(), new
	 * MeterTimeswitchCode(code)); if
	 * (meterTimeswitches.contains(meterTimeswitch)) { throw UserException
	 * .newOk("The Line Loss Factor already has this Meter Timeswitch."); }
	 * meterTimeswitches.add(meterTimeswitch);
	 * meterTimeswitch.getLineLossFactors().add(this); return meterTimeswitch; }
	 */
	public void update(VoltageLevel voltageLevel, boolean isSubstation,
			boolean isImport) throws ProgrammerException, UserException {
		setVoltageLevel(voltageLevel);
		setIsSubstation(isSubstation);
		setIsImport(isImport);
	}

	private String codeAsString() {
		return codeAsString(code);
	}

	public String toString() {
		return codeAsString() + " - " + description + " (DSO " + dso.getCode()
				+ ")";
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);
		element.setAttribute("code", codeAsString());
		element.setAttribute("description", description);
		element.setAttribute("is-substation", Boolean.toString(isSubstation));
		element.setAttribute("is-import", Boolean.toString(isImport));
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(getXML(new XmlTree("dso").put("voltageLevel"), doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
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
}