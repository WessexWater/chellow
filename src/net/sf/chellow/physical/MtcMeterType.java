/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class MtcMeterType extends PersistentEntity {
	static public MtcMeterType getMtcMeterType(String code)
			throws HttpException {
		MtcMeterType type = findMtcMeterType(code);
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public MtcMeterType findMtcMeterType(String code)
			throws HttpException {
		return (MtcMeterType) Hiber
				.session()
				.createQuery(
						"from MtcMeterType meterType where meterType.code = :meterTypeCode")
				.setString("meterTypeCode", code).uniqueResult();
	}

	static public MtcMeterType getMtcMeterType(Long id) throws HttpException {
		MtcMeterType type = (MtcMeterType) Hiber.session().get(
				MtcMeterType.class, id);
		if (type == null) {
			throw new UserException(
					"There is no meter timeswitch class meter type with that id.");
		}
		return type;
	}

	static public Mtc insertMeterTimeswitch(Dso dso, String mtcCode,
			String description, boolean isUnmetered) throws InternalException,
			HttpException {
		return insertMtc(dso, new MtcCode(mtcCode), description, isUnmetered);
	}

	static public Mtc insertMtc(Dso dso, MtcCode mtcCode, String description,
			boolean isUnmetered) throws HttpException {

		Mtc mtc = null;
		try {
			mtc = new Mtc(dso, mtcCode, description, isUnmetered);
			Hiber.session().save(mtc);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw new UserException("A site with this code already exists.");
			} else {
				throw new InternalException(e);
			}
		}
		return mtc;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = MtcMeterType.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource("net/sf/chellow/physical/MtcMeterType.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 11
					|| !titles[0].trim().equals("MTC Meter Type Id")
					|| !titles[1].trim().equals("MTC Meter Type Description")
					|| !titles[2].trim().equals(
							"Effective From Settlement Date {MMT}")
					|| !titles[3].trim().equals(
							"Effective To Settlement Date {MMT}")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "MTC Meter Type Id, MTC Meter Type Description, Effective From Settlement Date {MMT}, Effective To Settlement Date {MMT}.");
			}
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Hiber.session()
						.save(
								new MtcMeterType(values[0], values[1],
										dateFormat.parse(values[2]), dateFormat
												.parse(values[3])));
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private String code;

	private String description;

	private Date from;
	private Date to;

	// private Set<LineLossFactor> lineLossFactors;

	// private Set<Ssc> registers;

	public MtcMeterType() {
	}

	public MtcMeterType(String code, String description, Date from, Date to)
			throws HttpException {

		setCode(code);
		setDescription(description);
		setFrom(from);
		setTo(to);
	}

	public String getCode() {
		return code;
	}

	void setCode(String code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
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

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("mtc-meter-type");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		MonadDate fromDate = new MonadDate(from);
		fromDate.setLabel("from");
		element.appendChild(fromDate.toXml(doc));
		MonadDate toDate = new MonadDate(to);
		toDate.setLabel("to");
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

		source.appendChild(toXml(doc, new XmlTree("dso")));
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
	/*
	 * public void insertRegister(Ssc.Units units, String tprString) throws
	 * ProgrammerException, UserException { Set<Tpr> tprs = new HashSet<Tpr>();
	 * for (String tprCode : tprString.split(",")) { Tpr tpr =
	 * Tpr.getTpr(tprCode); tprs.add(tpr); } registers.add(new Ssc(this, units,
	 * tprs)); }
	 */
}