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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
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

import com.Ostermiller.util.CSVParser;

public class Mtc extends PersistentEntity {
	static public Mtc getMtc(Dso dso, MtcCode mtcCode)
			throws HttpException {
		return findMtc(dso, mtcCode, true);
	}

	static public Mtc findMtc(Dso dso, MtcCode mtcCode, boolean throwException)
			throws HttpException {
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
					+ (dso == null ? dso : dso.getCode())
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

	static public Mtc insertMtc(Dso dso, String code, String description,
			boolean hasRelatedMetering, Boolean hasComms, Boolean isHh,
			MtcMeterType meterType, MtcPaymentType paymentType, int tprCount,
			Date from, Date to) throws HttpException {

		Mtc mtc = new Mtc(dso, new MtcCode(code), description,
				hasRelatedMetering, hasComms, isHh, meterType, paymentType,
				tprCount, from, to);
		Hiber.session().save(mtc);
		Hiber.flush();
		return mtc;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Mtc.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource(
							"net/sf/chellow/physical/MeterTimeswitchClass.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 11
					|| !titles[0].trim().equals("Meter Timeswitch Class Id")
					|| !titles[1].trim().equals(
							"Effective From Settlement Date {MTC}")
					|| !titles[2].trim().equals(
							"Effective To Settlement Date {MTC}")
					|| !titles[3].trim().equals(
							"Meter Timeswitch Class Description")
					|| !titles[4].trim().equals("MTC Common Code Indicator")
					|| !titles[5].trim().equals(
							"MTC Related Metering System Indicator")
					|| !titles[6].trim().equals("MTC Meter Type Id")
					|| !titles[7].trim().equals("MTC Payment Type Id")
					|| !titles[8].trim().equals("MTC Communication Indicator")
					|| !titles[9].trim().equals("MTC Type Indicator")
					|| !titles[10].trim().equals("MTC TPR Count")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Meter Timeswitch Class Id, Effective From Settlement Date {MTC}, Effective To Settlement Date {MTC}, Meter Timeswitch Class Description, MTC Common Code Indicator, MTC Related Metering System Indicator, MTC Meter Type Id, MTC Payment Type Id, MTC Communication Indicator, MTC Type Indicator, MTC TPR Count.");
			}
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				if (values[4].equals("T")) {
					Boolean hasComms = null;
					if (values[8].equals("Y")) {
						hasComms = Boolean.TRUE;
					} else if (values[8].equals("N")) {
						hasComms = Boolean.FALSE;
					}
					Boolean isHh = null;
					if (values[9].equals("H")) {
						isHh = Boolean.TRUE;
					} else if (values[9].equals("N")) {
						isHh = Boolean.FALSE;
					}
					Mtc mtc = Mtc.insertMtc(null, values[0], values[3],
							values[5].equals("T"), hasComms, isHh, MtcMeterType
									.getMtcMeterType(values[6]), MtcPaymentType
									.getMtcPaymentType(values[7]), Integer
									.parseInt(values[9]), dateFormat
									.parse(values[1]), dateFormat
									.parse(values[2]));
					Hiber.session().save(mtc);
					Hiber.flush();
				}
			}			
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private Dso dso;

	private MtcCode code;

	private String description;

	private boolean hasRelatedMetering;
	private Boolean hasComms;
	private Boolean isHh;
	private MtcMeterType meterType;
	private MtcPaymentType paymentType;
	private int tprCount;
	private Date from;
	private Date to;

	public Mtc() {
	}

	public Mtc(Dso dso, MtcCode code, String description,
			boolean hasRelatedMetering, Boolean hasComms, Boolean isHh,
			MtcMeterType meterType, MtcPaymentType paymentType, int tprCount,
			Date from, Date to) throws HttpException {
		setDso(dso);
		setCode(code);
		setDescription(description);
		setHasRelatedMetering(hasRelatedMetering);
		setHasComms(hasComms);
		setIsHh(isHh);
		setMeterType(meterType);
		setPaymentType(paymentType);
		setTprCount(tprCount);
		setFrom(from);
		setTo(to);
	}

	void setDso(Dso dso) {
		this.dso = dso;
	}

	public Dso getDso() {
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

	public MtcMeterType getMeterType() {
		return meterType;
	}

	void setMeterType(MtcMeterType meterType) {
		this.meterType = meterType;
	}

	public MtcPaymentType getPaymentType() {
		return paymentType;
	}

	void setPaymentType(MtcPaymentType paymentType) {
		this.paymentType = paymentType;
	}

	public int getTprCount() {
		return tprCount;
	}

	void setTprCount(int tprCount) {
		this.tprCount = tprCount;
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

	/*
	 * public Set<LineLossFactor> getLineLossFactors() { return
	 * lineLossFactors; }
	 * 
	 * protected void setLineLossFactors(Set<LineLossFactor> lineLossFactors) {
	 * this.lineLossFactors = lineLossFactors; }
	 * 
	 * public Set<Ssc> getRegisters() { return registers; }
	 * 
	 * protected void setRegisters(Set<Ssc> registers) { this.registers =
	 * registers; }
	 */
	public String toString() {
		return code + " - " + description + " (DSO "
				+ (dso == null ? null : dso.getCode()) + ")";
	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("mtc");

		Element element = (Element) super.toXml(doc);

		element.setAttributeNode(code.toXml(doc));
		element.setAttribute("description", description);
		element.setAttribute("has-related-metering", Boolean
				.toString(hasRelatedMetering));
		element.setAttribute("has-comms", hasComms.toString());
		element.setAttribute("is-hh", isHh.toString());
		element.setAttribute("tpr-count", String.valueOf(tprCount));
		MonadDate fromDate = new MonadDate(from);
		fromDate.setLabel("from");
		element.appendChild(fromDate.toXml(doc));
		if (to != null) {
			MonadDate toDate = new MonadDate(to);
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