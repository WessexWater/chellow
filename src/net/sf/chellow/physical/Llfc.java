/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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
import java.util.Date;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.billing.Party;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class Llfc extends PersistentEntity {
	public Llfc getLlfc(String code, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dno = :dno and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dno", this)
				.setInteger("code", Integer.parseInt(code))
				.setTimestamp("date", date).uniqueResult();
		if (llfc == null) {
			throw new UserException(
					"There is no line loss factor with the code " + code
							+ " associated with the DNO '"
							+ getCode().toString() + "' for the date "
							+ date.toString() + ".");
		}
		return llfc;
	}

	public static Llfc getLlfc(Contract dnoContract, String code)
			throws HttpException {
		Party dno = dnoContract.getParty();
		code = code.trim();

		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dno = :dno and llfc.code = :code")
				.setEntity("dno", dno).setString("code", code).uniqueResult();
		if (llfc == null) {
			throw new UserException("There is no LLFC with the code " + code
					+ " associated with the DNO " + dno.getDnoCode() + ".");
		}
		return llfc;
	}

	private Party dno;

	private String code;

	private String description;

	private VoltageLevel voltageLevel;

	private boolean isSubstation;

	private boolean isImport;

	private Date validFrom;

	private Date validTo;

	Llfc() {
	}

	public Llfc(Party dno, String code, String description,
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

	public Party getDno() {
		return dno;
	}

	public void setDno(Party dno) {
		this.dno = dno;
	}

	public String getCode() {
		return code;
	}

	void setCode(String code) {
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

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getEditUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, isImport ? "imp-llfc" : "exp-llfc");
		element.setAttribute("code", code);
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
}
