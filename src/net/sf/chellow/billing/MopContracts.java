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
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class MopContracts extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("services");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public MopContracts() {
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		String mopCode = inv.getString("mop-code");
		String name = inv.getString("name");
		Date startDate = inv.getDate("start-date");
		String chargeScript = inv.getString("charge-script");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Provider mop = Provider.getProvider(mopCode, MarketRole.MOP);
		MopContract contract = MopContract.insertMopContract(mop, name,
				HhEndDate.roundDown(startDate), null, chargeScript);
		Hiber.commit();
		inv.sendCreated(contract.getUri());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element contractsElement = toXml(doc);
		source.appendChild(contractsElement);
		for (HhdcContract contract : (List<HhdcContract>) Hiber
				.session()
				.createQuery(
						"from MopContract contract where contract order by contract.name")
				.list()) {
			contractsElement.appendChild(contract.toXml(doc));
		}
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MopContract getChild(UriPathElement uriId) throws HttpException {
		MopContract contract = (MopContract) Hiber.session().createQuery(
				"from MopContract contract where contract.id = :contractId")
				.setLong("contractId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException();
		}
		return contract;
	}

	public Element toXml(Document doc) throws HttpException {
		Element contractsElement = doc.createElement("mop-services");
		return contractsElement;
	}
}