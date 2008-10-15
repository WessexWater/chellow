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
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.ContractFrequency;
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class HhdcContracts extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("hhdc-contracts");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public HhdcContracts() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		Long providerId = inv.getLong("provider-id");
		String name = inv.getString("name");
		ContractFrequency frequency = inv.getValidatable(
				ContractFrequency.class, "frequency");
		Date startDate = inv.getDate("start-date");
		String chargeScript = inv.getString("charge-script");
		Integer lag = inv.getInteger("lag");
		String importerProperties = inv.toString();
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Provider provider = Provider.getProvider(providerId);
		HhdcContract contract = HhdcContract.insertHhdcContract(provider, name,
				HhEndDate.roundDown(startDate), chargeScript, frequency, lag,
				importerProperties);
		Hiber.commit();
		inv.sendCreated(document(), contract.getUri());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element contractsElement = toXml(doc);
		source.appendChild(contractsElement);
		for (HhdcContract contract : (List<HhdcContract>) Hiber.session()
				.createQuery(
						"from HhdcContract contract order by contract.name")
				.list()) {
			contractsElement.appendChild(contract.toXml(doc, new XmlTree(
					"party")));
		}
		for (Provider provider : (List<Provider>) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.role.code = :roleCode order by provider.participant.code")
				.setCharacter("roleCode", MarketRole.HHDC).list()) {
			source.appendChild(provider.toXml(doc, new XmlTree("participant")));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public HhdcContract getChild(UriPathElement uriId) throws HttpException {
		HhdcContract contract = (HhdcContract) Hiber.session().createQuery(
				"from HhdcContract contract where contract.id = :contractId")
				.setLong("contractId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException();
		}
		return contract;
	}

	public Element toXml(Document doc) throws HttpException {
		Element contractsElement = doc.createElement("hhdc-contracts");
		return contractsElement;
	}
}