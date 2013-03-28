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

public class Cop extends PersistentEntity {	
	public static final String COP_1 = "1";
	public static final String COP_2 = "2";
	public static final String COP_3 = "3";
	public static final String COP_4 = "4";
	public static final String COP_5 = "5";
	public static final String COP_6A = "6a";
	public static final String COP_6B = "6b";
	public static final String COP_6C = "6c";
	public static final String COP_6D = "6d";
	public static final String COP_7 = "7";

	static public Cop getCop(Long id) throws HttpException {
		Cop cop = (Cop) Hiber.session().get(Cop.class, id);
		if (cop == null) {
			throw new NotFoundException("The CoP with id " + id + " can't be found.");
		}
		return cop;
	}

	static public Cop getCop(String code) throws HttpException {
		code = code.trim();
		Cop type = (Cop) Hiber.session().createQuery(
				"from Cop cop where cop.code = :code").setString(
				"code", code).uniqueResult();
		if (type == null) {
			throw new NotFoundException("The CoP with code " + code + " can't be found.");
		}
		return type;
	}

	static public Cop insertCop(String code, String description)
			throws HttpException {
		Cop cop = new Cop(code, description);
		Hiber.session().save(cop);
		Hiber.flush();
		return cop;
	}

	private String code;
	private String description;

	public Cop() {
	}

	public Cop(String code, String description) {
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