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

package net.sf.chellow.billing;

import java.net.URI;
import java.util.Date;
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplierContracts extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("supplier-contracts");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public SupplierContracts() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getEditUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		Long participantId = inv.getLong("participant-id");
		String name = inv.getString("name");
		Date startDate = inv.getDateTime("start");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			SupplierContract contract = SupplierContract
					.insertSupplierContract(null,
							Participant.getParticipant(participantId), name,
							HhStartDate.roundDown(startDate), null, "", null,
							"");
			Hiber.commit();
			inv.sendSeeOther(contract.getEditUri());
		} catch (UserException e) {
			e.setDocument(document());
			throw e;
		}
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element contractsElement = toXml(doc);
		source.appendChild(contractsElement);
		for (Provider provider : (List<Provider>) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.role.code = :roleCode order by provider.participant.code")
				.setCharacter("roleCode", MarketRole.SUPPLIER).list()) {
			source.appendChild(provider.toXml(doc, new XmlTree("participant")));
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

	public SupplierContract getChild(UriPathElement uriId)
			throws HttpException, InternalException {
		SupplierContract contract = (SupplierContract) Hiber
				.session()
				.createQuery(
						"from SupplierContract contract where contract.id = :contractId")
				.setLong("contractId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException();
		}
		return contract;
	}

	public Element toXml(Document doc) throws HttpException {
		Element contractsElement = doc.createElement("supplier-contracts");
		return contractsElement;
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
