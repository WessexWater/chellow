/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2013 Wessex Water Services Limited
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

package net.sf.chellow.billing;

import java.net.URI;
import java.util.Date;
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.Participant;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class NonCoreContracts implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("non-core-contracts");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public NonCoreContracts() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getEditUri() throws HttpException {
		return new MonadUri("/").resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		Long participantId = inv.getLong("participant-id");
		boolean isCore = inv.getBoolean("is-core");
		String name = inv.getString("name");
		Date startDate = inv.getDateTime("start");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Contract contract = Contract.insertNonCoreContract(isCore,
				Participant.getParticipant(participantId), name,
				HhStartDate.roundDown(startDate), null, "", "");
		Hiber.commit();
		inv.sendSeeOther("/non-core-contracts/" + contract.getId());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element contractsElement = toXml(doc);
		source.appendChild(contractsElement);
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract order by contract.finishRateScript.finishDate.date desc, contract.party.participant.code")
				.list()) {
			Element contractElement = contract.toXml(doc);
			contractsElement.appendChild(contractElement);
			contractElement.appendChild(contract.getParty().toXml(doc));
		}
		for (Party party : (List<Party>) Hiber
				.session()
				.createQuery(
						"from Party party where party.role.code = 'Z' order by party.participant.code, party.name")
				.list()) {
			Element partyElement = party.toXml(doc);
			source.appendChild(partyElement);
			partyElement.appendChild(party.getParticipant().toXml(doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(MonadDate.getHoursXml(doc));
		source.appendChild(HhStartDate.getHhMinutesXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Contract getChild(UriPathElement uriId) throws HttpException {
		Contract contract = (Contract) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.id = :contractId")
				.setLong("contractId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException();
		}
		return contract;
	}

	public Element toXml(Document doc) throws HttpException {
		Element contractsElement = doc.createElement("non-core-contracts");
		return contractsElement;
	}

	public void httpDelete(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}