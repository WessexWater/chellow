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

package net.sf.chellow.physical;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplyGenerations extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("generations");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Supply supply;

	SupplyGenerations(Supply supply) {
		setSupply(supply);
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Supply getSupply() {
		return supply;
	}

	public MonadUri getUri() throws HttpException {
		return supply.getUri().resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public void httpPost(Invocation inv) throws HttpException {
		MonadDate finishDate = inv.getMonadDate("finish-date");
		SupplyGeneration supplyGeneration = supply.addGeneration(HhEndDate
				.roundDown(finishDate.getDate()));
		Hiber.commit();
		inv.sendCreated(document(), supplyGeneration.getUri());
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element generationsElement = toXml(doc);
		source.appendChild(generationsElement);
		generationsElement.appendChild(supply.toXml(doc));
		for (SupplyGeneration supplyGeneration : supply.getGenerations()) {
			generationsElement.appendChild(supplyGeneration.toXml(doc,
					new XmlTree("mpans", new XmlTree("core").put("top",
							new XmlTree("pc").put("llfc").put("mtc").put(
									"gspGroup")))));
		}
		source.appendChild(new MonadDate().toXml(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public SupplyGeneration getChild(UriPathElement uriId) throws HttpException {
		SupplyGeneration supplyGeneration = (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration supplyGeneration where supplyGeneration.supply = :supply and supplyGeneration.id = :supplyGenerationId")
				.setEntity("supply", supply).setLong("supplyGenerationId",
						Long.parseLong(uriId.toString())).uniqueResult();
		if (supplyGeneration == null) {
			throw new NotFoundException();
		}
		return supplyGeneration;
	}

	public Element toXml(Document doc) throws HttpException {
		return doc.createElement("supply-generations");
	}
}