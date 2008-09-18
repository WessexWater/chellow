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
import java.text.DateFormat;
import java.text.ParseException;
import java.util.Date;
import java.util.Locale;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class SscPc extends PersistentEntity {
	static public Pc getProfileClass(Long id) throws InternalException,
			HttpException {
		Pc profileClass = (Pc) Hiber.session().get(Pc.class, id);
		if (profileClass == null) {
			throw new UserException("There is no profile class with that id.");
		}
		return profileClass;
	}
/*
	static public Pc getProfileClass(int code) throws InternalException,
			HttpException {
		return getProfileClass(new PcCode(code));
	}
*/
/*
	static public Pc getProfileClass(PcCode code) throws InternalException,
			HttpException {
		Pc profileClass = findProfileClass(code);
		if (profileClass == null) {
			throw new UserException("There is no profile class with that code.");
		}
		return profileClass;
	}
	*/
/*
	static public Pc findProfileClass(PcCode code) {
		return findProfileClass(code.getInteger());
	}
	*/
	/*
	static public Pc findProfileClass(int code) {
		return (Pc) Hiber
				.session()
				.createQuery(
						"from Pc pc where pc.code = :code")
				.setInteger("code", code).uniqueResult();
	}
*/
	/*
	 * @SuppressWarnings("unchecked") static public List<ProfileClass>
	 * findAll() throws ProgrammerException { return (List<ProfileClass>) Hiber
	 * .session() .createQuery( "from ProfileClass profileClass order by
	 * profileClass.code.integer") .list(); }
	 */
	/*
	public static Pc insertProfileClass(int code, String description)
			throws InternalException, HttpException {

		Pc profileClass = null;
		try {
			profileClass = new Pc(new PcCode(code), description);
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
*/
	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = SscPc.class.getClassLoader();
			CSVParser parser = new CSVParser(
					new InputStreamReader(
							classLoader
									.getResource(
											"net/sf/chellow/physical/ValidStandardSettlementConfigurationProfileClass.csv")
									.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();
			if (titles.length < 4
					|| !titles[0].trim().equals("Profile Class Id")
					|| !titles[1].trim().equals(
							"Standard Settlement Configuration Id")
					|| !titles[2].trim().equals(
							"Effective From Settlement Date {VSCPC}")
					|| !titles[3].trim().equals(
							"Effective To Settlement Date {VSCPC}")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Profile Class Id, Standard Settlement Configuration Id, Effective From Settlement Date {VSCPC}, Effective To Settlement Date {VSCPC}.");
			}
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Hiber.session()
						.save(
								new SscPc(Ssc.getSsc(values[0]), Pc
										.getPc(values[1]),
										dateFormat.parse(values[2]), dateFormat
												.parse(values[3])));
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (NumberFormatException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private Ssc ssc;

	private Pc pc;

	private Date from;
	private Date to;

	public SscPc() {
	}

	public SscPc(Ssc ssc, Pc pc, Date from, Date to) {
		setSsc(ssc);
		setPc(pc);
		setFrom(from);
		setTo(to);
	}

	public Ssc getSsc() {
		return ssc;
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public Pc getPc() {
		return pc;
	}

	void setPc(Pc pc) {
		this.pc = pc;
	}

	public Date getFrom() {
		return from;
	}

	void setFrom(Date from) {
		this.from = from;
	}

	public Date getTo() {
		return to;
	}

	void setTo(Date to) {
		this.to = to;
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "ssc-pc");

		MonadDate fromDate = new MonadDate(from);
		fromDate.setLabel("from");
		element.appendChild(fromDate.toXml(doc));

		MonadDate toDate = new MonadDate(to);
		fromDate.setLabel("to");

		element.appendChild(toDate.toXml(doc));
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