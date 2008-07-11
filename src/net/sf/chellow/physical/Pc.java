/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Pc extends PersistentEntity {
	static public Pc getPc(Long id) throws HttpException {
		Pc pc = (Pc) Hiber.session().get(Pc.class, id);
		if (pc == null) {
			throw new UserException("There is no profile class with that id.");
		}
		return pc;
	}

	static public Pc getPc(int code) throws HttpException {
		return getPc(new PcCode(code));
	}

	static public Pc getPc(PcCode code) throws HttpException {
		Pc profileClass = findPc(code);
		if (profileClass == null) {
			throw new UserException("There is no profile class with that code.");
		}
		return profileClass;
	}

	static public Pc findPc(PcCode code) {
		return findPc(code.getInteger());
	}

	static public Pc findPc(int code) {
		return (Pc) Hiber.session().createQuery(
				"from Pc pc where pc.code.integer = :code").setInteger("code",
				code).uniqueResult();
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add PCs");
		Mdd mdd = new Mdd(sc, "ProfileClass", new String[] {
				"Profile Class Id", "Effective From Settlement Date {PCLA}",
				"Profile Class Description", "Switched Load Profile Class Ind",
				"Effective To Settlement Date {PCLA}" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Hiber.session().save(
					new Pc(new PcCode(Integer.parseInt(values[0])), values[2]));
			Hiber.close();
		}
		Debug.print("Added PCs.");
	}

	private PcCode code;

	private String description;

	public Pc() {
	}

	public Pc(PcCode code, String description) {
		this(null, code, description);
	}

	public Pc(String label, PcCode code, String description) {
		this();
		setLabel(label);
		this.code = code;
		this.description = description;
	}

	void setCode(PcCode code) {
		code.setLabel("code");
		this.code = code;
	}

	public PcCode getCode() {
		return code;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public String getDescription() {
		return description;
	}

	public void update(String description) {
		setDescription(description);
		Hiber.flush();
	}

	public String toString() {
		return getCode() + " - " + getDescription();
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("pc");
		Element element = (Element) super.toXml(doc);

		element.setAttributeNode(code.toXml(doc));
		element.setAttribute("description", description);
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
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc));
		inv.sendOk(doc);
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