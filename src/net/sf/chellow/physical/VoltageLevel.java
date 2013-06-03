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

import org.w3c.dom.Document;
import org.w3c.dom.Node;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

public class VoltageLevel extends PersistentEntity {
	static public final String EHV = "EHV";
	static public final String HV = "HV";
	static public final String LV = "LV";

	static public VoltageLevel getVoltageLevel(String code)
			throws HttpException {
		VoltageLevel voltageLevel = findVoltageLevel(code);
		if (voltageLevel == null) {
			throw new UserException("There is no voltage level with the code '"
					+ code + "'.");
		}
		return voltageLevel;
	}

	static public VoltageLevel findVoltageLevel(String code)
			throws HttpException {
		return (VoltageLevel) Hiber.session().createQuery(
				"from VoltageLevel level where level.code = :code")
				.setString("code", code).uniqueResult();
	}

	public static void insertVoltageLevels() throws HttpException {
		insertVoltageLevel(LV, "Low voltage");
		insertVoltageLevel(HV, "High voltage");
		insertVoltageLevel(EHV, "Extra high voltage");
	}

	private static VoltageLevel insertVoltageLevel(String code, String name)
			throws HttpException {
		VoltageLevel voltageLevel = new VoltageLevel(code, name);
		Hiber.session().save(voltageLevel);
		Hiber.flush();
		return voltageLevel;
	}
	
	private String code;

	private String name;

	public VoltageLevel() {
	}

	public VoltageLevel(String code, String name) {
		setCode(code);
		setName(name);
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
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
