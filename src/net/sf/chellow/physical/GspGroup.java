/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class GspGroup extends PersistentEntity {
	public static GspGroup getGspGroup(Long id) throws HttpException {
		GspGroup group = (GspGroup) Hiber.session().get(GspGroup.class, id);
		if (group == null) {
			throw new UserException("There isn't a GSP group with that id.");
		}
		return group;
	}

	public static GspGroup getGspGroup(String code) throws HttpException {
		GspGroup group = (GspGroup) Hiber.session().createQuery("from GspGroup group where group.code = :code").setString("code", code).uniqueResult();
		if (group == null) {
			throw new NotFoundException("There isn't a GSP group with that code.");
		}
		return group;
	}
	
	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Gsp groups.");
		Mdd mdd = new Mdd(sc, "GspGroup",
				new String[] { "GSP Group Id", "GSP Group Name" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			GspGroup group = new GspGroup(values[0], values[1]);
			Hiber.session().save(group);
			Hiber.close();
		}
		Debug.print("Finished adding GSP groups.");
	}

	private String code;
	private String description;

	public GspGroup() {
	}

	public GspGroup(String code, String description) {
		setCode(code);
		setDescription(description);
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

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "gsp-group");

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.GSP_GROUPS_INSTANCE.getUri().resolve(getUriId()).append(
				"/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}
}