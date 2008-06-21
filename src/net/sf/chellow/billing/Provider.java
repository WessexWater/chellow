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

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.SupplyGeneration;

import org.hibernate.HibernateException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class Provider extends PersistentEntity implements Urlable {
	public static Provider getSupplier(Long id) throws HttpException {
		Provider supplier = (Provider) Hiber.session().get(Provider.class, id);
		if (supplier == null) {
			throw new UserException("There isn't a supplier with that id.");
		}
		return supplier;
	}

	public static void deleteSupplier(Provider supplier)
			throws InternalException {
		try {
			Hiber.session().delete(supplier);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	private String name;

	public Provider() {
	}

	public Provider(String name) {
		update(name);
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public void update(String name) {
		setName(name);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = (Element) super.toXml(doc);

		element.setAttributeNode((Attr) MonadString.toXml(doc, "name", name));
		return element;
	}

	public Account getAccount(String accountText) throws HttpException,
			InternalException {
		Account account = (Account) Hiber
				.session()
				.createQuery(
						"from Account account where account.provider = :provider and account.reference = :accountReference")
				.setEntity("provider", this).setString("accountReference",
						accountText.trim()).uniqueResult();
		if (account == null) {
			throw new UserException("There isn't an account for '" + getName()
					+ "' with the reference '" + accountText + "'.");
		}
		return account;
	}

	@SuppressWarnings("unchecked")
	public void deleteAccount(Account account) throws HttpException,
			InternalException {
		if (!account.getProvider().equals(this)) {
			throw new UserException(
					"The account isn't attached to this provider.");
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

	abstract public List<SupplyGeneration> supplyGenerations(Account account);

	public abstract Service getService(String name) throws HttpException,
			InternalException;
}