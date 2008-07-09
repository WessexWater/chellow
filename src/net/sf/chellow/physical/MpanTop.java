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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

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

	static public MpanTop findMpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc)
			throws HttpException {
		return (MpanTop) Hiber
				.session()
				.createQuery(
						"from MpanTop top where top.pc = :pc and top.mtc = :mtc and top.llfc = :llfc and top.ssc = :ssc")
				.setEntity("pc", pc).setEntity("mtc", mtc).setEntity("llfc",
						llfc).setEntity("ssc", ssc).uniqueResult();
	}

	static public MpanTop getMpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc)
			throws HttpException {
		MpanTop mpanTop = findMpanTop(pc, mtc, llfc, ssc);
		if (mpanTop == null) {
			throw new UserException(
					"There is no MPAN top line with Profile Class: " + pc
							+ ", Meter Timeswitch: " + mtc
							+ " and Line Loss Factor: " + llfc);
		}
		return mpanTop;
	}

	@SuppressWarnings("unchecked")
	static public MpanTop getAnMpanTop(Pc pc, Mtc mtc, Llfc llfc)
			throws HttpException {
		List<MpanTop> mpanTops = (List<MpanTop>) Hiber
				.session()
				.createQuery(
						"from MpanTop top where top.pc = :pc and top.mtc = :mtc and top.llfc = :llfc order by top.ssc.code")
				.setEntity("pc", pc).setEntity("mtc", mtc).setEntity("llfc",
						llfc).list();

		if (mpanTops.isEmpty()) {
			throw new UserException(
					"There is no MPAN top line with Profile Class: " + pc
							+ ", Meter Timeswitch: " + mtc
							+ " and Line Loss Factor: " + llfc);
		}
		return mpanTops.get(0);
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		try {
			Mdd mdd = new Mdd(sc, "ValidSettlementConfigurationProfileClass",
					new String[] { "Profile Class Id",
							"Standard Settlement Configuration Id",
							"Effective From Settlement Date {VSCPC}",
							"Effective To Settlement Date {VSCPC}" });

			Map<String, List<List<Object>>> sscPcMap = new HashMap<String, List<List<Object>>>();
			for (String[] values = mdd.getLine(); values != null; values = mdd
					.getLine()) {
				String sscCode = values[1];
				PcCode pcCode = new PcCode(Integer.parseInt(values[0]));
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
				Dso dso = Dso.getDso(values[2]);
				Date validFrom = mdd.toDate(values[7]);
				Date validTo = mdd.toDate(values[8]);
				Llfc llfc = dso.getLlfc(new LlfcCode(Integer
						.parseInt(values[6])), validFrom);
				Mtc mtc = Mtc.getMtc(dso, new MtcCode(values[0]));
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
					llfc.insertMpanTop(Pc.getPc((PcCode) sscPc.get(0)), mtc,
							ssc, derivedFrom, derivedTo);
				}
			}
		} catch (NumberFormatException e) {
			throw new InternalException(e);
		}
	}

	private Pc pc;

	private Mtc mtc;

	private Llfc llfc;

	private Ssc ssc;

	private Date from;
	private Date to;

	MpanTop() {
	}

	MpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc, Date from, Date to)
			throws HttpException {
		setMtc(mtc);
		setLlfc(llfc);
		setPc(pc);
		setSsc(ssc);
		setFrom(from);
		setTo(to);
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

	public MonadUri getUri() {
		// TODO Auto-generated method stub
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
		source.appendChild(toXml(doc, new XmlTree("llfc", new XmlTree("dso"))
				.put("pc").put("mtc")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		throw new MethodNotAllowedException();
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	/*
	 * public void insertSscs(Set<Ssc> sscSet) { for (Ssc ssc : sscSet) { if
	 * (!sscs.contains(ssc)) { sscs.add(ssc); Set<MpanTop> mpanTops =
	 * ssc.getMpanTops(); if (!mpanTops.contains(this)) { mpanTops.add(this); } } } }
	 */
	public Element toXml(Document doc) throws InternalException, HttpException {
		setTypeName("mpan-top");
		Element mpanTopElement = (Element) super.toXml(doc);
		return mpanTopElement;
	}
}