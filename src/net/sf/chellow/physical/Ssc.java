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
import java.util.Set;

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

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
			throw new UserException("An SSC code must be an integer. "
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

	public MeasurementRequirement insertMeasurementRequirement(Tpr tpr)
			throws HttpException {
		MeasurementRequirement mr = new MeasurementRequirement(this, tpr);
		Hiber.session().save(mr);
		Hiber.session().flush();
		return mr;
	}

	@Override
	public MonadUri getEditUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
