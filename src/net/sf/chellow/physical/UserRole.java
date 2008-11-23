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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class UserRole extends PersistentEntity {
	public static final String EDITOR = "editor";
	public static final String VIEWER = "viewer";
	public static final String PARTY_VIEWER = "party-viewer";

	static public UserRole getUserRole(Long id) {
		return (UserRole) Hiber.session().get(UserRole.class, id);
	}

	static public UserRole getUserRole(String code)
			throws HttpException {
		UserRole role =  (UserRole) Hiber
				.session()
				.createQuery(
						"from UserRole role where role.code = :code")
				.setString("code", code.trim())
				.uniqueResult();
		if (role == null) {
			throw new UserException("There isn't a user role with code " + code + ".");
		}
		return role;
	}

	static public UserRole insertUserRole(String roleCode) throws HttpException {
		UserRole role = new UserRole(roleCode);
			Hiber.session().save(role);
			Hiber.flush();
		return role;
	}

	private String code;

	public UserRole() {
	}

	public UserRole(String code) throws HttpException {
		update(code);
	}

	public void update(String code) throws HttpException {
		setCode(code);
	}

	public String getCode() {
		return code;
	}

	protected void setCode(String code) {
		this.code = code;
	}

	public boolean equals(Object object) {
		boolean isEqual = false;
		if (object instanceof UserRole) {
			UserRole user = (UserRole) object;
			isEqual = user.getId().equals(getId());
		}
		return isEqual;
	}

	public String toString() {
		try {
			return getUriId().toString();
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "user-role");
		element.setAttribute("code", code);
		return element;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.USER_ROLES_INSTANCE.getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		return document(null);
	}

	@SuppressWarnings("unchecked")
	private Document document(String message) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		if (message != null) {
			source.appendChild(new MonadMessage(message).toXml(doc));
		}
		return doc;
	}
}