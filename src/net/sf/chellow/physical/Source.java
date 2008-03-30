/*
 
 Copyright 2005 Meniscus Systems Ltd
 
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
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Source extends PersistentEntity implements Urlable {
	static private HttpMethod[] ALLOWED_METHODS = { HttpMethod.GET };

	static public Source getSource(Long id) throws ProgrammerException,
			UserException {
		try {
			Source source = (Source) Hiber.session().get(Source.class, id);
			if (source == null) {
				throw UserException.newOk("There is no source with that id.");
			}
			return source;
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}

	static public Source getSource(SourceCode sourceCode)
			throws ProgrammerException, UserException {
		Source source = findSource(sourceCode.getString());
		if (source == null) {
			throw UserException.newNotFound();
		}
		return source;
	}

	static public Source findSource(String code) throws ProgrammerException,
			UserException {
		return (Source) Hiber.session().createQuery(
				"from Source as source where " + "source.code.string = :code")
				.setString("code", code).uniqueResult();
	}

	@SuppressWarnings("unchecked")
	static public List<Source> getSources() throws ProgrammerException,
			UserException {
		return (List<Source>) Hiber.session().createQuery(
				"from Source as source").list();
	}

	static public Source insertSource(String code, String name)
			throws ProgrammerException, UserException {
		return insertSource(new SourceCode(code), new SourceName(name));
	}

	static public Source insertSource(SourceCode code, SourceName name)
			throws ProgrammerException, UserException {

		Source source = null;
		try {
			source = new Source(code, name);
			Hiber.session().save(source);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw UserException
						.newOk("A site with this code already exists.");
			} else {
				throw new ProgrammerException(e);
			}
		}
		return source;
	}

	private SourceCode code;

	private SourceName name;

	//private Set<Supply> supplies;

	public Source() {
		setTypeName("source");
	}

	public Source(SourceCode code, SourceName name) {
		this();
		update(code, name);
	}

	public SourceCode getCode() {
		return code;
	}

	public void setCode(SourceCode code) {
		checkNull(this.code = code, "code");
		code.setLabel("code");
	}

	public SourceName getName() {
		return name;
	}

	public void setName(SourceName name) {
		this.name = name;
		name.setLabel("name");
	}

	/*
	public Set getSupplies() {
		return supplies;
	}

	protected void setSupplies(Set<Supply> supplies) {
		this.supplies = supplies;
	}
	*/

	public void update(SourceCode code, SourceName name) {
		setCode(code);
		setName(name);
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttributeNode((Attr) code.toXML(doc));
		element.setAttributeNode((Attr) getName().toXML(doc));
		return element;
	}

	/*
	public void addSupply(Supply supply) {
		supplies.add(supply);
		// supply.getSites().add(this);
	}
	*/

	public MonadUri getUri() throws ProgrammerException, UserException {
		return Chellow.SOURCES_INSTANCE.getUri().resolve(getUriId());
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXML(doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		inv.sendMethodNotAllowed(ALLOWED_METHODS);
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		throw UserException.newNotFound();
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		inv.sendMethodNotAllowed(ALLOWED_METHODS);
	}
}