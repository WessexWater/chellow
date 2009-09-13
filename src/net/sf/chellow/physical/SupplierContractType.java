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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplierContractType extends PersistentEntity {
	static public SupplierContractType getSupplierContractType(Long id) throws HttpException {
		SupplierContractType type = (SupplierContractType) Hiber.session().get(SupplierContractType.class, id);
		if (type == null) {
			throw new UserException("There is no supplier contract type with that id.");
		}
		return type;
	}

	static public SupplierContractType getSupplierContractType(String code) throws HttpException {
		SupplierContractType type = findSupplierContractType(code);
		if (type == null) {
			throw new NotFoundException("There's no supplier contract type with the code '"
					+ code + "'");
		}
		return type;
	}

	static public SupplierContractType findSupplierContractType(String code) throws HttpException {
		return (SupplierContractType) Hiber.session().createQuery(
				"from SupplierContractType type where " + "type.code = :code")
				.setString("code", code).uniqueResult();
	}

	static public SupplierContractType insertSupplierContractType(String code, String name)
			throws HttpException {
		SupplierContractType type = new SupplierContractType(code, name);
		Hiber.session().save(type);
		Hiber.flush();
		return type;
	}

	private String code;

	private String description;

	public SupplierContractType() {
	}

	public SupplierContractType(String code, String description) throws HttpException {
		update(code, description);
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

	public void update(String code, String description) throws HttpException {
		setCode(code);
		setDescription(description);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supplier-contract-type");

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		return element;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.GENERATOR_TYPES_INSTANCE.getUri().resolve(getUriId()).append("/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}
}