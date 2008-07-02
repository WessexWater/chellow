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
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class MeterType extends PersistentEntity {
	static public MeterType getMtcMeterType(String code) throws HttpException {
		MeterType type = findMeterType(code);
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public MeterType findMeterType(String code) throws HttpException {
		return (MeterType) Hiber
				.session()
				.createQuery(
						"from MeterType meterType where meterType.code = :meterTypeCode")
				.setString("meterTypeCode", code).uniqueResult();
	}

	static public MeterType getMeterType(Long id) throws HttpException {
		MeterType type = (MeterType) Hiber.session().get(MeterType.class, id);
		if (type == null) {
			throw new UserException(
					"There is no meter timeswitch class meter type with that id.");
		}
		return type;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = MeterType.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource("net/sf/chellow/physical/MtcMeterType.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 4
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
			SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy",
					Locale.UK);
			dateFormat.setCalendar(new GregorianCalendar(TimeZone
					.getTimeZone("GMT"), Locale.UK));
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				String toDateStr = values[3];
				Date toDate = toDateStr.length() == 0 ? null : dateFormat
						.parse(toDateStr);
				Hiber.session().save(
						new MeterType(values[0], values[1], dateFormat
								.parse(values[2]), toDate));
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

	private Date validFrom;
	private Date validTo;

	public MeterType() {
	}

	public MeterType(String code, String description, Date validFrom,
			Date validTo) throws HttpException {
		setCode(code);
		setDescription(description);
		setValidFrom(validFrom);
		setValidTo(validTo);
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

	public Date getValidFrom() {
		return validFrom;
	}

	void setValidFrom(Date from) {
		this.validFrom = from;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date to) {
		this.validTo = to;
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("meter-type");
		Element element = (Element) super.toXml(doc);

		element.setAttribute("code", code);
		element.setAttribute("description", description);
		MonadDate fromDate = new MonadDate(validFrom);
		fromDate.setLabel("from");
		element.appendChild(fromDate.toXml(doc));
		if (validTo != null) {
			MonadDate toDate = new MonadDate(validTo);
			toDate.setLabel("to");
			element.appendChild(toDate.toXml(doc));
		}
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}
}