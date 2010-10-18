/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
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

package net.sf.chellow.physical;

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Supplies extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("supplies");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Supplies() {
	}

	public MonadUri getUrlPath() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUriId()).append("/");
	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	@SuppressWarnings("unchecked")
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		List<SupplyGeneration> generations = new ArrayList<SupplyGeneration>();

		if (inv.hasParameter("search-pattern")) {
			String pattern = inv.getString("search-pattern");
			pattern = pattern.trim();
			String reducedPattern = pattern.replace(" ", "");
			Long lastSupply = null;
			for (Object[] supplyGenerationRes : (List<Object[]>) Hiber
					.session()
					.createQuery(
							"select distinct mpan.supplyGeneration, mpan.supplyGeneration.startDate, mpan.supplyGeneration.supply from Mpan mpan where (lower(mpan.core.dso.code || mpan.core.uniquePart || mpan.core.checkDigit) like lower(:reducedPattern)) or lower(mpan.supplierAccount) like lower(:pattern) or (mpan.supplyGeneration.hhdcAccount is not null and lower(mpan.supplyGeneration.hhdcAccount) like lower(:pattern)) or (mpan.supplyGeneration.mopAccount is not null and lower(mpan.supplyGeneration.mopAccount) like lower(:pattern)) or lower(mpan.supplyGeneration.meterSerialNumber) like lower(:pattern) order by mpan.supplyGeneration.supply.id, mpan.supplyGeneration.startDate desc")
					.setString("pattern", "%" + pattern + "%").setString(
							"reducedPattern", "%" + reducedPattern + "%")
					.setMaxResults(50).list()) {
				SupplyGeneration supplyGeneration = (SupplyGeneration) supplyGenerationRes[0];
				Long supplyId = supplyGeneration.getSupply().getId();
				if (supplyId == lastSupply) {
					continue;
				}
				lastSupply = supplyId;
				generations.add(supplyGeneration);
			}

			if (generations.size() == 1) {
				inv.sendTemporaryRedirect("/supplies/"
						+ generations.get(0).getSupply().getId() + "/");
			} else {
				for (SupplyGeneration generation : generations) {
					source.appendChild(generation.toXml(doc, new XmlTree(
							"supply").put("hhdcContract").put("pc").put("mtc")
							.put(
									"mpans",
									new XmlTree("llfc").put("core").put(
											"supplierContract"))));
				}
			}
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public Supply getChild(UriPathElement uriId) throws HttpException {
		return Supply.getSupply(Long.parseLong(uriId.getString()));
	}

	public MonadUri getUri() throws HttpException {
		return Chellow.ROOT_URI.resolve(getUriId());
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("supplies");
		return element;
	}
}
