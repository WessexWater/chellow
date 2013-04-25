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

import java.net.URI;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Source extends PersistentEntity {
	static public final String NETWORK_CODE = "net";
	static public final String GENERATOR_CODE = "gen";
	static public final String GENERATOR_NETWORK_CODE = "gen-net";
	static public final String SUBMETER_CODE = "sub";
	static public final String THIRD_PARTY_CODE = "3rd-party";
	static public final String THIRD_PARTY_REVERSE_CODE = "3rd-party-reverse";
	
	static public Source getSource(Long id) throws HttpException {
		Source source = (Source) Hiber.session().get(Source.class, id);
		if (source == null) {
			throw new UserException("There is no source with that id.");
		}
		return source;
	}

	static public Source getSource(String sourceCode) throws HttpException {
		Source source = findSource(sourceCode);
		if (source == null) {
			throw new NotFoundException("There's no source with the code '"
					+ sourceCode + "'");
		}
		return source;
	}

	static public Source findSource(String code) throws HttpException {
		return (Source) Hiber.session().createQuery(
				"from Source as source where " + "source.code = :code")
				.setString("code", code).uniqueResult();
	}

	static public Source insertSource(String code, String name)
			throws HttpException {
		Source source = new Source(code, name);
		Hiber.session().save(source);
		Hiber.flush();
		return source;
	}

	private String code;

	private String name;

	public Source() {
	}

	public Source(String code, String name) throws HttpException {
		update(code, name);
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

	public void update(String code, String name) throws HttpException {
		/*
		if (code.length() > 6) {
			throw new UserException(
					"The source code is too long. It shouldn't be more than 5 characters long.");
		}
		*/
		setCode(code);
		setName(name);
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

	public Element toXml(Document doc) throws HttpException {
        Element element = super.toXml(doc, "site");

        element.setAttribute("name", name);
        element.setAttribute("code", code);
        return element;
}
}
