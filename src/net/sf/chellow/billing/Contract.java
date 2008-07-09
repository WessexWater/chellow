/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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

import java.util.List;

import org.hibernate.exception.ConstraintViolationException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;

public abstract class Contract extends Service {
	private Provider provider;
	private Organization organization;

	public Contract() {
	}

	public Contract(Provider provider, Organization organization, String name,
			HhEndDate startDate, String chargeScript) throws HttpException {
		super(Service.TYPE_CONTRACT, name, startDate, chargeScript);
		setOrganization(organization);
	}

	public Organization getOrganization() {
		return organization;
	}

	void setOrganization(Organization organization) {
		this.organization = organization;
	}
	
	public Provider getProvider() {
		return provider;
	}
	
	void setProvider(Provider provider) {
		this.provider = provider;
	}

	public Batch insertBatch(String reference) {
		Batch batch = new Batch(this, reference);
		Hiber.session().save(batch);
		return batch;
	}

	public void internalUpdate(String name, String chargeScript)
			throws HttpException {
		super.internalUpdate(Service.TYPE_CONTRACT, name, chargeScript);
	}

	public void update(String name, String chargeScript) throws HttpException {
		super.update(Service.TYPE_CONTRACT, name, chargeScript);
	}

	@SuppressWarnings("unchecked")
	public void deleteAccount(Account account) throws HttpException,
			InternalException {
		if (!account.getContract().equals(this)) {
			throw new UserException(
					"The account isn't attached to this contract.");
		}
		if ((Long) Hiber.session().createQuery(
				"select count(*) from Bill bill where bill.account = :account")
				.setEntity("account", account).uniqueResult() > 0) {
			throw new UserException(
					"Can't delete this account as there are still bills attached to it.");
		}
		if ((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from Mpan mpan where mpan.supplierAccount.id = :accountId")
				.setLong("accountId", account.getId()).uniqueResult() > 0) {
			throw new UserException(
					"Can't delete this account as there are still MPANs attached to it.");
		}
		for (AccountSnag snag : (List<AccountSnag>) Hiber.session()
				.createQuery(
						"from AccountSnag snag where snag.account = :account")
				.setEntity("account", account).list()) {
			Hiber.session().delete(snag);
			Hiber.flush();
		}
		Hiber.session().delete(account);
		Hiber.flush();
	}

	public Accounts accountsInstance() {
		return new Accounts(this);
	}

	public Account insertAccount(String reference) throws HttpException {
		Account account = new Account(this, reference);
		try {
			Hiber.session().save(account);
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException(
					"There's already an account with the reference, '"
							+ reference + "' attached to this provider.");
		}
		return account;
	}
	
public Account getAccount(String reference) throws HttpException {
	Account account = (Account) Hiber.session().createQuery("from Account account where account.contract = :contract and account.reference = :reference").setEntity("contract", this).setString("reference", reference).uniqueResult();
	if (account == null) {
		throw new NotFoundException();
	}
	return account;
}
public Batches batchesInstance() {
	return new Batches(this);
}
}