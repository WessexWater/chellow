/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
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

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class MarketRole extends PersistentEntity {
	static public final char HHDC = 'C';
	static public final char MOP = 'M';
	static public final char DISTRIBUTOR = 'R';
	static public final char SUPPLIER = 'X';
	static public final char NON_CORE_ROLE = 'Z';

	static public MarketRole getMarketRole(Long id) throws HttpException {
		MarketRole marketRole = (MarketRole) Hiber.session().get(
				MarketRole.class, id);
		if (marketRole == null) {
			throw new NotFoundException();
		}
		return marketRole;
	}
	
	static public MarketRole getMarketRole(String code) throws HttpException {
		String trimmed = code.trim();
		if (trimmed.length() > 1) {
			throw new UserException("A market role code must be a single character.");
		}
		return getMarketRole(trimmed.charAt(0));
	}

	static public MarketRole getMarketRole(char code) throws HttpException {
		MarketRole marketRole = (MarketRole) Hiber.session().createQuery(
				"from MarketRole role where role.code = :code").setCharacter(
				"code", code).uniqueResult();
		if (marketRole == null) {
			throw new NotFoundException();
		}
		return marketRole;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Market Roles.");
		Mdd mdd = new Mdd(sc, "MarketRole", new String[] {
				"Market Participant Role Code", "Market Role Description" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			MarketRole role = new MarketRole(values[0].charAt(0), values[1]);
			Hiber.session().save(role);
			Hiber.close();
		}
		Debug.print("Finished adding Market Roles.");
	}

	private char code;
	private String description;

	public MarketRole() {

	}

	public MarketRole(char code, String description) {
		this.code = code;
		this.description = description;
	}

	public char getCode() {
		return code;
	}

	public void setCode(char code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
	}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

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
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "market-role");

		element.setAttribute("code", String.valueOf(code));
		element.setAttribute("description", description);
		return element;
	}
}
