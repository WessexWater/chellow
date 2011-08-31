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

import java.net.URI;

import net.sf.chellow.billing.Provider;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Participant extends PersistentEntity {
	static public Participant getParticipant(Long id) throws HttpException {
		Participant participant = (Participant) Hiber.session().get(
				Participant.class, id);
		if (participant == null) {
			throw new NotFoundException("There isn't a participant with id "
					+ id + ".");
		}
		return participant;
	}

	static public Participant getParticipant(String code) throws HttpException {
		Participant participant = (Participant) Hiber.session().createQuery(
				"from Participant participant where participant.code = :code")
				.setString("code", code).uniqueResult();
		if (participant == null) {
			throw new NotFoundException("There isn't a participant with code '"
					+ code + "'.");
		}
		return participant;
	}


	private String code;
	private String name;

	public Participant() {

	}

	public Participant(String code, String name) {
		this.code = code;
		this.name = name;
	}

	public String getCode() {
		return code;
	}

	public void setCode(String code) {
		this.code = code;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public MonadUri getEditUri() throws HttpException {
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
		Element source = (Element) doc.getFirstChild();

		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "participant");

		element.setAttribute("code", code);
		element.setAttribute("name", name);
		return element;
	}

	public Provider getProvider(char roleCode) {
		return (Provider) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.participant = :participant and provider.role.code = :roleCode")
				.setEntity("participant", this).setCharacter("roleCode",
						roleCode).uniqueResult();
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
