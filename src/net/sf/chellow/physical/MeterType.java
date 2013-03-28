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

import java.util.Date;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;

public class MeterType extends PersistentEntity {
	static public MeterType getMtcMeterType(String code) throws HttpException {
		MeterType type = findMeterType(code);
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public MeterType findMeterType(String code) throws HttpException {
		return (MeterType) Hiber
				.session()
				.createQuery(
						"from MeterType meterType where meterType.code = :meterTypeCode")
				.setString("meterTypeCode", code).uniqueResult();
	}

	static public MeterType getMeterType(Long id) throws HttpException {
		MeterType type = (MeterType) Hiber.session().get(MeterType.class, id);
		if (type == null) {
			throw new UserException(
					"There is no meter timeswitch class meter type with that id.");
		}
		return type;
	}

	private String code;

	private String description;

	private Date validFrom;
	private Date validTo;

	public MeterType() {
	}

	public MeterType(String code, String description, Date validFrom,
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

	void setValidFrom(Date from) {
		this.validFrom = from;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date to) {
		this.validTo = to;
	}
}
