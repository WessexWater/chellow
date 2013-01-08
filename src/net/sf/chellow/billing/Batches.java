/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2011 Wessex Water Services Limited
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
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Batches extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("batches");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Contract contract;

	public Batches(Contract contract) {
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

	public MonadUri getEditUri() throws HttpException {
		return contract.getEditUri().resolve(getUrlId()).append("/");
	}

	public URI getViewUri() throws HttpException {
		return null;
	}

	public void httpPost(Invocation inv) throws HttpException {
		Hiber.setReadWrite();
		String reference = inv.getString("reference");
		String description = inv.getString("description");

		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Document doc = document();
		Batch batch = null;
		try {
			batch = contract.insertBatch(reference, description);
		} catch (UserException e) {
			e.setDocument(doc);
			throw e;
		}
		Hiber.commit();
		inv.sendSeeOther(batch.getViewUri());
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Batch getChild(UriPathElement uriId) throws HttpException {
		Batch batch = (Batch) Hiber
				.session()
				.createQuery(
						"from Batch batch where batch.contract = :contract and batch.id = :batchId")
				.setEntity("contract", contract)
				.setLong("batchId", Long.parseLong(uriId.getString()))
				.uniqueResult();
		if (batch == null) {
			throw new NotFoundException("Can't find the batch " + uriId + ".");
		}
		return batch;
	}

	public Node toXml(Document doc) throws HttpException {
		Element batchesElement = doc.createElement("batches");
		return batchesElement;
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element batchesElement = (Element) toXml(doc);
		source.appendChild(batchesElement);
		batchesElement.appendChild(contract.toXml(doc, new XmlTree("party")));
		for (Batch batch : (List<Batch>) Hiber
				.session()
				.createQuery(
						"from Batch batch where batch.contract = :contract order by batch.reference")
				.setEntity("contract", contract).list()) {
			batchesElement.appendChild(batch.toXml(doc));
		}
		return doc;
	}
}
