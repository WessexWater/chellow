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

package net.sf.chellow.physical;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;


import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class SupplyGenerations implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("generations");
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);		}
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

	public MonadUri getUri() throws ProgrammerException, UserException {
		return supply.getUri().resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		MonadDate finishDate = inv.getMonadDate("finish-date");
		SupplyGeneration supplyGeneration = supply.addGeneration(HhEndDate
				.roundDown(finishDate.getDate()));
		Hiber.commit();
		inv.sendCreated(document(), supplyGeneration.getUri());
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public Document document() throws DesignerException, ProgrammerException,
			UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		/*
		 * Element generationsElement = (Element) getXML( new
		 * XMLTree("siteSupplyGenerations", new XMLTree("site", new XMLTree(
		 * "organization")).put("supply")), doc);
		 */
		Element generationsElement = toXML(doc);
		source.appendChild(generationsElement);
		generationsElement.appendChild(supply.getXML(
				new XmlTree("organization"), doc));
		for (SupplyGeneration supplyGeneration : supply.getGenerations()) {
			generationsElement.appendChild(supplyGeneration.getXML(new XmlTree(
					"mpans", new XmlTree("mpanCore")), doc));
		}
		source.appendChild(new MonadDate().toXML(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public SupplyGeneration getChild(UriPathElement uriId)
			throws ProgrammerException, UserException {
		SupplyGeneration supplyGeneration = (SupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SupplyGeneration supplyGeneration where supplyGeneration.supply = :supply and supplyGeneration.id = :supplyGenerationId")
				.setEntity("supply", supply).setLong("supplyGenerationId",
						Long.parseLong(uriId.toString())).uniqueResult();
		if (supplyGeneration == null) {
			throw UserException.newNotFound();
		}
		return supplyGeneration;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		return doc.createElement("supply-generations");
	}

	public Node getXML(XmlTree tree, Document doc) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}
}