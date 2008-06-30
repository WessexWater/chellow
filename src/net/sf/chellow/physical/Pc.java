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

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;

import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class Pc extends PersistentEntity {
	static public Pc getProfileClass(Long id)
			throws InternalException, HttpException {
		Pc profileClass = (Pc) Hiber.session().get(
				Pc.class, id);
		if (profileClass == null) {
			throw new UserException("There is no profile class with that id.");
		}
		return profileClass;
	}

	static public Pc getProfileClass(int code)
			throws InternalException, HttpException {
		return getPc(new PcCode(code));
	}

	static public Pc getPc(PcCode code)
			throws InternalException, HttpException {
		Pc profileClass = findProfileClass(code);
		if (profileClass == null) {
			throw new UserException("There is no profile class with that code.");
		}
		return profileClass;
	}

	static public Pc findProfileClass(PcCode code) {
		return findProfileClass(code.getInteger());
	}

	static public Pc findProfileClass(int code) {
		return (Pc) Hiber
				.session()
				.createQuery(
						"from ProfileClass as profileClass where profileClass.code.integer = :code")
				.setInteger("code", code).uniqueResult();
	}

	/*
	 * @SuppressWarnings("unchecked") static public List<ProfileClass>
	 * findAll() throws ProgrammerException { return (List<ProfileClass>) Hiber
	 * .session() .createQuery( "from ProfileClass profileClass order by
	 * profileClass.code.integer") .list(); }
	 */
	public static Pc insertProfileClass(int code, String description)
			throws InternalException, HttpException {

		Pc profileClass = null;
		try {
			profileClass = new Pc(new PcCode(code),
					description);
			Hiber.session().save(profileClass);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw new UserException(
						"A profile class with this code already exists.");
			} else {
				throw new InternalException(e);
			}
		}
		return profileClass;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Participant.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource("net/sf/chellow/physical/ProfileClass.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length < 3
					|| !titles[0].trim().equals("Profile Class Id")
					|| !titles[1].trim().equals(
							"Effective From Settlement Date {PCLA}")
					|| !titles[2].trim().equals("Profile Class Description")
					|| !titles[2].trim().equals(
							"Switched Load Profile Class Ind")
					|| !titles[2].trim().equals(
							"Effective To Settlement Date {PCLA}")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Profile Class Id, Effective From Settlement Date {PCLA}, Profile Class Description, Switched Load Profile Class Ind, Effective To Settlement Date {PCLA}.");
			}
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Hiber.session().save(
						new Pc(new PcCode(Integer
								.parseInt(values[0])), values[1]));
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	private PcCode code;

	private String description;

	public Pc() {
	}

	public Pc(PcCode code, String description) {
		this(null, code, description);
	}

	public Pc(String label, PcCode code, String description) {
		this();
		setLabel(label);
		this.code = code;
		this.description = description;
	}

	void setCode(PcCode code) {
		code.setLabel("code");
		this.code = code;
	}

	public PcCode getCode() {
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

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("profile-class");
		Element element = (Element) super.toXml(doc);

		element.setAttributeNode(code.toXml(doc));
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