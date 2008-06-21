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

import java.util.List;

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

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Llf extends PersistentEntity {
	static public Llf insertLlf(Dso dso, int code,
			String description, String voltageLevel, boolean isSubstation,
			boolean isImport) throws InternalException, HttpException {
		Llf llf = new Llf(dso, code,
				description, VoltageLevel.getVoltageLevel(new VoltageLevelCode(
						voltageLevel)), isSubstation, isImport);
		Hiber.session().save(llf);
		Hiber.flush();
		return llf;
	}

	static public Llf getLlf(Long id)
			throws InternalException, HttpException {
		Llf llf = (Llf) Hiber.session().get(
				Llf.class, id);
		if (llf == null) {
			throw new UserException
					("There is no mpan generation with that id.");
		}
		return llf;
	}

	@SuppressWarnings("unchecked")
	static public List<Llf> find(Dso dso, ProfileClass profileClass,
			boolean isSubstation, boolean isImport, VoltageLevel voltageLevel)
			throws InternalException, HttpException {
		try {
			return (List<Llf>) Hiber
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
	static public List<Llf> find(Dso dso, ProfileClass profileClass)
			throws InternalException, HttpException {
		try {
			return (List<Llf>) Hiber
					.session()
					.createQuery(
							"from Llf llf where llf.dso = :dso and llf.profileClass = :profileClass order by llf.code.string")
					.setEntity("dso", dso).setEntity("profileClass",
							profileClass).list();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	private Dso dso;

	private LlfCode code;

	private String description;

	private VoltageLevel voltageLevel;

	private boolean isSubstation;

	private boolean isImport;

	Llf() {
	}

	public Llf(Dso dso, int code, String description,
			VoltageLevel voltageLevel, boolean isSubstation, boolean isImport)
			throws InternalException, HttpException {
		this();
		this.dso = dso;
		setCode(new LlfCode(code));
		if (description == null) {
			throw new InternalException("The description can't be null.");
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

	public LlfCode getCode() {
		return code;
	}

	void setCode(LlfCode code) {
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
			boolean isImport) throws InternalException, HttpException {
		setVoltageLevel(voltageLevel);
		setIsSubstation(isSubstation);
		setIsImport(isImport);
	}

	public String toString() {
		return code.toString() + " - " + description + " (DSO " + dso.getCode()
				+ ")";
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("llf");
		Element element = (Element) super.toXml(doc);
		element.setAttribute("code", code.toString());
		element.setAttribute("description", description);
		element.setAttribute("is-substation", Boolean.toString(isSubstation));
		element.setAttribute("is-import", Boolean.toString(isImport));
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
}