/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import java.util.List;

import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class VoltageLevel extends PersistentEntity {
	static public VoltageLevel getVoltageLevel(VoltageLevelCode code)
			throws InternalException, HttpException {
		VoltageLevel voltageLevel = findVoltageLevel(code);
		if (voltageLevel == null) {
			throw new UserException
					("There is no voltage level with that code.");
		}
		return voltageLevel;
	}

	static public VoltageLevel findVoltageLevel(VoltageLevelCode code)
			throws InternalException, HttpException {
		return (VoltageLevel) Hiber.session().createQuery(
				"from VoltageLevel as voltageLevel where "
						+ "voltageLevel.code.string = :code").setString("code",
				code.toString()).uniqueResult();
	}

	public static VoltageLevel insertVoltageLevel(String code, String name)
			throws InternalException, HttpException {
		VoltageLevelCode voltageLevelCode = new VoltageLevelCode(code);
		VoltageLevel voltageLevel = VoltageLevel
				.findVoltageLevel(voltageLevelCode);
		if (voltageLevel == null) {
			voltageLevel = VoltageLevel.insertVoltageLevel(voltageLevelCode,
					name);
		}
		return voltageLevel;
	}

	public static VoltageLevel insertVoltageLevel(VoltageLevelCode code,
			String name) throws InternalException, HttpException {

		VoltageLevel voltageLevel = null;
		try {
			voltageLevel = new VoltageLevel(code, name);
			Hiber.session().save(voltageLevel);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw new UserException
						("A site with this code already exists.");
			} else {
				throw new InternalException(e);
			}
		}
		return voltageLevel;
	}

	@SuppressWarnings("unchecked")
	public static List<VoltageLevel> getVoltageLevels()
			throws InternalException {
		try {
			return Hiber.session()
					.createQuery("from VoltageLevel voltageLevel").list();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	private VoltageLevelCode code;

	private String name;

	public VoltageLevel() {
	}

	public VoltageLevel(VoltageLevelCode code, String name) {
		this();
		setCode(code);
		setName(name);
	}

	public VoltageLevelCode getCode() {
		return code;
	}

	public void setCode(VoltageLevelCode code) {
		this.code = code;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = doc.createElement("voltage-level");
		code.setLabel("code");
		element.setAttributeNode((Attr) code.toXml(doc));
		element.setAttribute("name", name);
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
}