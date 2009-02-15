/*
 
 Copyright 2005, 2009 Meniscus Systems Ltd
 
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
import org.w3c.dom.Node;

public class Source extends PersistentEntity implements Urlable {
	static public final String NETWORK_CODE = "net";
	static public final String GENERATOR_CODE = "gen";
	static public final String GENERATOR_NETWORK_CODE = "gen-net";
	static public final String SUBMETER_CODE = "sub";

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

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "source");

		element.setAttribute("code", code);
		element.setAttribute("name", name);
		return element;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.SOURCES_INSTANCE.getUri().resolve(getUriId()).append("/");
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