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
import java.util.Map.Entry;

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
	 * @SuppressWarnings("unchecked") static public List<MpanTop>
	 * getMpanTops(Pc pc, Mtc mtc, Llfc llfc, Date date) { return (List<MpanTop>)
	 * Hiber .session() .createQuery( "from MpanTop top where top.pc = :pc and
	 * top.mtc = :mtc and top.llfc = :llfc and top.validFrom <= :date and
	 * (top.validTo is null or top.validTo >= :date)") .setEntity("pc",
	 * pc).setEntity("mtc", mtc).setEntity("llfc", llfc).setTimestamp("date",
	 * date).list(); }
	 */
	static public MpanTop findMpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc,
			GspGroup group, Date date) throws HttpException {
		/*
		 * Debug.print("trying to find mpantop. " + pc + " " + mtc + " " + llfc + " " +
		 * ssc + " " + group + " " + date); if (ssc == null) {
		 * Debug.print("About to loop."); for (MpanTop top : (List<MpanTop>)
		 * Hiber.session().createQuery("from MpanTop top where top.pc = :pc and
		 * top.mtc = :mtc and top.llfc = :llfc and top.gspGroup = :group and ssc
		 * is null").setEntity("group", group).setEntity("pc",
		 * pc).setEntity("llfc", llfc).setEntity("mtc", mtc).list()) {
		 * Debug.print("MpanTop " + top.getPc() + " " + top.getMtc() + " " +
		 * top.getLlfc() + " " + top.getSsc() + " " + top.getGspGroup() + " " +
		 * top.getValidFrom() + " " + top.getValidTo()); } } StringBuilder
		 * queryString = new StringBuilder( "from MpanTop top where top.pc = :pc
		 * and top.mtc = :mtc and top.llfc = :llfc and top.gspGroup = :group and
		 * top.validFrom <= :date and (top.validTo is null or top.validTo >=
		 * :date)"); Query query = null; if (ssc == null) { queryString.append("
		 * and top.ssc is null"); query =
		 * Hiber.session().createQuery(queryString.toString()) .setEntity("pc",
		 * pc).setEntity("mtc", mtc).setEntity( "llfc", llfc).setEntity("group",
		 * group) .setTimestamp("date", date); } else { queryString.append(" and
		 * top.ssc = :ssc"); query =
		 * Hiber.session().createQuery(queryString.toString()) .setEntity("pc",
		 * pc).setEntity("mtc", mtc).setEntity( "llfc", llfc).setEntity("ssc",
		 * ssc).setEntity( "group", group).setTimestamp("date", date); } return
		 * (MpanTop) query.uniqueResult(); // return (MpanTop)
		 * Hiber.session().createQuery("from MpanTop top where // top.pc = :pc
		 * and top.mtc = :mtc and top.llfc = :llfc and top.ssc = // :ssc and
		 * top.gspGroup = :group and top.validFrom <= :date and // (top.validTo
		 * is null or top.validTo >= :date)").setEntity("pc", //
		 * pc).setEntity("mtc", mtc).setEntity("llfc", //
		 * llfc).setEntity("gspGroup", group).setEntity("date", //
		 * date).uniqueResult();
		 * 
		 */

		Criteria criteria = Hiber.session().createCriteria(MpanTop.class).add(
				Restrictions.eq("pc", pc)).add(Restrictions.eq("mtc", mtc))
				.add(Restrictions.eq("gspGroup", group)).add(
						Restrictions.eq("llfc", llfc)).add(
						Restrictions.le("validFrom", date)).add(
						Restrictions.or(Restrictions.isNull("validTo"),
								Restrictions.ge("validTo", date)));
		if (ssc == null) {
			criteria.add(Restrictions.isNull("ssc"));
		} else {
			criteria.add(Restrictions.eq("ssc", ssc));
		}
		return (MpanTop) criteria.uniqueResult(); /*
													 * MpanTop mpanTop =
													 * (MpanTop) return
													 * (MpanTop) Hiber
													 * .session() .createQuery(
													 * "from MpanTop top where
													 * top.pc = :pc and top.mtc =
													 * :mtc and top.llfc = :llfc
													 * and top.ssc = :ssc and
													 * top.validFrom <= :date
													 * and (top.validTo is null
													 * or top.validTo <=
													 * :date)") .setEntity("pc",
													 * pc).setEntity("mtc",
													 * mtc).setEntity("llfc",
													 * llfc).setEntity("ssc",
													 * ssc).setTimestamp("date",
													 * date) .uniqueResult();
													 */
	}

	static public MpanTop getMpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc,
			GspGroup group, Date date) throws HttpException {
		MpanTop mpanTop = findMpanTop(pc, mtc, llfc, ssc, group, date);
		if (mpanTop == null) {
			throw new UserException(
					"There is no MPAN top line with Profile Class: " + pc
							+ ", Meter Timeswitch: " + mtc
							+ ", Line Loss Factor: " + llfc + ", SSC: " + ssc
							+ ", GSP Group: " + group + " and Date: " + date);
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
			Map<Integer, List<List<Object>>> sscPcMap = new HashMap<Integer, List<List<Object>>>();
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

			Map<String, List<List<Object>>> dsoGroupMap = new HashMap<String, List<List<Object>>>();
			mdd = new Mdd(sc, "GspGroupDistributor", new String[] {
					"GSP Group Id", "Market Participant Id",
					"Market Participant Role Code",
					"Effective From Date {MPR}",
					"Effective From Settlement Date {GGD}",
					"Effective To Settlement Date {GGD}" });
			for (String[] values = mdd.getLine(); values != null; values = mdd
					.getLine()) {
				String gspCode = values[0];
				String dsoCode = values[1];
				Date validFrom = mdd.toDate(values[3]);
				if (validFrom.before(mdd.toDate(values[4]))) {
					validFrom = mdd.toDate(values[4]);
				}
				Date validTo = mdd.toDate(values[5]);

				if (!dsoGroupMap.containsKey(dsoCode)) {
					dsoGroupMap.put(dsoCode, new ArrayList<List<Object>>());
				}
				List<List<Object>> groupsList = dsoGroupMap.get(dsoCode);
				List<Object> groupList = new ArrayList<Object>();
				groupsList.add(groupList);
				groupList.add(gspCode);
				groupList.add(validFrom);
				groupList.add(validTo);
			}
			Map<String, Map<String, List<Object>>> groupSscMap = new HashMap<String, Map<String, List<Object>>>();
			mdd = new Mdd(sc, "AverageFractionOfYearlyConsumptionSet",
					new String[] { "GSP Group Id", "Profile Class Id",
							"Standard Settlement Configuration Id",
							"Effective From Settlement Date {VSCPC}",
							"Effective From Settlement Date {AFOYCS}",
							"Effective To Settlement Date {AFOYCS}" });
			for (String[] values = mdd.getLine(); values != null; values = mdd
					.getLine()) {
				String gspCode = values[0];
				String pcCode = values[1];
				int sscCode = Integer.parseInt(values[2]);
				Date validFrom = Mdd.minDate(mdd.toDate(values[3]), mdd
						.toDate(values[4]));
				Date validTo = mdd.toDate(values[5]);
				String key = gspCode + sscCode;
				if (!groupSscMap.containsKey(key)) {
					groupSscMap.put(key, new HashMap<String, List<Object>>());
				}
				Map<String, List<Object>> groupSscPcMap = groupSscMap.get(key);
				if (groupSscPcMap.containsKey(pcCode)) {
					List<Object> groupSscList = groupSscPcMap.get(pcCode);
					groupSscList.set(0, Mdd.minDate((Date) groupSscList.get(0),
							validFrom));
					groupSscList.set(1, Mdd.maxDate((Date) groupSscList.get(1),
							validTo));
					/*
					 * if (validFrom != null && mapTo != null && mapTo.getTime() +
					 * 24 * 60 * 60 == validFrom.getTime()) {
					 * groupSscList.set(1, validTo); } else if (validTo != null &&
					 * mapFrom != null && validTo.getTime() + 24 * 60 * 60 ==
					 * mapFrom.getTime()) { groupSscList.set(0, validFrom); }
					 * else { groupSscList = new ArrayList<Object>();
					 * groupSscsList.add(groupSscList);
					 * groupSscList.add(validFrom); groupSscList.add(validTo); }
					 */
				} else {
					List<Object> groupSscList = new ArrayList<Object>();
					groupSscPcMap.put(pcCode, groupSscList);
					groupSscList.add(validFrom);
					groupSscList.add(validTo);
				}
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
				String participantCode = values[2];
				Dso dso = Dso.getDso(Participant
						.getParticipant(participantCode));
				Date validFrom = mdd.toDate(values[7]);
				Date validTo = mdd.toDate(values[8]);
				Llfc llfc = dso.getLlfc(values[6], validFrom);
				Mtc mtc = Mtc.getMtc(dso, values[0]);
				Ssc ssc = Ssc.getSsc(values[4]);
				for (List<Object> groupList : dsoGroupMap.get(participantCode)) {
					String groupCode = (String) groupList.get(0);
					GspGroup group = GspGroup.getGspGroup(groupCode);
					Date groupFrom = Mdd.maxDate((Date) groupList.get(1),
							validFrom);
					Date groupTo = Mdd
							.minDate((Date) groupList.get(2), validTo);
					//Debug.print("GC :" + groupCode + " ssc " + ssc.getCode()
					//		+ " part " + participantCode + " llfc "
					//		+ llfc.codeAsString() + " mtc "
					//		+ mtc.codeAsString());
					//Debug
					//		.print(""
					//				+ groupSscMap
					//						.get(groupCode + ssc.getCode()));
					Map<String, List<Object>> pcs = groupSscMap.get(groupCode
							+ ssc.getCode());
					if (pcs != null) {
						for (Entry<String, List<Object>> entrySet : pcs
								.entrySet()) {
							String pcCode = entrySet.getKey();
							Date from = Mdd.maxDate((Date) entrySet.getValue()
									.get(0), groupFrom);
							Date to = Mdd.minDate((Date) entrySet.getValue()
									.get(1), groupTo);
							llfc.insertMpanTop(Pc.getPc(pcCode), mtc, ssc,
									group, from, to);
							Hiber.close();
						}
					} else {
						List<List<Object>> pclasses = sscPcMap.get(ssc.getCode());
						for (List<Object> pcList : pclasses) {
							String pcCode = (String) pcList.get(0);
							Date from = Mdd.maxDate((Date) pcList.get(1)
									, groupFrom);
							Date to = Mdd.minDate((Date) pcList.get(2), groupTo);
							llfc.insertMpanTop(Pc.getPc(pcCode), mtc, ssc,
									group, from, to);
							Hiber.close();
						}
					}
				}
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
				String participantCode = values[2];
				Dso dso = Dso.getDso(Participant
						.getParticipant(participantCode));
				Date validFrom = mdd.toDate(values[5]);
				Date validTo = mdd.toDate(values[6]);
				Llfc llfc = dso.getLlfc(values[4], validFrom);
				Mtc mtc = Mtc.getMtc(dso, values[0]);
				for (List<Object> groupList : dsoGroupMap.get(participantCode)) {
					GspGroup group = GspGroup.getGspGroup((String) groupList
							.get(0));
					Date from = Mdd.maxDate((Date) groupList.get(1), validFrom);
					Date to = Mdd.minDate((Date) groupList.get(2), validTo);
					llfc.insertMpanTop(Pc.getPc("0"), mtc, null, group, from,
							to);
					Hiber.close();
				}
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

	MpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc, GspGroup gspGroup,
			Date validFrom, Date validTo) throws HttpException {
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
		return pc.codeAsString() + " " + mtc.codeAsString() + " "
				+ llfc.codeAsString();
	}
}