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

import java.util.HashSet;
import java.util.Set;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

public class MpanTop extends PersistentEntity {
	static public MpanTop insertMpanTop(ProfileClass pc, MeterTimeswitch mt,
			Llf llf, Set<Ssc> sscs) throws ProgrammerException,
			UserException {
		MpanTop mpanTop = new MpanTop(pc, mt, llf, sscs);
		Hiber.session().save(mpanTop);
		Hiber.flush();
		return mpanTop;
	}

	static public Set<MpanTop> insertMpanTops(Dso dso, ProfileClass[] pcs,
			String mts, int llf, String sscString) throws ProgrammerException,
			UserException {
		Set<Ssc> sscs = new HashSet<Ssc>();
		for (String ssc : sscString.split(",")) {
			sscs.add(Ssc.getSsc(ssc));
		}
		Set<MpanTop> tops = new HashSet<MpanTop>();
		for (ProfileClass pc : pcs) {
			for (String mt : mts.split(",")) {
				tops.add(insertMpanTop(pc, MeterTimeswitch.getMeterTimeswitch(
						dso, new MeterTimeswitchCode(mt)), dso
						.getLlf(new LlfCode(llf)), sscs));
			}
		}
		return tops;
	}

	static public MpanTop getMpanTop(Long id) throws ProgrammerException,
			UserException {
		MpanTop mpanTop = (MpanTop) Hiber.session().get(MpanTop.class, id);
		if (mpanTop == null) {
			throw UserException.newOk("There is no mpan with that id.");
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
	static public MpanTop findMpanTop(ProfileClass pc, MeterTimeswitch mt,
			Llf llf) throws ProgrammerException, UserException {
		return (MpanTop) Hiber
				.session()
				.createQuery(
						"from MpanTop top where top.profileClass = :pc and top.meterTimeswitch = :mt and top.llf = :llf")
				.setEntity("pc", pc).setEntity("mt", mt).setEntity("llf", llf)
				.uniqueResult();
	}

	static public MpanTop getMpanTop(ProfileClass pc, MeterTimeswitch mt,
			Llf llf) throws ProgrammerException, UserException {
		MpanTop mpanTop = findMpanTop(pc, mt, llf);
		if (mpanTop == null) {
			throw UserException
					.newInvalidParameter("There is no MPAN top line with Profile Class: "
							+ pc
							+ ", Meter Timeswitch: "
							+ mt
							+ " and Line Loss Factor: " + llf);
		}
		return mpanTop;
	}

	private ProfileClass profileClass;

	private MeterTimeswitch meterTimeswitch;

	private Llf llf;

	private Set<Ssc> sscs;

	MpanTop() {
	}

	MpanTop(ProfileClass profileClass, MeterTimeswitch meterTimeswitch,
			Llf llf, Set<Ssc> sscs)
			throws ProgrammerException, UserException {
		this();
		if (meterTimeswitch.getDso() != null
				&& !llf.getDso().equals(meterTimeswitch.getDso())) {
			throw UserException
					.newInvalidParameter("The Meter Timeswitch DSO doesn't match the Line Loss Factor DSO.");
		}
		setMeterTimeswitch(meterTimeswitch);
		setLlf(llf);
		setProfileClass(profileClass);
		setSscs(sscs);
	}

	public ProfileClass getProfileClass() {
		return profileClass;
	}

	void setProfileClass(ProfileClass profileClass) {
		this.profileClass = profileClass;
	}

	public MeterTimeswitch getMeterTimeswitch() {
		return meterTimeswitch;
	}

	void setMeterTimeswitch(MeterTimeswitch meterTimeswitch) {
		this.meterTimeswitch = meterTimeswitch;
	}

	public Llf getLlf() {
		return llf;
	}

	void setLlf(Llf llf) {
		this.llf = llf;
	}

	public Set<Ssc> getSscs() {
		return sscs;
	}

	void setSscs(Set<Ssc> sscs) {
		this.sscs = sscs;
	}

	public String toString() {
		return getProfileClass() + " " + getMeterTimeswitch() + " "
				+ getLlf();
	}

	public MonadUri getUri() {
		// TODO Auto-generated method stub
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(getXML(new XmlTree(
				"llf", new XmlTree("dso")).put("profileClass")
				.put("meterTimeswitch"), doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		throw UserException.newMethodNotAllowed();
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
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
	public Element toXML(Document doc) throws ProgrammerException, UserException {
		setTypeName("mpan-top");
		Element mpanTopElement = (Element) super.toXML(doc);
		return mpanTopElement;
	}
}