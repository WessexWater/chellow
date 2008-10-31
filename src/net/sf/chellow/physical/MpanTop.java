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

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import javax.servlet.ServletContext;

import net.sf.chellow.billing.Dso;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.Criteria;
import org.hibernate.criterion.Restrictions;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MpanTop extends PersistentEntity {
	static public MpanTop getMpanTop(Long id) throws HttpException {
		MpanTop mpanTop = (MpanTop) Hiber.session().get(MpanTop.class, id);
		if (mpanTop == null) {
			throw new UserException("There is no mpan with that id.");
		}
		return mpanTop;
	}
/*
	@SuppressWarnings("unchecked")
	static public List<MpanTop> getMpanTops(Pc pc, Mtc mtc, Llfc llfc, Date date) {
		return (List<MpanTop>) Hiber
				.session()
				.createQuery(
						"from MpanTop top where top.pc = :pc and top.mtc = :mtc and top.llfc = :llfc and top.validFrom <= :date and (top.validTo is null or top.validTo >= :date)")
				.setEntity("pc", pc).setEntity("mtc", mtc).setEntity("llfc",
						llfc).setTimestamp("date", date).list();
	}
*/
	static public MpanTop findMpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc,
			Date date) throws HttpException {
		Criteria criteria = Hiber.session().createCriteria(MpanTop.class).add(
				Restrictions.eq("pc", pc)).add(Restrictions.eq("mtc", mtc))
				.add(Restrictions.eq("llfc", llfc)).add(
						Restrictions.le("validFrom", date)).add(
						Restrictions.or(Restrictions.isNull("validTo"),
								Restrictions.ge("validTo", date)));
		if (ssc == null) {
			criteria.add(Restrictions.isNull("ssc"));
		} else {
			criteria.add(Restrictions.eq("ssc", ssc));
		}
		return (MpanTop) criteria.uniqueResult();
		/*
		 * MpanTop mpanTop = (MpanTop) return (MpanTop) Hiber .session()
		 * .createQuery( "from MpanTop top where top.pc = :pc and top.mtc = :mtc
		 * and top.llfc = :llfc and top.ssc = :ssc and top.validFrom <= :date
		 * and (top.validTo is null or top.validTo <= :date)") .setEntity("pc",
		 * pc).setEntity("mtc", mtc).setEntity("llfc", llfc).setEntity("ssc",
		 * ssc).setTimestamp("date", date) .uniqueResult();
		 */
	}

	static public MpanTop getMpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc,
			Date date) throws HttpException {
		MpanTop mpanTop = findMpanTop(pc, mtc, llfc, ssc, date);
		if (mpanTop == null) {
			throw new UserException(
					"There is no MPAN top line with Profile Class: " + pc
							+ ", Meter Timeswitch: " + mtc
							+ " and Line Loss Factor: " + llfc);
		}
		return mpanTop;
	}

	/*
	 * @SuppressWarnings("unchecked") static public MpanTop getAnMpanTop(Pc pc,
	 * Mtc mtc, Llfc llfc) throws HttpException { List<MpanTop> mpanTops =
	 * (List<MpanTop>) Hiber .session() .createQuery( "from MpanTop top where
	 * top.pc = :pc and top.mtc = :mtc and top.llfc = :llfc order by
	 * top.ssc.code") .setEntity("pc", pc).setEntity("mtc",
	 * mtc).setEntity("llfc", llfc).list();
	 * 
	 * if (mpanTops.isEmpty()) { throw new UserException( "There is no MPAN top
	 * line with Profile Class: " + pc + ", Meter Timeswitch: " + mtc + " and
	 * Line Loss Factor: " + llfc); } return mpanTops.get(0); }
	 */
	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add MPAN tops.");
		try {
			Mdd mdd = new Mdd(sc, "ValidSettlementConfigurationProfileClass",
					new String[] { "Profile Class Id",
							"Standard Settlement Configuration Id",
							"Effective From Settlement Date {VSCPC}",
							"Effective To Settlement Date {VSCPC}" });

			Map<Integer, List<List<Object>>> dsoGroupSscPcMap = new HashMap<Integer, List<List<Object>>>();
			for (String[] values = mdd.getLine(); values != null; values = mdd
					.getLine()) {
				int sscCode = Integer.parseInt(values[1]);
				String pcCode = values[0];
				Date validFrom = mdd.toDate(values[2]);
				Date validTo = mdd.toDate(values[3]);

				if (!sscPcMap.containsKey(sscCode)) {
					sscPcMap.put(sscCode, new ArrayList<List<Object>>());
				}
				List<List<Object>> sscPcs = sscPcMap.get(sscCode);
				List<Object> sscPc = new ArrayList<Object>();
				sscPc.add(pcCode);
				sscPc.add(validFrom);
				sscPc.add(validTo);
				sscPcs.add(sscPc);
			}
			mdd = new Mdd(sc, "ValidMtcLlfcSsc", new String[] {
					"Meter Timeswitch Class Id",
					"Effective From Settlement Date {MTC}",
					"Market Participant Id",
					"Effective From Settlement Date {MTCPA}",
					"Standard Settlement Configuration Id",
					"Effective From Settlement Date {VMTCSC}",
					"Line Loss Factor Class Id",
					"Effective From Settlement Date {VMTCLSC}",
					"Effective To Settlement Date {VMTCLSC}" });

			for (String[] values = mdd.getLine(); values != null; values = mdd
					.getLine()) {
				Dso dso = Dso.getDso(Participant.getParticipant(values[2]));
				Date validFrom = mdd.toDate(values[7]);
				Date validTo = mdd.toDate(values[8]);
				Llfc llfc = dso.getLlfc(values[6], validFrom);
				Mtc mtc = Mtc.getMtc(dso, values[0]);
				Ssc ssc = Ssc.getSsc(values[4]);
				for (List<Object> sscPc : sscPcMap.get(ssc.getCode())) {
					Date mapFrom = (Date) sscPc.get(1);
					Date mapTo = (Date) sscPc.get(2);
					Date derivedFrom = validFrom.after(mapFrom) ? validFrom
							: mapFrom;
					Date derivedTo = null;
					if (mapTo != null && validTo != null) {
						derivedTo = validTo.before(mapTo) ? validTo : mapTo;
					}
					llfc.insertMpanTop(Pc.getPc((String) sscPc.get(0)), mtc,
							ssc, derivedFrom, derivedTo);
				}
				Hiber.close();
			}
			mdd = new Mdd(sc, "ValidMtcLlfc", new String[] {
					"Meter Timeswitch Class Id",
					"Effective From Settlement Date {MTC}",
					"Market Participant Id",
					"Effective From Settlement Date {MTCPA}",
					"Line Loss Factor Class Id",
					"Effective From Settlement Date {VMTCLC}",
					"Effective To Settlement Date {VMTCLC}" });
			for (String[] values = mdd.getLine(); values != null; values = mdd
					.getLine()) {
				Dso dso = Dso.getDso(Participant.getParticipant(values[2]));
				Date validFrom = mdd.toDate(values[5]);
				Date validTo = mdd.toDate(values[6]);
				Llfc llfc = dso.getLlfc(values[4], validFrom);
				Mtc mtc = Mtc.getMtc(dso, values[0]);
				llfc
						.insertMpanTop(Pc.getPc("0"), mtc, null, validFrom,
								validTo);
				Hiber.close();
			}
		} catch (NumberFormatException e) {
			throw new InternalException(e);
		}

		Debug.print("Finished adding MPAN tops.");
	}

	private Pc pc;

	private Mtc mtc;

	private Llfc llfc;

	private Ssc ssc;
	
	private GspGroup gspGroup;

	private Date validFrom;
	private Date validTo;

	MpanTop() {
	}

	MpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc, GspGroup gspGroup, Date validFrom, Date validTo)
			throws HttpException {
		setMtc(mtc);
		setLlfc(llfc);
		setPc(pc);
		setSsc(ssc);
		setGspGroup(gspGroup);
		setValidFrom(validFrom);
		setValidTo(validTo);
	}

	public Pc getPc() {
		return pc;
	}

	void setPc(Pc pc) {
		this.pc = pc;
	}

	public Mtc getMtc() {
		return mtc;
	}

	void setMtc(Mtc mtc) {
		this.mtc = mtc;
	}

	public Llfc getLlfc() {
		return llfc;
	}

	void setLlfc(Llfc llfc) {
		this.llfc = llfc;
	}

	public Ssc getSsc() {
		return ssc;
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public GspGroup getGspGroup() {
		return gspGroup;
	}

	void setGspGroup(GspGroup gspGroup) {
		this.gspGroup = gspGroup;
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

	public MonadUri getUri() {
		// TODO Auto-generated method stub
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("llfc", new XmlTree("dso"))
				.put("pc").put("mtc").put("ssc")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}

	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	/*
	 * public void insertSscs(Set<Ssc> sscSet) { for (Ssc ssc : sscSet) { if
	 * (!sscs.contains(ssc)) { sscs.add(ssc); Set<MpanTop> mpanTops =
	 * ssc.getMpanTops(); if (!mpanTops.contains(this)) { mpanTops.add(this); } } } }
	 */
	public Element toXml(Document doc) throws HttpException {
		Element mpanTopElement = super.toXml(doc, "mpan-top");
		MonadDate from = new MonadDate(validFrom);
		from.setLabel("from");
		mpanTopElement.appendChild(from.toXml(doc));
		if (validTo != null) {
			MonadDate to = new MonadDate(validTo);
			to.setLabel("to");
			mpanTopElement.appendChild(to.toXml(doc));
		}
		return mpanTopElement;
	}
	
	public String toString() {
		return pc.codeAsString() + " " + mtc.codeAsString() + " " + llfc.codeAsString();
	}
}