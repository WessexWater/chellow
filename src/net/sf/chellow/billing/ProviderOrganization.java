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

package net.sf.chellow.billing;

import org.hibernate.exception.ConstraintViolationException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.Organization;

public abstract class ProviderOrganization extends Provider {
	private Organization organization;

	public ProviderOrganization() {
	}

	public ProviderOrganization(String name, Organization organization) {
		super(name);
		setOrganization(organization);
	}

	public Accounts accountsInstance() {
		return new Accounts(this);
	}

	public Account insertAccount(String reference) throws UserException,
			ProgrammerException {
		Account account = new Account(this, reference);
		try {
			Hiber.session().save(account);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw UserException
					.newInvalidParameter("There's already an account with the reference, '" + reference + "' attached to this provider.");
		}
		return account;
	}

	public Organization getOrganization() {
		return organization;
	}

	void setOrganization(Organization organization) {
		this.organization = organization;
	}
}