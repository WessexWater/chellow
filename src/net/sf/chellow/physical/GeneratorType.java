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

public class GeneratorType extends PersistentEntity {
	static public GeneratorType getGeneratorType(Long id) throws HttpException {
		GeneratorType type = (GeneratorType) Hiber.session().get(GeneratorType.class, id);
		if (type == null) {
			throw new UserException("There is no generator type with that id.");
		}
		return type;
	}

	static public GeneratorType getGeneratorType(String code) throws HttpException {
		GeneratorType type = findGeneratorType(code);
		if (type == null) {
			throw new NotFoundException("There's no generator type with the code '"
					+ code + "'");
		}
		return type;
	}

	static public GeneratorType findGeneratorType(String code) throws HttpException {
		return (GeneratorType) Hiber.session().createQuery(
				"from GeneratorType type where " + "type.code = :code")
				.setString("code", code).uniqueResult();
	}

	static public GeneratorType insertGeneratorType(String code, String name)
			throws HttpException {
		GeneratorType type = new GeneratorType(code, name);
		Hiber.session().save(type);
		Hiber.flush();
		return type;
	}

	private String code;

	private String description;

	public GeneratorType() {
	}

	public GeneratorType(String code, String description) throws HttpException {
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
		Element element = super.toXml(doc, "generator-type");

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
