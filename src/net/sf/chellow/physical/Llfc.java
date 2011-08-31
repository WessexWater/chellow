/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.physical;

import java.net.URI;
import java.text.DecimalFormat;
import java.util.Date;
import java.util.List;

import net.sf.chellow.billing.Dno;
import net.sf.chellow.billing.Provider;
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

public class Llfc extends PersistentEntity {
	static public Llfc getLlfc(Long id) throws HttpException {
		Llfc llfc = (Llfc) Hiber.session().get(Llfc.class, id);
		if (llfc == null) {
			throw new UserException("There is no LLFC with that id.");
		}
		return llfc;
	}

	@SuppressWarnings("unchecked")
	static public List<Llfc> find(Provider dno, Pc profileClass,
			boolean isSubstation, boolean isImport, VoltageLevel voltageLevel)
			throws InternalException, HttpException {
		try {
			return (List<Llfc>) Hiber
					.session()
					.createQuery(
							"from Llf llf where llf.dno = :dno and llf.profileClass = :profileClass and llf.isSubstation.boolean = :isSubstation and llf.isImport.boolean = :isImport and llf.voltageLevel = :voltageLevel")
					.setEntity("dno", dno).setEntity("profileClass",
							profileClass).setBoolean("isSubstation",
							isSubstation).setBoolean("isImport", isImport)
					.setEntity("voltageLevel", voltageLevel).list();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	@SuppressWarnings("unchecked")
	static public List<Llfc> find(Provider dno, Pc profileClass)
			throws HttpException {
		try {
			return (List<Llfc>) Hiber
					.session()
					.createQuery(
							"from Llf llf where llf.dno = :dno and llf.profileClass = :profileClass order by llf.code.string")
					.setEntity("dno", dno).setEntity("profileClass",
							profileClass).list();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	private Dno dno;

	private int code;

	private String description;

	private VoltageLevel voltageLevel;

	private boolean isSubstation;

	private boolean isImport;

	private Date validFrom;
	private Date validTo;

	Llfc() {
	}

	public Llfc(Dno dno, int code, String description,
			VoltageLevel voltageLevel, boolean isSubstation, boolean isImport,
			Date validFrom, Date validTo) throws HttpException {
		setDno(dno);
		setCode(code);
		setDescription(description);
		setVoltageLevel(voltageLevel);
		setIsSubstation(isSubstation);
		setIsImport(isImport);
		setValidFrom(validFrom);
		setValidTo(validTo);
	}

	public Dno getDno() {
		return dno;
	}

	public void setDno(Dno dno) {
		this.dno = dno;
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

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "llfc");
		element.setAttribute("code", toString());
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

	public MonadUri getEditUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("dno").put("voltageLevel")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public String toString() {
		return new DecimalFormat("000").format(code);
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
