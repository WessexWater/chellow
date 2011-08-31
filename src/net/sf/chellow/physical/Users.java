/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.physical;

import java.net.URI;
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

	public MonadUri getEditUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUriId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		EmailAddress emailAddress = inv.getEmailAddress("email-address");
		String password = inv.getString("password");
		Long userRoleId = inv.getLong("user-role-id");

		if (!inv.isValid()) {
			throw new UserException(document());
		}
		UserRole role = UserRole.getUserRole(userRoleId);
		try {
			Party party = null;
			if (role.getCode().equals(UserRole.PARTY_VIEWER)) {
				Long partyId = inv.getLong("party-id");
				if (!inv.isValid()) {
					throw new UserException(document());
				}
				party = Party.getParty(partyId);
			}
			User user = User.insertUser(emailAddress, password, null, role,
					party);
			Hiber.commit();
			inv.sendSeeOther(user.getEditUri());
		} catch (HttpException e) {
			Hiber.rollBack();
			e.setDocument(document());
			throw e;
		}
	}

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
			usersElement.appendChild(user.toXml(doc, new XmlTree("role").put("party")));
		}
		for (Party party : (List<Party>) Hiber
				.session()
				.createQuery(
						"from Party party order by party.role.code, party.participant.code")
				.list()) {
			source.appendChild(party.toXml(doc, new XmlTree("participant")
					.put("role")));
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

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
