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

import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;

import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class ProfileClass extends PersistentEntity {
	static public ProfileClass getProfileClass(Long id)
			throws ProgrammerException, UserException {
		ProfileClass profileClass = (ProfileClass) Hiber.session().get(
				ProfileClass.class, id);
		if (profileClass == null) {
			throw UserException
					.newOk("There is no profile class with that id.");
		}
		return profileClass;
	}
	
	static public ProfileClass getProfileClass(int code) throws ProgrammerException, UserException {
		return getProfileClass(new ProfileClassCode(code));
	}

	static public ProfileClass getProfileClass(ProfileClassCode code)
			throws ProgrammerException, UserException {
		ProfileClass profileClass = findProfileClass(code);
		if (profileClass == null) {
			throw UserException
					.newOk("There is no profile class with that code.");
		}
		return profileClass;
	}

	static public ProfileClass findProfileClass(ProfileClassCode code) {
		return findProfileClass(code.getInteger());
	}

	static public ProfileClass findProfileClass(int code) {
		return (ProfileClass) Hiber
				.session()
				.createQuery(
						"from ProfileClass as profileClass where profileClass.code.integer = :code")
				.setInteger("code", code).uniqueResult();
	}
/*
	@SuppressWarnings("unchecked")
	static public List<ProfileClass> findAll() throws ProgrammerException {
		return (List<ProfileClass>) Hiber
				.session()
				.createQuery(
						"from ProfileClass profileClass order by profileClass.code.integer")
				.list();
	}
*/
	public static ProfileClass insertProfileClass(int code,
			String description) throws ProgrammerException, UserException {

		ProfileClass profileClass = null;
		try {
			profileClass = new ProfileClass(new ProfileClassCode(code),
					description);
			Hiber.session().save(profileClass);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw UserException
						.newOk("A profile class with this code already exists.");
			} else {
				throw new ProgrammerException(e);
			}
		}
		return profileClass;
	}

	private ProfileClassCode code;

	private String description;

	public ProfileClass() {
		setTypeName("profile-class");
	}

	public ProfileClass(ProfileClassCode code, String description) {
		this(null, code, description);
	}

	public ProfileClass(String label, ProfileClassCode code, String description) {
		this();
		setLabel(label);
		this.code = code;
		this.description = description;
	}

	void setCode(ProfileClassCode code) {
		code.setLabel("code");
		this.code = code;
	}

	public ProfileClassCode getCode() {
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
		return getCode() + " - " + getDescription();
	}

	public Node toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);

		element.setAttributeNode((Attr) code.toXML(doc));
		element.setAttributeNode(MonadString.toXml(doc, "description",
				description));
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXML(doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}
}