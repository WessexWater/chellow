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

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

@SuppressWarnings("serial")
public class Permissions implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("permissions");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Role role;

	public Permissions(Role role) {
		setRole(role);
	}

	public Role getRole() {
		return role;
	}

	void setRole(Role role) {
		this.role = role;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return role.getUri().resolve(getUrlId()).append("/");
	}
	
	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		MonadUri uriPattern = inv.getMonadUri("uri-pattern");
		Boolean isOptionsAllowed = inv.getBoolean("is-options-allowed");
		Boolean isGetAllowed = inv.getBoolean("is-get-allowed");
		Boolean isHeadAllowed = inv.getBoolean("is-head-allowed");
		Boolean isPostAllowed = inv.getBoolean("is-post-allowed");
		Boolean isPutAllowed = inv.getBoolean("is-put-allowed");
		Boolean isDeleteAllowed = inv.getBoolean("is-delete-allowed");
		Boolean isTraceAllowed = inv.getBoolean("is-trace-allowed");
		if (!inv.isValid()) {
			throw new UserException(getDocument());
		}
		List<Invocation.HttpMethod> methods = new ArrayList<Invocation.HttpMethod>();
		if (isOptionsAllowed) {
			methods.add(Invocation.HttpMethod.OPTIONS);
		}
		if (isHeadAllowed) {
			methods.add(Invocation.HttpMethod.HEAD);
		}
		if (isPutAllowed) {
			methods.add(Invocation.HttpMethod.PUT);
		}
		if (isDeleteAllowed) {
			methods.add(Invocation.HttpMethod.DELETE);
		}
		if (isGetAllowed) {
			methods.add(Invocation.HttpMethod.GET);
		}
		if (isPostAllowed) {
			methods.add(Invocation.HttpMethod.POST);
		}
		if (isTraceAllowed) {
			methods.add(Invocation.HttpMethod.TRACE);
		}
		Permission.methodsAllowed(inv.getUser(), uriPattern, methods);
		Permission permission = role.insertPermission(uriPattern, methods);
		Hiber.commit();
		inv.sendCreated(getDocument(), permission.getUri());
	}
	
	private Document getDocument() throws InternalException, HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element permissionsElement = (Element) toXml(doc);
		
		source.appendChild(permissionsElement);
		permissionsElement.appendChild(role.toXml(doc));
		for (Permission permission : role.getPermissions()) {
			permissionsElement.appendChild(permission.toXml(doc));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(getDocument());
	}

	public Permission getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		Permission permission = (Permission) Hiber
				.session()
				.createQuery(
						"from Permission permission where permission.role = :role and permission.id = :permissionId")
				.setEntity("role", role).setLong("permissionId",
						Long.parseLong(uriId.getString())).uniqueResult();
		return permission;
	}

	public void httpDelete(Invocation inv) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		return doc.createElement("permissions");
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}