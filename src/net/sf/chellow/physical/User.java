/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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

import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.SQLException;

import net.sf.chellow.billing.Party;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.exception.ConstraintViolationException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.Base64;

public class User extends PersistentEntity {
	public static final UriPathElement USERS_URI_ID;

	static {
		try {
			USERS_URI_ID = new UriPathElement("users");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String emailAddressStr = GeneralImport.addField(csvElement,
					"Email Address", values, 0);
			EmailAddress emailAddress = new EmailAddress(emailAddressStr);
			String password = GeneralImport.addField(csvElement, "Password",
					values, 1);
			String passwordDigest = GeneralImport.addField(csvElement,
					"Password Digest", values, 2);
			String userRoleCode = GeneralImport.addField(csvElement,
					"User Role Code", values, 3);
			UserRole userRole = UserRole.getUserRole(userRoleCode);
			String participantCode = GeneralImport.addField(csvElement,
					"Participant Code", values, 4);
			Party party = null;
			if (participantCode.trim().length() != 0) {
				String marketRoleCode = GeneralImport.addField(csvElement,
						"Market Role Code", values, 5);
				party = Party.getParty(participantCode, marketRoleCode);
			}
			User.insertUser(emailAddress, password.trim().length() == 0 ? null
					: password, passwordDigest.trim().length() == 0 ? null
					: passwordDigest, userRole, party);
		} else if (action.equals("update")) {
		}
	}

	static public User getUser(Long id) {
		return (User) Hiber.session().get(User.class, id);
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

	static public User insertUser(EmailAddress emailAddress, String password,
			String passwordDigest, UserRole userRole, Party party)
			throws HttpException {
		User user = null;
		try {
			user = new User(emailAddress, password, passwordDigest, userRole,
					party);
			Hiber.session().setDefaultReadOnly(false);
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
						throw new UserException(
								"There is already a user with this email address.");
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

	public static String digest(String password) throws HttpException {
		try {
			MessageDigest md = MessageDigest.getInstance("SHA-256");
			md.update(password.getBytes("UTF-8"));
			return Base64.encodeToString(md.digest());
		} catch (NoSuchAlgorithmException e) {
			throw new InternalException(e.getMessage());
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e.getMessage());
		}
	}

	private EmailAddress emailAddress;

	private String passwordDigest;

	private UserRole role;

	private Party party;

	public User() {
	}

	public User(EmailAddress emailAddress, String password,
			String passwordDigest, UserRole role, Party party)
			throws HttpException {
		update(emailAddress, password, passwordDigest, role, party);
	}

	public void update(EmailAddress emailAddress, String password,
			String passwordDigest, UserRole role, Party party)
			throws HttpException {
		setEmailAddress(emailAddress);
		if (password == null) {
			if (passwordDigest == null) {
				throw new UserException(
						"There must be either a password or a password digest.");
			}
		} else {
			if (passwordDigest == null) {
				passwordDigest = digest(password);
			} else {
				throw new UserException(
						"There can't be both a password and password digest.");
			}
		}
		setPasswordDigest(passwordDigest);
		setRole(role);
		if (role.getCode().equals(UserRole.PARTY_VIEWER)) {
			if (party == null) {
				throw new UserException(
						"There must be a party if the role is party-viewer.");
			}
			setParty(party);
		} else {
			setParty(null);
		}
	}

	public String getPasswordDigest() {
		return passwordDigest;
	}

	protected void setPasswordDigest(String passwordDigest) {
		this.passwordDigest = passwordDigest;
	}

	public EmailAddress getEmailAddress() {
		return emailAddress;
	}

	protected void setEmailAddress(EmailAddress emailAddress) {
		this.emailAddress = emailAddress;
	}

	public UserRole getRole() {
		return role;
	}

	protected void setRole(UserRole role) {
		this.role = role;
	}

	public Party getParty() {
		return party;
	}

	void setParty(Party party) {
		this.party = party;
	}

	public boolean equals(Object object) {
		boolean isEqual = false;
		if (object instanceof User) {
			User user = (User) object;
			isEqual = user.getId().equals(getId());
		}
		return isEqual;
	}

	@Override
	public MonadUri getEditUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public Node toXml(Document doc) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
