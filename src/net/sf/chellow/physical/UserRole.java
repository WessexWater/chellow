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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;

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
}
