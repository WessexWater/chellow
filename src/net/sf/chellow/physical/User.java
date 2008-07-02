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

import java.net.URI;
import java.sql.SQLException;
import java.util.HashSet;
import java.util.Set;

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
import net.sf.chellow.monad.Invocation.HttpMethod;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class User extends PersistentEntity {
	public static final UriPathElement USERS_URI_ID;

	static {
		try {
			USERS_URI_ID = new UriPathElement("users");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	static public User getUser(Long id) throws InternalException {
		try {
			return (User) Hiber.session().get(User.class, id);
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	static public User findUserByEmail(EmailAddress emailAddress)
			throws InternalException {
		return (User) Hiber
				.session()
				.createQuery(
						"from User user where user.emailAddress.address = :emailAddress")
				.setString("emailAddress", emailAddress.getAddress())
				.uniqueResult();
	}

	static public User insertUser(EmailAddress emailAddress, Password password)
			throws InternalException, HttpException {
		User user = null;
		try {
			user = new User(emailAddress, password);
			Hiber.session().save(user);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			SQLException sqle = e.getSQLException();
			if (sqle != null) {
				Exception nextException = sqle.getNextException();
				if (nextException != null) {
					String message = nextException.getMessage();
					if (message != null
							&& message.contains("user_email_address_key")) {
						throw new UserException
								("There is already a user with this email address.");
					} else {
						throw e;
					}
				} else {
					throw e;
				}
			} else {
				throw e;
			}
		}
		return user;
	}

	private EmailAddress emailAddress;

	private Password password;

	private Set<Role> roles;

	public User() {
		setTypeName("user");
	}

	public User(EmailAddress emailAddress, Password password)
			throws InternalException,
			HttpException {
		update(emailAddress, password);
	}

	public void update(EmailAddress emailAddress, Password password) {
		setEmailAddress(emailAddress);
		setPassword(password);
	}

	public Password getPassword() {
		return password;
	}

	protected void setPassword(Password password) {
		this.password = password;
	}

	public EmailAddress getEmailAddress() {
		return emailAddress;
	}

	protected void setEmailAddress(EmailAddress emailAddress) {
		this.emailAddress = emailAddress;
	}

	public Set<Role> getRoles() {
		return roles;
	}

	protected void setRoles(Set<Role> roles) {
		this.roles = roles;
	}

	public boolean equals(Object object) {
		boolean isEqual = false;
		if (object instanceof User) {
			User user = (User) object;
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
		element.setAttributeNode((Attr) emailAddress.toXml(doc));
		return element;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.USERS_INSTANCE.getUri().resolve(getUriId());
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
		return document(null);
	}

	private Document document(String message) throws InternalException,
			HttpException, DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("roles")));
		if (message != null) {
			//source.appendChild(new VFMessage(message).toXML(doc));
		}
		return doc;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		if (inv.hasParameter("delete")) {
			Hiber.session().delete(this);
			Hiber.close();
			inv.sendSeeOther(Chellow.USERS_INSTANCE.getUri());
		} else if (inv.hasParameter("role-id")) {
			MonadLong roleId = inv.getMonadLong("role-id");
			Role role = Role.getRole(roleId);
			insertRole(inv.getUser(), role);
			Hiber.close();
			inv.sendSeeOther(getUri());
		} else if (inv.hasParameter("current-password")) {
			Password currentPassword = inv.getValidatable(Password.class,
					"current-password");
			Password newPassword = inv.getValidatable(Password.class,
					"new-password");
			Password confirmNewPassword = inv.getValidatable(Password.class,
					"confirm-new-password");
			
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			if (!getPassword().equals(currentPassword)) {
				throw new UserException
						("The current password is incorrect.");
			}
			if (!newPassword.equals(confirmNewPassword)) {
				throw new UserException
						("The new passwords aren't the same.");
			}
			setPassword(newPassword);
			Hiber.commit();
			inv.sendOk(document("New password set successfully."));
		} else {
			throw new UserException
					("I can't really see what you're trying to do.");
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
	}

	public void insertRole(User user, Role role) throws InternalException,
			HttpException {
		if (roles == null) {
			roles = new HashSet<Role>();
		}
		for (Permission permission : role.getPermissions()) {
			Permission.methodsAllowed(user, permission.getUriPattern(),
					permission.getMethods());
		}
		roles.add(role);
	}

	public Role userRole(User user) throws InternalException, HttpException {
		String userRoleName = "user-" + getId();
		Role userRole = Role.find(userRoleName);
		if (userRole == null) {
			userRole = Role.insertRole(userRoleName);
			insertRole(user, userRole);
			userRole.insertPermission(userRole.getUri(),
					new Invocation.HttpMethod[] { Invocation.HttpMethod.GET });
		}
		return userRole;
	}
	
	public boolean methodAllowed(URI uri, HttpMethod method) {
		for (Role role : getRoles()) {
			if (role.methodAllowed(uri, method)) {
				return true;
			}
		}
		return false;
	}
}