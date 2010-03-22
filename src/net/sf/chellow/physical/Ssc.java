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

import java.text.DecimalFormat;
import java.util.Date;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Ssc extends PersistentEntity {
	public static Ssc getSsc(String code) throws HttpException {
		try {
			Ssc ssc = (Ssc) Hiber.session().createQuery(
					"from Ssc ssc where ssc.code = :code").setInteger("code",
					Integer.parseInt(code)).uniqueResult();
			if (ssc == null) {
				throw new UserException("There isn't an SSC with code: " + code
						+ ".");
			}
			return ssc;
		} catch (NumberFormatException e) {
			throw new UserException("An SCC code must be an integer. "
					+ e.getMessage());
		}
	}

	public static Ssc getSsc(long id) throws HttpException {
		Ssc ssc = (Ssc) Hiber.session().get(Ssc.class, id);
		if (ssc == null) {
			throw new UserException("There isn't an SSC with id: " + id + ".");
		}
		return ssc;
	}

	private int code;
	private Date validFrom;
	private Date validTo;
	private String description;
	private boolean isImport;
	private Set<MeasurementRequirement> mrs;

	public Ssc() {
	}

	public Ssc(String code, Date validFrom, Date validTo, String description,
			boolean isImport) throws HttpException {
		setCode(Integer.parseInt(code));
		setValidFrom(validFrom);
		setValidTo(validTo);
		setDescription(description);
		setIsImport(isImport);
	}

	public int getCode() {
		return code;
	}

	void setCode(int code) {
		this.code = code;
	}

	public Date getValidFrom() {
		return validFrom;
	}

	void setValidFrom(Date validFrom) {
		this.validFrom = validFrom;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date validTo) {
		this.validTo = validTo;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public boolean getIsImport() {
		return isImport;
	}

	void setIsImport(boolean isImport) {
		this.isImport = isImport;
	}

	public Set<MeasurementRequirement> getMeasurementRequirements() {
		return mrs;
	}

	void setMeasurementRequirements(Set<MeasurementRequirement> mrs) {
		this.mrs = mrs;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		return null;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("measurementRequirements",
				new XmlTree("tpr"))));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
	
	public String codeAsString() {
		return new DecimalFormat("0000").format(code);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "ssc");

		element.setAttribute("code", codeAsString());
		element.setAttribute("is-import", Boolean.toString(isImport));
		element.setAttribute("description", description);
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

	public MeasurementRequirement insertMeasurementRequirement(Tpr tpr)
			throws HttpException {
		MeasurementRequirement mr = new MeasurementRequirement(this, tpr);
		Hiber.session().save(mr);
		Hiber.session().flush();
		return mr;
	}
}
