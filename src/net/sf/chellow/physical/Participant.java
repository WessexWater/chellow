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
package net.sf.chellow.physical;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;

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
	
	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("participant");
		
		element.setAttribute("id", getId().toString());
		element.setAttribute("code", code);
        element.setAttribute("name", name);
		return element;
	}
}
