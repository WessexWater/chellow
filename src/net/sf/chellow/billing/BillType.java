/*******************************************************************************
 * 
 *  Copyright (c) 2010 Wessex Water Services Limited
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
package net.sf.chellow.billing;

import java.net.URI;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class BillType extends PersistentEntity {	
	public static final String TYPE_FINAL = "F";
	public static final String TYPE_NORMAL = "N";
	public static final String TYPE_WITHDRAWN = "W";

	static public BillType getBillType(Long id) throws HttpException {
		BillType type = (BillType) Hiber.session().get(BillType.class, id);
		if (type == null) {
			throw new NotFoundException("The bill type with id " + id + " can't be found.");
		}
		return type;
	}

	static public BillType getBillType(String code) throws HttpException {
		code = code.trim();
		BillType type = (BillType) Hiber.session().createQuery(
				"from BillType type where type.code = :code").setString(
				"code", code).uniqueResult();
		if (type == null) {
			throw new NotFoundException("The bill type with code " + code + " can't be found.");
		}
		return type;
	}

	static public BillType insertBillType(String code, String description)
			throws HttpException {
		BillType type = new BillType(code, description);
		Hiber.session().save(type);
		Hiber.flush();
		return type;
	}

	private String code;
	private String description;

	public BillType() {
	}

	public BillType(String code, String description) {
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

	@Override
	public MonadUri getEditUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "bill-type");

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		return element;
	}

	public String toString() {
		return code;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}