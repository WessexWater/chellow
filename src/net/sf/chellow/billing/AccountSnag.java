/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.SnagDateBounded;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class AccountSnag extends SnagDateBounded {
	public static final String MISSING_BILL = "Missing bill.";

	public static AccountSnag getAccountSnag(Long id) throws HttpException {
		AccountSnag snag = (AccountSnag) Hiber.session().get(AccountSnag.class,
				id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	public static void insertSnagAccount(AccountSnag snag) {
		Hiber.session().save(snag);
	}

	public static void deleteAccountSnag(AccountSnag snag) {
		Hiber.session().delete(snag);
	}

	private Account account;

	public AccountSnag() {
	}

	public AccountSnag(String description, Account account,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		super(description, startDate, finishDate);
		this.account = account;
	}

	public Account getAccount() {
		return account;
	}

	void setAccount(Account account) {
		this.account = account;
	}

	public void update() {
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "account-snag");
		return element;
	}

	public AccountSnag copy() throws InternalException {
		AccountSnag cloned;
		try {
			cloned = (AccountSnag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return super.toString();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("contract",
				new XmlTree("party")).put("account")));
		return doc;
	}

	public MonadUri getUri() throws HttpException {
		return getContract().getSnagsAccountInstance().getUri().resolve(
				getUriId()).append("/");
	}

	/*
	 * public boolean isCombinable(SnagDateBounded snag) throws
	 * ProgrammerException, UserException { Bill incomingBill = ((AccountSnag)
	 * snag).getBill(); return super.isCombinable(snag) && ((incomingBill ==
	 * null && getBill() == null) || (incomingBill != null && incomingBill
	 * .equals(getBill()))); }
	 */

	@Override
	public Contract getContract() {
		return account.getContract();
	}

	@Override
	public void setContract(Contract contract) {
	}
}
