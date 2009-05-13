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

public class MeterPaymentType extends PersistentEntity {
	static public MeterPaymentType getMtcPaymentType(String code)
			throws HttpException {
		MeterPaymentType type = findMtcPaymentType(code);
		if (type == null) {
			throw new NotFoundException();
		}
		return type;
	}

	static public MeterPaymentType findMtcPaymentType(String code)
			throws HttpException {
		return (MeterPaymentType) Hiber
				.session()
				.createQuery(
						"from MeterPaymentType type where type.code = :paymentCode")
				.setString("paymentCode", code).uniqueResult();
	}

	static public MeterPaymentType getMeterPaymentType(Long id)
			throws HttpException {
		MeterPaymentType type = (MeterPaymentType) Hiber.session().get(
				MeterPaymentType.class, id);
		if (type == null) {
			throw new UserException(
					"There is no meter timeswitch class payment type with that id.");
		}
		return type;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add MTC Payment Types.");
		Mdd mdd = new Mdd(sc, "MtcPaymentType", new String[] {
				"MTC Payment Type Id", "MTC Payment Type Description",
				"Effective From Settlement Date {MPT}",
				"Effective To Settlement Date {MPT}" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Hiber.session().save(
					new MeterPaymentType(values[0], values[1], mdd
							.toDate(values[2]), mdd.toDate(values[3])));
			Hiber.close();
		}
		Debug.print("Finished adding MTC Payment Types.");
	}

	private String code;

	private String description;

	private Date validFrom;
	private Date validTo;

	public MeterPaymentType() {
	}

	public MeterPaymentType(String code, String description, Date validFrom,
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

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "meter-payment-type");

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
