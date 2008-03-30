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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import net.sf.chellow.ui.ExplicitMe;
import net.sf.chellow.ui.ImplicitMe;
import net.sf.chellow.ui.NewUserForm;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Users implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("users");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	public Users() {
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return new MonadUri("/").resolve(getUriId()).append("/");
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		EmailAddress emailAddress = inv.getEmailAddress("email-address");
		Password password = inv.getValidatable(Password.class, "password");

		if (!inv.isValid()) {
			throw UserException.newInvalidParameter();
		}
		User user = User.insertUser(emailAddress, password);
		user.userRole(inv.getUser()).insertPermission(
				user.getUri(),
				new Invocation.HttpMethod[] { Invocation.HttpMethod.GET,
						Invocation.HttpMethod.POST });
		user.insertRole(inv.getUser(), Role.find("basic-user"));
		inv.getUser().userRole(inv.getUser()).insertPermission(
				user.getUri(),
				new Invocation.HttpMethod[] { Invocation.HttpMethod.GET,
						Invocation.HttpMethod.POST });
		Hiber.commit();
		inv.sendCreated(user.getUri());
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element usersElement = (Element) toXML(doc);
		source.appendChild(usersElement);
		for (User user : (List<User>) Hiber.session().createQuery(
				"from User user").list()) {
			usersElement.appendChild(user.toXML(doc));
		}
		inv.sendOk(doc);
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		Urlable urlable = null;
		if (NewUserForm.URI_ID.equals(uriId)) {
			urlable = new NewUserForm();
		} else if (ImplicitMe.URI_ID.equals(uriId)) {
			urlable = new ImplicitMe();
		} else if (ExplicitMe.URI_ID.equals(uriId)) {
			urlable = new ExplicitMe();
		} else {
			urlable = (User) Hiber.session().createQuery(
					"from User user where user.id = :userId").setLong("userId",
					Long.parseLong(uriId.getString())).uniqueResult();
		}
		return urlable;
	}

	public User findUser(EmailAddress emailAddress) throws ProgrammerException,
			UserException {
		return (User) Hiber
				.session()
				.createQuery(
						"from User user where user.emailAddress.address = :emailAddress")
				.setString("emailAddress", emailAddress.toString())
				.uniqueResult();
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public UriPathElement setUriId(UriPathElement uriId)
			throws ProgrammerException {
		// TODO Auto-generated method stub
		return null;
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		return doc.createElement("users");
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}