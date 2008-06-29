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
import java.text.DateFormat;
import java.text.ParseException;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import com.Ostermiller.util.CSVParser;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class MpanTop extends PersistentEntity {
	/*
	static public MpanTop insertMpanTop(Pc pc, Mtc mt, Llf llf, Ssc ssc)
			throws InternalException, HttpException {
		MpanTop mpanTop = new MpanTop(pc, mt, llf, ssc);
		Hiber.session().save(mpanTop);
		Hiber.flush();
		return mpanTop;
	}
	*/

	static public Set<MpanTop> insertMpanTops(Dso dso, Pc[] pcs, String mts,
			int llf, String sscString) throws InternalException, HttpException {
		Set<Ssc> sscs = new HashSet<Ssc>();
		for (String ssc : sscString.split(",")) {
			sscs.add(Ssc.getSsc(ssc));
		}
		Set<MpanTop> tops = new HashSet<MpanTop>();
		for (Pc pc : pcs) {
			for (String mt : mts.split(",")) {
				tops.add(insertMpanTop(pc, Mtc.getMtc(dso,
						new MeterTimeswitchCode(mt)), dso.getLlf(new LlfCode(
						llf)), sscs));
			}
		}
		return tops;
	}

	static public MpanTop getMpanTop(Long id) throws InternalException,
			HttpException {
		MpanTop mpanTop = (MpanTop) Hiber.session().get(MpanTop.class, id);
		if (mpanTop == null) {
			throw new UserException("There is no mpan with that id.");
		}
		return mpanTop;
	}

	/*
	 * static public MpanTop findMpanTop(String dsoStr, int pc, String mt,
	 * String llf) throws ProgrammerException, UserException { Dso dso =
	 * Dso.findDso(dsoStr); return findMpanTop(ProfileClass .getProfileClass(new
	 * ProfileClassCode(pc)), MeterTimeswitch .getMeterTimeswitch(dso, new
	 * MeterTimeswitchCode(mt)), LineLossFactor.getLineLossFactor(dso, new
	 * LineLossFactorCode( llf))); }
	 */
	static public MpanTop findMpanTop(Pc pc, Mtc mt, Llf llf)
			throws InternalException, HttpException {
		return (MpanTop) Hiber
				.session()
				.createQuery(
						"from MpanTop top where top.profileClass = :pc and top.meterTimeswitch = :mt and top.llf = :llf")
				.setEntity("pc", pc).setEntity("mt", mt).setEntity("llf", llf)
				.uniqueResult();
	}

	static public MpanTop getMpanTop(Pc pc, Mtc mt, Llf llf)
			throws InternalException, HttpException {
		MpanTop mpanTop = findMpanTop(pc, mt, llf);
		if (mpanTop == null) {
			throw new UserException(
					"There is no MPAN top line with Profile Class: " + pc
							+ ", Meter Timeswitch: " + mt
							+ " and Line Loss Factor: " + llf);
		}
		return mpanTop;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = MpanTop.class.getClassLoader();
			CSVParser parser = new CSVParser(new InputStreamReader(classLoader
					.getResource("net/sf/chellow/physical/ValidMtcLlfcSsc.csv")
					.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 9
					|| !titles[0].trim().equals("Meter Timeswitch Class Id")
					|| !titles[1].trim().equals(
							"Effective From Settlement Date {MTC}")
					|| !titles[2].trim().equals("Market Participant Id")
					|| !titles[3].trim().equals(
							"Effective From Settlement Date {MTCPA}")
					|| !titles[4].trim().equals(
							"Standard Settlement Configuration Id")
					|| !titles[5].trim().equals(
							"Effective From Settlement Date {VMTCSC}")
					|| !titles[6].trim().equals("Line Loss Factor Class Id")
					|| !titles[7].trim().equals(
							"Effective From Settlement Date {VMTCLSC}")
					|| !titles[8].trim().equals(
							"Effective To Settlement Date {VMTCLSC}")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Meter Timeswitch Class Id, Effective From Settlement Date {MTC}, Market Participant Id, Effective From Settlement Date {MTCPA}, Standard Settlement Configuration Id, Effective From Settlement Date {VMTCSC}, Line Loss Factor Class Id, Effective From Settlement Date {VMTCLSC}, Effective To Settlement Date {VMTCLSC}.");
			}
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Dso dso = Dso.getDso(values[2]);
				Llfc llfc = dso.getLlf(new LlfcCode(Integer.parseInt(values[6])));
				Mtc mtc = Mtc.getm
				llfc.insertMpanTop(Pc.getProfileClass(PcCode.PC00), mtc, ssc)
				String participantCode = values[0];
				String description = values[5];
				VoltageLevel vLevel = null;
				if (description.contains(VoltageLevel.EHV)) {
					vLevel = VoltageLevel.getVoltageLevel(VoltageLevel.EHV);
				} else if (description.contains(VoltageLevel.HV)) {
					vLevel = VoltageLevel.getVoltageLevel(VoltageLevel.HV);
				} else {
					vLevel = VoltageLevel.getVoltageLevel(VoltageLevel.LV);
				}
				boolean isSubstation = (participantCode.equals("SWEB") && description
						.contains("S/S"))
						|| (!participantCode.equals("SWEB") && description
								.contains("sub"));
				String indicator = values[6];
				boolean isImport = indicator.equals("A")
						|| indicator.equals("B");
				Hiber.session().save(
						new MpanTop(Dso.getDso(participantCode), Integer
								.parseInt(values[3]), description, vLevel,
								isSubstation, isImport, dateFormat
										.parse(values[2]), dateFormat
										.parse(values[4])));
				
				MpanTop mpanTop = new MpanTop(pc, mt, llf, ssc);
				Hiber.session().save(mpanTop);
				Hiber.flush();
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (NumberFormatException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private Pc pc;

	private Mtc mtc;

	private Llfc llfc;

	private Ssc ssc;

	MpanTop() {
	}

	MpanTop(Pc pc, Mtc mtc, Llfc llfc, Ssc ssc) throws HttpException {
		setMtc(mtc);
		setLlfc(llfc);
		setPc(pc);
		setSsc(ssc);
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
		source.appendChild(toXml(doc, new XmlTree("llf", new XmlTree("dso"))
				.put("profileClass").put("meterTimeswitch")));
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

	public Dso getDso() {
		return llf.getDso();
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