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

import java.util.List;

import net.sf.chellow.billing.Party;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.Me;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Users extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("users");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Users() {
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUriId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		EmailAddress emailAddress = inv.getEmailAddress("email-address");
		String password = inv.getString("password");
		long userRoleId = inv.getLong("user-role-id");

		if (!inv.isValid()) {
			throw new UserException(document());
		}
		UserRole role = UserRole.getUserRole(userRoleId);
		try {
			Party party = null;
			if (role.getCode().equals(UserRole.PARTY_VIEWER)) {
				String participantCode = inv.getString("participant-code");
				Long marketRoleId = inv.getLong("market-role-id");

				party = Party.getParty(Participant.getParticipant(participantCode), MarketRole
						.getMarketRole(marketRoleId));
			}
			User user = User
					.insertUser(emailAddress, password, null, role, party);
			Hiber.commit();
			inv.sendCreated(user.getUri());
		} catch (HttpException e) {
			Hiber.rollBack();
			e.setDocument(document());
			throw e;
		}
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element usersElement = toXml(doc);
		source.appendChild(usersElement);
		for (User user : (List<User>) Hiber.session().createQuery(
				"from User user").list()) {
			usersElement.appendChild(user.toXml(doc, new XmlTree("role")));
		}
		for (MarketRole role : (List<MarketRole>) Hiber.session().createQuery(
				"from MarketRole role").list()) {
			source.appendChild(role.toXml(doc));
		}
		for (UserRole role : (List<UserRole>) Hiber.session().createQuery(
		"from UserRole role").list()) {
	source.appendChild(role.toXml(doc));
}
		return doc;
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Me.URI_ID.equals(uriId)) {
			return new Me();
		} else {
			return (User) Hiber.session().createQuery(
					"from User user where user.id = :userId").setLong("userId",
					Long.parseLong(uriId.getString())).uniqueResult();
		}
	}

	public User findUser(EmailAddress emailAddress) throws InternalException {
		return (User) Hiber
				.session()
				.createQuery(
						"from User user where user.emailAddress.address = :emailAddress")
				.setString("emailAddress", emailAddress.toString())
				.uniqueResult();
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("users");
	}
}