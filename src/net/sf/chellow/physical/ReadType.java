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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;

public class ReadType extends PersistentEntity {	
	public static final String TYPE_NORMAL = "N";
	public static final String TYPE_NORMAL_3RD_PARTY = "N3";
	public static final String TYPE_CUSTOMER = "C";
	public static final String TYPE_ESTIMATED = "E";
	public static final String TYPE_ESTIMATED_3RD_PARTY = "E3";
	public static final String TYPE_ESTIMATED_MANUAL = "EM";
	public static final String TYPE_WITHDRAWN = "W";
	public static final String TYPE_EXCHANGE = "X";
	public static final String TYPE_COMPUTER = "CP";
	public static final String TYPE_INFORMATION = "IF";

	static public ReadType getReadType(Long id) throws HttpException {
		ReadType readType = (ReadType) Hiber.session().get(ReadType.class, id);
		if (readType == null) {
			throw new NotFoundException("The Read Type with id " + id + " can't be found.");
		}
		return readType;
	}

	static public ReadType getReadType(String code) throws HttpException {
		code = code.trim();
		ReadType type = (ReadType) Hiber.session().createQuery(
				"from ReadType type where type.code = :code").setString(
				"code", code).uniqueResult();
		if (type == null) {
			throw new NotFoundException("The Read Type with code " + code + " can't be found.");
		}
		return type;
	}

	static public ReadType insertReadType(String code, String description)
			throws HttpException {
		ReadType readType = new ReadType(code, description);
		Hiber.session().save(readType);
		Hiber.flush();
		return readType;
	}

	private String code;
	private String description;

	public ReadType() {
	}

	public ReadType(String code, String description) {
		this.code = code;
		this.description = description;
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
	}
}
