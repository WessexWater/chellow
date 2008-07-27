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

import java.util.Date;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
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

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Meter Types.");
		Mdd mdd = new Mdd(sc, "MtcMeterType", new String[] {
				"MTC Meter Type Id", "MTC Meter Type Description",
				"Effective From Settlement Date {MMT}",
				"Effective To Settlement Date {MMT}" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Hiber.session().save(
					new MeterType(values[0], values[1], mdd.toDate(values[2]),
							mdd.toDate(values[3])));
			Hiber.close();
		}
		Debug.print("Finished adding Meter Types.");
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

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "meter-type");

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