/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Role extends PersistentEntity {
	static public Role getRole(MonadLong id) throws InternalException {
		return getRole(id.getLong());
	}

	static public Role getRole(Long id) throws InternalException {
		try {
			return (Role) Hiber.session().get(Role.class, id);
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	@SuppressWarnings("unchecked")
	static public List<Role> getRoles() throws InternalException {
		return (List<Role>) Hiber.session().createQuery("from Role role")
				.list();
	}

	static public Role find(String name) throws InternalException {
		return (Role) Hiber.session().createQuery(
				"from Role role where role.name = :roleName").setString(
				"roleName", name).uniqueResult();
	}

	static public Role insertRole(String name) throws InternalException,
			HttpException {
		Role role = new Role(name);
		Hiber.session().save(role);
		return role;
	}

	private String name;

	private Set<Permission> permissions;

	public Role() {
		setTypeName("role");
	}

	Role(String name) throws InternalException, HttpException {
		this();
		update(name);
	}

	public void update(String name) {
		setName(name);
	}

	public String getName() {
		return name;
	}

	protected void setName(String name) {
		this.name = name;
	}

	public Set<Permission> getPermissions() {
		if (permissions == null) {
			permissions = new HashSet<Permission>();
		}
		return permissions;
	}

	protected void setPermissions(Set<Permission> permissions) {
		this.permissions = permissions;
	}

	public boolean equals(Object object) {
		boolean isEqual = false;
		if (object instanceof Role) {
			Role user = (Role) object;
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

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = (Element) super.toXml(doc);
		element.setAttributeNode(MonadString.toXml(doc, "name", name));
		return element;
	}

	public Permission insertPermission(MonadUri uriPattern,
			Invocation.HttpMethod[] methods) throws InternalException,
			HttpException {
		return insertPermission(uriPattern.getString(), methods);
	}

	public Permission insertPermission(String uriPattern,
			Invocation.HttpMethod[] methods) throws InternalException,
			HttpException {
		return insertPermission(uriPattern, Arrays.asList(methods));
	}

	public Permission insertPermission(MonadString uriPattern,
			List<Invocation.HttpMethod> methods) throws InternalException,
			HttpException {
		return insertPermission(uriPattern.getString(), methods);
	}

	public Permission insertPermission(String uriPattern,
			List<Invocation.HttpMethod> methods) throws InternalException,
			HttpException {
		return insertPermission(uriPattern, methods
				.contains(Invocation.HttpMethod.OPTIONS), methods
				.contains(Invocation.HttpMethod.GET), methods
				.contains(Invocation.HttpMethod.HEAD), methods
				.contains(Invocation.HttpMethod.POST), methods
				.contains(Invocation.HttpMethod.PUT), methods
				.contains(Invocation.HttpMethod.DELETE), methods
				.contains(Invocation.HttpMethod.TRACE));
	}

	public Permission insertPermission(String uriPattern,
			boolean isOptionsAllowed, boolean isGetAllowed,
			boolean isHeadAllowed, boolean isPostAllowed, boolean isPutAllowed,
			boolean isDeleteAllowed, boolean isTraceAllowed)
			throws InternalException, HttpException {
			return insertPermission(new MonadUri(uriPattern),
					isOptionsAllowed, isGetAllowed,
					isHeadAllowed,
							isPostAllowed, isPutAllowed,
					isDeleteAllowed,
							isTraceAllowed);
	}

	Permission insertPermission(MonadUri uriPattern,
			Boolean isOptionsAllowed, Boolean isGetAllowed,
			Boolean isHeadAllowed, Boolean isPostAllowed,
			Boolean isPutAllowed, Boolean isDeleteAllowed,
			Boolean isTraceAllowed) throws InternalException,
			HttpException {
		Permission permission;
		try {
			permission = new Permission(this, uriPattern, isOptionsAllowed,
					isGetAllowed, isHeadAllowed, isPostAllowed, isPutAllowed,
					isDeleteAllowed, isTraceAllowed);
			Hiber.session().save(permission);
			Hiber.session().flush();
		} catch (ConstraintViolationException e) {
			throw new UserException
					("For this role, there's already a permission with this URI");
		}
		if (permissions == null) {
			permissions = new HashSet<Permission>();
		}
		permissions.add(permission);
		return permission;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.ROLES_INSTANCE.getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		if (Permissions.URI_ID.equals(uriId)) {
			return permissionsInstance();
		} else {
			return null;
		}
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("permissions")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		if (inv.hasParameter("delete")) {
			Hiber.session().delete(this);
			Hiber.close();
			inv.sendSeeOther(Chellow.ROLES_INSTANCE.getUri());
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Permissions permissionsInstance() {
		return new Permissions(this);
	}
}