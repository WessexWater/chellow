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

import java.net.URI;
import java.text.DecimalFormat;
import java.util.Date;

import net.sf.chellow.billing.Dno;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Mtc extends PersistentEntity {
	static public Mtc getMtc(Dno dno, String code)
			throws HttpException {
		Mtc mtc = findMtc(dno, code);
		if (mtc == null) {
			throw new UserException("There isn't a meter timeswitch with DNO '"
					+ (dno == null ? dno : dno.getCode())
					+ "' and Meter Timeswitch Code '" + code + "'");
		}
		return mtc;
	}
	
	static public boolean hasDno(int code) {
		return !((code > 499 && code < 510) || (code > 799 && code < 1000));
	}

	static public Mtc findMtc(Dno dno, String codeStr) throws HttpException {
		int code = Integer.parseInt(codeStr);
		dno = hasDno(code) ? dno : null;
		Mtc mtc = null;
		if (dno == null) {
			mtc = (Mtc) Hiber
					.session()
					.createQuery(
							"from Mtc as mtc where mtc.dno is null and mtc.code = :mtcCode")
					.setInteger("mtcCode", code).uniqueResult();
		} else {
			mtc = (Mtc) Hiber
					.session()
					.createQuery(
							"from Mtc as mtc where mtc.dno = :dno and mtc.code = :mtcCode")
					.setEntity("dno", dno).setInteger("mtcCode", code).uniqueResult();
		}
		return mtc;
	}

	static public Mtc getMtc(Long id) throws HttpException {
		Mtc mtc = (Mtc) Hiber.session().get(Mtc.class, id);
		if (mtc == null) {
			throw new UserException(
					"There is no meter timeswitch with that id.");
		}
		return mtc;
	}

	static public Mtc insertMtc(Dno dno, String code, String description,
			boolean hasRelatedMetering, Boolean hasComms, Boolean isHh,
			MeterType meterType, MeterPaymentType paymentType, Integer tprCount,
			Date from, Date to) throws HttpException {

		Mtc mtc = new Mtc(dno, code, description, hasRelatedMetering, hasComms,
				isHh, meterType, paymentType, tprCount, from, to);
		Hiber.session().save(mtc);
		Hiber.flush();
		return mtc;
	}

	private Dno dno;

	private int code;

	private String description;

	private boolean hasRelatedMetering;
	private Boolean hasComms;
	private Boolean isHh;
	private MeterType meterType;
	private MeterPaymentType paymentType;
	private Integer tprCount;
	private Date validFrom;
	private Date validTo;

	public Mtc() {
	}

	public Mtc(Dno dno, String code, String description,
			boolean hasRelatedMetering, Boolean hasComms, Boolean isHh,
			MeterType meterType, MeterPaymentType paymentType, Integer tprCount,
			Date validFrom, Date validTo) throws HttpException {
		setDno(dno);
		setCode(Integer.parseInt(code));
		setDescription(description);
		setHasRelatedMetering(hasRelatedMetering);
		setHasComms(hasComms);
		setIsHh(isHh);
		setMeterType(meterType);
		setPaymentType(paymentType);
		setTprCount(tprCount);
		setValidFrom(validFrom);
		setValidTo(validTo);
	}

	void setDno(Dno dno) {
		this.dno = dno;
	}

	public Dno getDno() {
		return dno;
	}

	public int getCode() {
		return code;
	}

	void setCode(int code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public boolean getHasRelatedMetering() {
		return hasRelatedMetering;
	}

	void setHasRelatedMetering(boolean hasRelatedMetering) {
		this.hasRelatedMetering = hasRelatedMetering;
	}

	public Boolean getHasComms() {
		return hasComms;
	}

	void setHasComms(Boolean hasComms) {
		this.hasComms = hasComms;
	}

	public Boolean getIsHh() {
		return isHh;
	}

	void setIsHh(Boolean isHh) {
		this.isHh = isHh;
	}

	public MeterType getMeterType() {
		return meterType;
	}

	void setMeterType(MeterType meterType) {
		this.meterType = meterType;
	}

	public MeterPaymentType getPaymentType() {
		return paymentType;
	}

	void setPaymentType(MeterPaymentType paymentType) {
		this.paymentType = paymentType;
	}

	public Integer getTprCount() {
		return tprCount;
	}

	void setTprCount(Integer tprCount) {
		this.tprCount = tprCount;
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
	
	public String toString() {
		DecimalFormat mtcFormat = new DecimalFormat("000");
		return mtcFormat.format(code);		
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "mtc");
		element.setAttribute("code", toString());
		element.setAttribute("description", description);
		element.setAttribute("has-related-metering", Boolean
				.toString(hasRelatedMetering));
		if (hasComms != null) {
			element.setAttribute("has-comms", hasComms.toString());
		}
		if (isHh != null) {
			element.setAttribute("is-hh", isHh.toString());
		}
		if (tprCount != null) {
			element.setAttribute("tpr-count", String.valueOf(tprCount));
		}
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

	public MonadUri getEditUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("dno").put("meterType").put(
				"paymentType")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
