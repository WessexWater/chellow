/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadBoolean;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class MeterTimeswitch extends PersistentEntity {
	static public MeterTimeswitch getMeterTimeswitch(Dso dso,
			MeterTimeswitchCode meterTimeswitchCode)
			throws ProgrammerException, UserException {
		return findMeterTimeswitch(dso, meterTimeswitchCode, true);
	}

	static public MeterTimeswitch findMeterTimeswitch(Dso dso,
			MeterTimeswitchCode meterTimeswitchCode, boolean throwException)
			throws ProgrammerException, UserException {
		dso = meterTimeswitchCode.hasDso() ? dso : null;
		MeterTimeswitch mtc = null;
		if (dso == null) {
			mtc = (MeterTimeswitch) Hiber
					.session()
					.createQuery(
							"from MeterTimeswitch as mt where mt.dso is null and mt.code.integer = :meterTimeswitchCode")
					.setInteger("meterTimeswitchCode",
							meterTimeswitchCode.getInteger()).uniqueResult();
		} else {
			mtc = (MeterTimeswitch) Hiber
					.session()
					.createQuery(
							"from MeterTimeswitch as mt where mt.dso = :dso and mt.code.integer = :meterTimeswitchCode")
					.setEntity("dso", dso).setInteger("meterTimeswitchCode",
							meterTimeswitchCode.getInteger()).uniqueResult();
		}
		if (throwException && mtc == null) {
			throw UserException
					.newInvalidParameter("There isn't a meter timeswitch with DSO '"
							+ (dso == null ? dso : dso.getCode())
							+ "' and Meter Timeswitch Code '"
							+ meterTimeswitchCode + "'");
		}
		return mtc;
	}

	static public MeterTimeswitch getMeterTimeswitch(Long id)
			throws ProgrammerException, UserException {
		MeterTimeswitch meterTimeswitch = (MeterTimeswitch) Hiber.session()
				.get(MeterTimeswitch.class, id);
		if (meterTimeswitch == null) {
			throw UserException
					.newOk("There is no meter timeswitch with that id.");
		}
		return meterTimeswitch;
	}

	static public MeterTimeswitch insertMeterTimeswitch(Dso dso,
			String mtcCode, String description, boolean isUnmetered)
			throws ProgrammerException, UserException {
		return insertMeterTimeswitch(dso, new MeterTimeswitchCode(mtcCode),
				description, isUnmetered);
	}

	static public MeterTimeswitch insertMeterTimeswitch(Dso dso,
			MeterTimeswitchCode meterTimeswitchCode, String description,
			boolean isUnmetered) throws ProgrammerException, UserException {

		MeterTimeswitch meterTimeswitch = null;
		try {
			meterTimeswitch = new MeterTimeswitch(dso, meterTimeswitchCode,
					description, isUnmetered);
			Hiber.session().save(meterTimeswitch);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw UserException
						.newOk("A site with this code already exists.");
			} else {
				throw new ProgrammerException(e);
			}
		}
		return meterTimeswitch;
	}

	private Dso dso;

	private MeterTimeswitchCode code;

	private String description;

	private boolean isUnmetered;

	// private Set<LineLossFactor> lineLossFactors;

	// private Set<Ssc> registers;

	public MeterTimeswitch() {
		setTypeName("meter-timeswitch");
	}

	public MeterTimeswitch(Dso dso, MeterTimeswitchCode code,
			String description, boolean isUnmetered)
			throws ProgrammerException, UserException {
		this(null, dso, code, description, isUnmetered);
	}

	public MeterTimeswitch(String label, Dso dso, MeterTimeswitchCode code,
			String description, boolean isUnmetered)
			throws ProgrammerException, UserException {
		this();
		boolean hasDso = code.hasDso();
		if (hasDso && dso == null) {
			throw UserException.newInvalidParameter("The MTC " + code
					+ " requires a DSO.");

		} else if (!hasDso && dso != null) {
			throw UserException.newInvalidParameter("The MTC " + code
					+ " does not have a DSO.");
		}
		setLabel(label);
		setDso(dso);
		setCode(code);
		setDescription(description);
		setIsUnmetered(isUnmetered);
	}

	void setDso(Dso dso) {
		this.dso = dso;
	}

	public Dso getDso() {
		return dso;
	}

	public MeterTimeswitchCode getCode() {
		return code;
	}

	void setCode(MeterTimeswitchCode code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public boolean getIsUnmetered() {
		return isUnmetered;
	}

	void setIsUnmetered(boolean isUnmetered) {
		this.isUnmetered = isUnmetered;
	}

	/*
	 * public Set<LineLossFactor> getLineLossFactors() { return
	 * lineLossFactors; }
	 * 
	 * protected void setLineLossFactors(Set<LineLossFactor> lineLossFactors) {
	 * this.lineLossFactors = lineLossFactors; }
	 * 
	 * public Set<Ssc> getRegisters() { return registers; }
	 * 
	 * protected void setRegisters(Set<Ssc> registers) { this.registers =
	 * registers; }
	 */
	public String toString() {
		return code + " - " + description + " (DSO "
				+ (dso == null ? null : dso.getCode()) + ")";
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttributeNode(code.toXML(doc));
		element.setAttribute("description", description);
		element.setAttributeNode(MonadBoolean.toXml(doc, "is-unmetered",
				isUnmetered));
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

		source.appendChild(getXML(new XmlTree("dso"), doc));
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
	 * public void insertRegister(Ssc.Units units, String tprString) throws
	 * ProgrammerException, UserException { Set<Tpr> tprs = new HashSet<Tpr>();
	 * for (String tprCode : tprString.split(",")) { Tpr tpr =
	 * Tpr.getTpr(tprCode); tprs.add(tpr); } registers.add(new Ssc(this, units,
	 * tprs)); }
	 */
}