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

package net.sf.chellow.billing;

import java.util.Date;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Participant;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Provider extends Party {
	static public Provider getProvider(String participantCode, char roleCode)
			throws HttpException {
		Participant participant = Participant.getParticipant(participantCode);
		MarketRole role = MarketRole.getMarketRole(roleCode);
		Provider provider = (Provider) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.participant = :participant and provider.role = :role")
				.setEntity("participant", participant).setEntity("role", role)
				.uniqueResult();
		if (provider == null) {
			throw new NotFoundException(
					"There isn't a provider with participant code "
							+ participant.getCode() + " ("
							+ participant.getName() + ") and role code "
							+ role.getCode() + " (" + role.getDescription()
							+ ").");
		}
		return provider;
	}

	static public Provider getProvider(long id) throws HttpException {
		Provider provider = (Provider) Hiber.session().get(Provider.class, id);
		if (provider == null) {
			throw new NotFoundException();
		}
		return provider;
	}

	public Provider() {
	}

	public Provider(String name, Participant participant, char role,
			Date validFrom, Date validTo) throws HttpException {
		super(name, participant, role, validFrom, validTo);
	}

	public Element toXml(Document doc) throws HttpException {
		return super.toXml(doc, "provider");
	}

	/*
	 * public Account getAccount(String accountText) throws HttpException {
	 * Account account = (Account) Hiber .session() .createQuery( "from Account
	 * account where account.provider = :provider and account.reference =
	 * :accountReference") .setEntity("provider",
	 * this).setString("accountReference", accountText.trim()).uniqueResult();
	 * if (account == null) { throw new UserException("There isn't an account
	 * for '" + getName() + "' with the reference '" + accountText + "'."); }
	 * return account; }
	 */

	@Override
	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("participant").put("role")));
		inv.sendOk(doc);
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}
}