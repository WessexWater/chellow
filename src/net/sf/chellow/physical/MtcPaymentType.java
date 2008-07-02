/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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

public class MtcPaymentType extends PersistentEntity {
	static public MtcPaymentType getMtcPaymentType(String code)
			throws HttpException {
		MtcPaymentType type = findMtcPaymentType(code);
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public MtcPaymentType findMtcPaymentType(String code)
			throws HttpException {
		return (MtcPaymentType) Hiber
				.session()
				.createQuery(
						"from MtcPaymentType meterType where meterType.code = :meterPaymentCode")
				.setString("meterPaymentCode", code).uniqueResult();
	}

	static public MtcPaymentType getMtcPaymentType(Long id)
			throws HttpException {
		MtcPaymentType type = (MtcPaymentType) Hiber.session().get(
				MtcPaymentType.class, id);
		if (type == null) {
			throw new UserException(
					"There is no meter timeswitch class payment type with that id.");
		}
		return type;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = MeterType.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource("net/sf/chellow/physical/MtcPaymentType.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 4
					|| !titles[0].trim().equals("MTC Payment Type Id")
					|| !titles[1].trim().equals("MTC Payment Type Description")
					|| !titles[2].trim().equals(
							"Effective From Settlement Date {MPT}")
					|| !titles[3].trim().equals(
							"Effective To Settlement Date {MPT}")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "MTC Payment Type Id, MTC Payment Type Description, Effective From Settlement Date {MPT}, Effective To Settlement Date {MPT}.");
			}
			SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy",
					Locale.UK);
			dateFormat.setCalendar(new GregorianCalendar(TimeZone
					.getTimeZone("GMT"), Locale.UK));
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				String validToStr = values[3];
				Date validTo = validToStr.length() == 0 ? null : dateFormat
						.parse(validToStr);
				Hiber.session().save(
						new MtcPaymentType(values[0], values[1], dateFormat
								.parse(values[2]), validTo));
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

	public MtcPaymentType() {
	}

	public MtcPaymentType(String code, String description, Date validFrom,
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

	void setValidFrom(Date validFrom) {
		this.validFrom = validFrom;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date validTo) {
		this.validTo = validTo;
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("meter-payment-type");
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

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
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