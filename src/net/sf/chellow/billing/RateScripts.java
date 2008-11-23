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
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.HhEndDate;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class RateScripts extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("rate-scripts");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Contract contract;

	public RateScripts(Contract contract) {
		setContract(contract);
	}

	public Contract getContract() {
		return contract;
	}

	void setContract(Contract contract) {
		this.contract = contract;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return contract.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		Date startDate = inv.getDate("start-date");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			RateScript rateScript = contract.insertRateScript(HhEndDate
					.roundDown(startDate).getNext(), "");
			Hiber.commit();
			Hiber.flush();
			inv.sendCreated(document(), rateScript.getUri());
		} catch (HttpException e) {
			Hiber.rollBack();
			e.setDocument(document());
			throw e;
		}
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public RateScript getChild(UriPathElement uriId) throws HttpException {
		RateScript script = (RateScript) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract and script.id = :scriptId")
				.setEntity("contract", contract).setLong("scriptId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (script == null) {
			throw new NotFoundException();
		}
		return script;
	}

	public Element toXml(Document doc) throws HttpException {
		Element rateScriptsElement = doc.createElement("rate-scripts");
		return rateScriptsElement;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element scriptsElement = toXml(doc);
		source.appendChild(scriptsElement);
		scriptsElement.appendChild(contract.toXml(doc, new XmlTree("party")));
		for (RateScript script : (List<RateScript>) Hiber
				.session()
				.createQuery(
						"from RateScript script where script.contract = :contract order by script.startDate.date")
				.setEntity("contract", contract).list()) {
			scriptsElement.appendChild(script.toXml(doc));
		}
		source.appendChild(new MonadDate().toXml(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}
}