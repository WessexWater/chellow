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

import net.sf.chellow.billing.Provider;
import net.sf.chellow.monad.Debug;
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
	static public Mtc getMtc(Provider dso, MtcCode mtcCode)
			throws HttpException {
		return findMtc(dso, mtcCode, true);
	}

	static public Mtc findMtc(Provider dso, MtcCode mtcCode,
			boolean throwException) throws HttpException {
		dso = mtcCode.hasDso() ? dso : null;
		Mtc mtc = null;
		if (dso == null) {
			mtc = (Mtc) Hiber
					.session()
					.createQuery(
							"from Mtc as mtc where mtc.dso is null and mtc.code.integer = :mtcCode")
					.setInteger("mtcCode", mtcCode.getInteger()).uniqueResult();
		} else {
			mtc = (Mtc) Hiber
					.session()
					.createQuery(
							"from Mtc as mtc where mtc.dso = :dso and mtc.code.integer = :mtcCode")
					.setEntity("dso", dso).setInteger("mtcCode",
							mtcCode.getInteger()).uniqueResult();
		}
		if (throwException && mtc == null) {
			throw new UserException("There isn't a meter timeswitch with DSO '"
					+ (dso == null ? dso : dso.getDsoCode())
					+ "' and Meter Timeswitch Code '" + mtcCode + "'");
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

	static public Mtc insertMtc(Provider dso, MtcCode code, String description,
			boolean hasRelatedMetering, Boolean hasComms, Boolean isHh,
			MeterType meterType, MtcPaymentType paymentType, Integer tprCount,
			Date from, Date to) throws HttpException {

		Mtc mtc = new Mtc(dso, code, description, hasRelatedMetering, hasComms,
				isHh, meterType, paymentType, tprCount, from, to);
		Hiber.session().save(mtc);
		Hiber.flush();
		return mtc;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add MTCs.");
		Mdd mdd = new Mdd(sc, "MeterTimeswitchClass", new String[] {
				"Meter Timeswitch Class Id",
				"Effective From Settlement Date {MTC}",
				"Effective To Settlement Date {MTC}",
				"Meter Timeswitch Class Description",
				"MTC Common Code Indicator",
				"MTC Related Metering System Indicator", "MTC Meter Type Id",
				"MTC Payment Type Id", "MTC Communication Indicator",
				"MTC Type Indicator", "MTC TPR Count" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			if (values[4].equals("T")) {
				MtcCode code = new MtcCode(values[0]);
				String description = values[3];
				Boolean hasComms = null;
				if (values[8].equals("Y")) {
					hasComms = Boolean.TRUE;
				} else if (values[8].equals("N")) {
					hasComms = Boolean.FALSE;
				}
				Boolean isHh = null;
				Integer tprCount = null;
				if (values[9].equals("H")) {
					isHh = Boolean.TRUE;
				} else if (values[9].equals("N")) {
					isHh = Boolean.FALSE;
					tprCount = Integer.parseInt(values[10]);
				}
				Date validFrom = mdd.toDate(values[1]);
				Date validTo = mdd.toDate(values[2]);
				MeterType meterType = MeterType.getMtcMeterType(values[6]);
				MtcPaymentType paymentType = MtcPaymentType
						.getMtcPaymentType(values[7]);
				boolean hasRelatedMetering = values[5].equals("T");
				Mtc mtc = Mtc.insertMtc(null, code, description,
						hasRelatedMetering, hasComms, isHh, meterType,
						paymentType, tprCount, validFrom, validTo);
				Hiber.session().save(mtc);
				Hiber.close();
			}
		}
		mdd = new Mdd(sc, "MtcInPesArea", new String[] {
				"Meter Timeswitch Class Id",
				"Effective From Settlement Date {MTC}",
				"Market Participant Id",
				"Effective From Settlement Date {MTCPA}",
				"Effective To Settlement Date {MTCPA}",
				"Meter Timeswitch Class Description", "MTC Meter Type Id",
				"MTC Payment Type Id", "MTC Communication Indicator",
				"MTC Type Indicator", "MTC TPR Count" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			MtcCode code = new MtcCode(values[0]);
			if (code.hasDso()) {
				Provider dso = Provider.getProvider(values[2],
						MarketRole.DISTRIBUTOR);
				String description = values[5];
				Boolean hasComms = null;
				if (values[8].equals("Y")) {
					hasComms = Boolean.TRUE;
				} else if (values[8].equals("N")) {
					hasComms = Boolean.FALSE;
				}
				Boolean isHh = null;
				Integer tprCount = null;
				if (values[9].equals("H")) {
					isHh = Boolean.TRUE;
				} else if (values[9].equals("N")) {
					isHh = Boolean.FALSE;
					tprCount = Integer.parseInt(values[10]);
				}
				Date validFrom = mdd.toDate(values[3]);
				Date validTo = mdd.toDate(values[4]);
				MeterType meterType = MeterType.getMtcMeterType(values[6]);
				MtcPaymentType paymentType = MtcPaymentType
						.getMtcPaymentType(values[7]);
				Mtc mtc = Mtc.insertMtc(dso, code, description, false,
						hasComms, isHh, meterType, paymentType, tprCount,
						validFrom, validTo);
				Hiber.session().save(mtc);
				Hiber.close();
			}
		}
		Debug.print("Starting to add MTCs.");
	}

	private Provider dso;

	private MtcCode code;

	private String description;

	private boolean hasRelatedMetering;
	private Boolean hasComms;
	private Boolean isHh;
	private MeterType meterType;
	private MtcPaymentType paymentType;
	private Integer tprCount;
	private Date validFrom;
	private Date validTo;

	public Mtc() {
	}

	public Mtc(Provider dso, MtcCode code, String description,
			boolean hasRelatedMetering, Boolean hasComms, Boolean isHh,
			MeterType meterType, MtcPaymentType paymentType, Integer tprCount,
			Date validFrom, Date validTo) throws HttpException {
		setDso(dso);
		setCode(code);
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

	void setDso(Provider dso) {
		this.dso = dso;
	}

	public Provider getDso() {
		return dso;
	}

	public MtcCode getCode() {
		return code;
	}

	void setCode(MtcCode code) {
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

	public MtcPaymentType getPaymentType() {
		return paymentType;
	}

	void setPaymentType(MtcPaymentType paymentType) {
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
		return code + " - " + description + " (DSO "
				+ (dso == null ? null : dso.getDsoCode()) + ")";
	}

	public Node toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "mtc");

		element.setAttributeNode(code.toXml(doc));
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

		source.appendChild(toXml(doc, new XmlTree("dso").put("meterType").put(
				"paymentType")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub
	}
}