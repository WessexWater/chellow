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

package net.sf.chellow.data08;

import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.VFMessage;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.physical.Llf;
import net.sf.chellow.physical.LlfCode;
import net.sf.chellow.physical.MeterTimeswitch;
import net.sf.chellow.physical.MeterTimeswitchCode;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.MpanTop;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.ProfileClass;
import net.sf.chellow.physical.ProfileClassCode;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MpanRaw extends MonadObject {
	private ProfileClassCode profileClassCode;

	private MeterTimeswitchCode meterTimeswitchCode;

	private LlfCode llfCode;

	private MpanCoreRaw mpanCoreRaw;

	public MpanRaw(String mpan) throws ProgrammerException, UserException {
		this(null, mpan);
	}

	public MpanRaw(String label, String mpan) throws ProgrammerException,
			UserException {
		setLabel(label);
		mpan = mpan.replace(" ", "");
		if (mpan.length() != 21) {
			throw UserException.newInvalidParameter(new VFMessage(
					"The MPAN must contain exactly 21 digits."));
		}
		init(new ProfileClassCode(Integer.parseInt(mpan.substring(0, 2))),
				new MeterTimeswitchCode(mpan.substring(2, 5)), new LlfCode(mpan
						.substring(5, 8)), new MpanCoreRaw(mpan.substring(8)));
	}

	private void init(ProfileClassCode profileClassCode,
			MeterTimeswitchCode meterTimeswitchCode, LlfCode llfCode,
			MpanCoreRaw mpanCoreRaw) throws ProgrammerException {
		if (profileClassCode == null || meterTimeswitchCode == null
				|| mpanCoreRaw == null) {
			throw new ProgrammerException("No nulls allowed.");
		}
		this.profileClassCode = profileClassCode;
		this.meterTimeswitchCode = meterTimeswitchCode;
		this.llfCode = llfCode;
		this.mpanCoreRaw = mpanCoreRaw;
	}

	public MpanRaw(ProfileClassCode profileClassCode,
			MeterTimeswitchCode meterTimeswitchCode, LlfCode llfCode,
			MpanCoreRaw mpanCoreRaw) throws ProgrammerException {
		init(profileClassCode, meterTimeswitchCode, llfCode, mpanCoreRaw);
	}

	public ProfileClassCode getProfileClassCode() {
		return profileClassCode;
	}

	public MeterTimeswitchCode getMeterTimeswitchCode() {
		return meterTimeswitchCode;
	}

	public LlfCode getLlfCode() {
		return llfCode;
	}

	public MpanCoreRaw getMpanCoreRaw() {
		return mpanCoreRaw;
	}

	public ProfileClass getProfileClass() throws ProgrammerException,
			UserException {
		return ProfileClass.getProfileClass(profileClassCode);
	}

	public MeterTimeswitch getMeterTimeswitch() throws ProgrammerException,
			UserException {
		return MeterTimeswitch.getMeterTimeswitch(mpanCoreRaw.getDso(),
				meterTimeswitchCode);
	}

	public Llf getLlf() throws ProgrammerException, UserException {
		return mpanCoreRaw.getDso().getLlf(llfCode);
	}

	public MpanTop getMpanTop() throws ProgrammerException, UserException {
		return MpanTop.getMpanTop(getProfileClass(), getMeterTimeswitch(),
				getLlf());
	}

	public MpanCore getMpanCore(Organization organization)
			throws ProgrammerException, UserException {
		return organization.getMpanCore(mpanCoreRaw);
	}

	public String toString() {
		return profileClassCode.toString() + " "
				+ meterTimeswitchCode.toString() + " " + llfCode.toString()
				+ " " + mpanCoreRaw.toString();
	}

	public String toStringNoSpaces() {
		return toString().replace(" ", "");
	}

	public Attr toXML(Document doc) {
		Attr attr = doc.createAttribute("mpan");

		attr.setValue(toString());
		return attr;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof MpanRaw) {
			MpanRaw mpan = (MpanRaw) obj;
			isEqual = getProfileClassCode().equals(mpan.getProfileClassCode())
					&& getMeterTimeswitchCode().equals(
							mpan.getMeterTimeswitchCode())
					&& getLlfCode().equals(mpan.getLlfCode())
					&& getMpanCoreRaw().equals(mpan.getMpanCoreRaw());
		}
		return isEqual;
	}

	public int hashCode() {
		return getProfileClassCode().hashCode()
				+ getMeterTimeswitchCode().hashCode() + getLlfCode().hashCode()
				+ getMpanCoreRaw().hashCode();
	}
}