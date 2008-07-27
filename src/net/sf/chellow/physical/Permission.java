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

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Permission extends PersistentEntity {
	static public Permission getPermission(Long id) throws InternalException {
		try {
			return (Permission) Hiber.session().get(Permission.class, id);
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}
/*
	static void methodsAllowed(User user, MonadUri uriPattern,
			List<Invocation.HttpMethod> methods) throws HttpException {
		for (Invocation.HttpMethod method : methods) {
			if (!user.methodAllowed(uriPattern.toUri(), method)) {
				throw new UserException(
						"You can't assign greater permissions that you have.");
			}
		}
	}
*/
	private Role role;

	private MonadUri uriPattern;

	private Boolean isOptionsAllowed;

	private Boolean isGetAllowed;

	private Boolean isHeadAllowed;

	private Boolean isPostAllowed;

	private Boolean isPutAllowed;

	private Boolean isDeleteAllowed;

	private Boolean isTraceAllowed;

	public Permission() {
	}

	public Permission(Role role, MonadUri uriPattern, List<Invocation.HttpMethod> methods) throws HttpException {
		setRole(role);
		update(uriPattern, methods);
	}

	public void update(MonadUri uriPattern, List<Invocation.HttpMethod> methods) throws InternalException {
		if (uriPattern == null) {
			throw new InternalException("uri parameter can't be null.");
		}
		setUriPattern(uriPattern);
		setIsOptionsAllowed(methods.contains(Invocation.HttpMethod.OPTIONS));
		setIsGetAllowed(methods.contains(Invocation.HttpMethod.GET));
		setIsHeadAllowed(methods.contains(Invocation.HttpMethod.HEAD));
		setIsPostAllowed(methods.contains(Invocation.HttpMethod.POST));
		setIsPutAllowed(methods.contains(Invocation.HttpMethod.PUT));
		setIsDeleteAllowed(methods.contains(Invocation.HttpMethod.DELETE));
		setIsTraceAllowed(methods.contains(Invocation.HttpMethod.TRACE));
	}

	public Role getRole() {
		return role;
	}

	protected void setRole(Role role) {
		this.role = role;
	}

	public MonadUri getUriPattern() {
		return uriPattern;
	}

	protected void setUriPattern(MonadUri uriPattern) {
		this.uriPattern = uriPattern;
		if (uriPattern != null) {
			uriPattern.setLabel("uri-pattern");
		}
	}

	public Boolean getIsOptionsAllowed() {
		return isOptionsAllowed;
	}

	protected void setIsOptionsAllowed(Boolean isOptionsAllowed) {
		this.isOptionsAllowed = isOptionsAllowed;
	}

	public Boolean getIsGetAllowed() {
		return isGetAllowed;
	}

	protected void setIsGetAllowed(Boolean isGetAllowed) {
		this.isGetAllowed = isGetAllowed;
	}

	public Boolean getIsHeadAllowed() {
		return isHeadAllowed;
	}

	protected void setIsHeadAllowed(Boolean isHeadAllowed) {
		this.isHeadAllowed = isHeadAllowed;
	}

	public Boolean getIsPostAllowed() {
		return isPostAllowed;
	}

	protected void setIsPostAllowed(Boolean isPostAllowed) {
		this.isPostAllowed = isPostAllowed;
	}

	public Boolean getIsPutAllowed() {
		return isPutAllowed;
	}

	protected void setIsPutAllowed(Boolean isPutAllowed) {
		this.isPutAllowed = isPutAllowed;
	}

	public Boolean getIsDeleteAllowed() {
		return isDeleteAllowed;
	}

	protected void setIsDeleteAllowed(Boolean isDeleteAllowed) {
		this.isDeleteAllowed = isDeleteAllowed;
	}

	public Boolean getIsTraceAllowed() {
		return isTraceAllowed;
	}

	protected void setIsTraceAllowed(Boolean isTraceAllowed) {
		this.isTraceAllowed = isTraceAllowed;
	}

	public boolean equals(Object object) {
		boolean isEqual = false;
		if (object instanceof Permission) {
			Permission user = (Permission) object;
			isEqual = user.getId().equals(getId());
		}
		return isEqual;
	}

	public String toString() {
		try {
			return getUriId().toString();
		} catch (InternalException e) {
			throw new RuntimeException(e);
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "permission");
		element.setAttributeNode(uriPattern.toXml(doc));
		element.setAttribute("is-post-allowed", Boolean.toString(isPostAllowed));
		element.setAttribute("is-get-allowed", Boolean.toString(isGetAllowed));
		return element;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return role.permissionsInstance().getUri().resolve(getUriId()).append(
				"/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		throw new NotFoundException();
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("role")));
		return doc;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException {
		if (inv.hasParameter("delete")) {
			Hiber.session().delete(this);
			Hiber.close();
			inv.sendSeeOther(role.permissionsInstance().getUri());
		} else {
			MonadUri uriPattern = inv.getMonadUri("uri-pattern");
			Boolean isOptionsAllowed = inv.getBoolean("is-options-allowed");
			Boolean isGetAllowed = inv.getBoolean("is-get-allowed");
			Boolean isHeadAllowed = inv.getBoolean("is-head-allowed");
			Boolean isPostAllowed = inv.getBoolean("is-post-allowed");
			Boolean isPutAllowed = inv.getBoolean("is-put-allowed");
			Boolean isDeleteAllowed = inv.getBoolean("is-delete-allowed");
			Boolean isTraceAllowed = inv.getBoolean("is-trace-allowed");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			List<Invocation.HttpMethod> methods = new ArrayList<Invocation.HttpMethod>();
			if (isOptionsAllowed) {
				methods.add(Invocation.HttpMethod.OPTIONS);
			}
			if (isGetAllowed) {
				methods.add(Invocation.HttpMethod.GET);
			}
			if (isHeadAllowed) {
				methods.add(Invocation.HttpMethod.HEAD);
			}
			if (isPostAllowed) {
				methods.add(Invocation.HttpMethod.POST);
			}
			if (isPutAllowed) {
				methods.add(Invocation.HttpMethod.PUT);
			}
			if (isDeleteAllowed) {
				methods.add(Invocation.HttpMethod.DELETE);
			}
			if (isTraceAllowed) {
				methods.add(Invocation.HttpMethod.TRACE);
			}
			inv.getUser().methodsAllowed(uriPattern, methods);
			update(uriPattern, methods);
			Hiber.close();
			inv.sendSeeOther(getUri());
		}
	}

	public List<Invocation.HttpMethod> getMethods() {
		List<Invocation.HttpMethod> methods = new ArrayList<Invocation.HttpMethod>();
		if (isOptionsAllowed) {
			methods.add(Invocation.HttpMethod.OPTIONS);
		}
		if (isGetAllowed) {
			methods.add(Invocation.HttpMethod.GET);
		}
		if (isHeadAllowed) {
			methods.add(Invocation.HttpMethod.HEAD);
		}
		if (isPostAllowed) {
			methods.add(Invocation.HttpMethod.POST);
		}
		if (isPutAllowed) {
			methods.add(Invocation.HttpMethod.PUT);
		}
		if (isDeleteAllowed) {
			methods.add(Invocation.HttpMethod.DELETE);
		}
		if (isTraceAllowed) {
			methods.add(Invocation.HttpMethod.TRACE);
		}
		return methods;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public boolean isMethodAllowed(Invocation.HttpMethod method) {
		boolean isMethodAllowed = false;
		switch (method) {
		case GET:
			isMethodAllowed = getIsGetAllowed();
			break;
		case POST:
			isMethodAllowed = getIsPostAllowed();
			break;
		case PUT:
			isMethodAllowed = getIsPutAllowed();
			break;
		case DELETE:
			isMethodAllowed = getIsDeleteAllowed();
			break;
		}
		return isMethodAllowed;
	}
}