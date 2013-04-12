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
import org.w3c.dom.Node;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

public class MeterPaymentType extends PersistentEntity {
	static public MeterPaymentType getMtcPaymentType(String code)
			throws HttpException {
		MeterPaymentType type = findMtcPaymentType(code);
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public MeterPaymentType findMtcPaymentType(String code)
			throws HttpException {
		return (MeterPaymentType) Hiber
				.session()
				.createQuery(
						"from MeterPaymentType type where type.code = :paymentCode")
				.setString("paymentCode", code).uniqueResult();
	}

	static public MeterPaymentType getMeterPaymentType(Long id)
			throws HttpException {
		MeterPaymentType type = (MeterPaymentType) Hiber.session().get(
				MeterPaymentType.class, id);
		if (type == null) {
			throw new UserException(
					"There is no meter timeswitch class payment type with that id.");
		}
		return type;
	}

	private String code;

	private String description;

	private Date validFrom;
	private Date validTo;

	public MeterPaymentType() {
	}

	public MeterPaymentType(String code, String description, Date validFrom,
			Date validTo) throws HttpException {
		setCode(code);
		setDescription(description);
		setValidFrom(validFrom);
		setValidTo(validTo);
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
