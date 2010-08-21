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

import java.text.DecimalFormat;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Pc extends PersistentEntity {
	static public Pc getPc(Long id) throws HttpException {
		Pc pc = (Pc) Hiber.session().get(Pc.class, id);
		if (pc == null) {
			throw new UserException("There is no profile class with that id.");
		}
		return pc;
	}

	static public Pc getPc(String code) throws HttpException {
		Pc profileClass = findPc(Integer.parseInt(code));
		if (profileClass == null) {
			throw new UserException("There is no profile class with that code.");
		}
		return profileClass;
	}

	static public Pc findPc(int code) {
		return (Pc) Hiber.session().createQuery(
				"from Pc pc where pc.code = :code").setInteger("code",
				code).uniqueResult();
	}

	private int code;

	private String description;

	public Pc() {
	}

	public Pc(String code, String description) {
		this(null, code, description);
	}

	public Pc(String label, String code, String description) {
		setLabel(label);
		this.code = Integer.parseInt(code);
		this.description = description;
	}

	void setCode(int code) {
		this.code = code;
	}

	public int getCode() {
		return code;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public String getDescription() {
		return description;
	}

	public void update(String description) {
		setDescription(description);
		Hiber.flush();
	}
	
	public String toString() {
		DecimalFormat pcFormat = new DecimalFormat("00");
		return pcFormat.format(code);
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "pc");
		

		element.setAttribute("code", toString());
		element.setAttribute("description", description);
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
}
