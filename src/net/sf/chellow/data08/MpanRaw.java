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

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.LlfcCode;
import net.sf.chellow.physical.Mtc;
import net.sf.chellow.physical.MtcCode;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.MpanTop;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.Pc;
import net.sf.chellow.physical.PcCode;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MpanRaw extends MonadObject {
	private PcCode profileClassCode;

	private MtcCode meterTimeswitchCode;

	private LlfcCode llfCode;

	private MpanCoreRaw mpanCoreRaw;

	public MpanRaw(String mpan) throws InternalException, HttpException {
		this(null, mpan);
	}

	public MpanRaw(String label, String mpan) throws HttpException {
		setLabel(label);
		mpan = mpan.replace(" ", "");
		if (mpan.length() != 21) {
			throw new UserException("The MPAN must contain exactly 21 digits.");
		}
		init(new PcCode(Integer.parseInt(mpan.substring(0, 2))),
				new MtcCode(mpan.substring(2, 5)), new LlfcCode(mpan
						.substring(5, 8)), new MpanCoreRaw(mpan.substring(8)));
	}

	private void init(PcCode profileClassCode,
			MtcCode meterTimeswitchCode, LlfcCode llfCode,
			MpanCoreRaw mpanCoreRaw) throws InternalException {
		if (profileClassCode == null || meterTimeswitchCode == null
				|| mpanCoreRaw == null) {
			throw new InternalException("No nulls allowed.");
		}
		this.profileClassCode = profileClassCode;
		this.meterTimeswitchCode = meterTimeswitchCode;
		this.llfCode = llfCode;
		this.mpanCoreRaw = mpanCoreRaw;
	}

	public MpanRaw(PcCode profileClassCode,
			MtcCode meterTimeswitchCode, LlfcCode llfCode,
			MpanCoreRaw mpanCoreRaw) throws InternalException {
		init(profileClassCode, meterTimeswitchCode, llfCode, mpanCoreRaw);
	}

	public PcCode getProfileClassCode() {
		return profileClassCode;
	}

	public MtcCode getMeterTimeswitchCode() {
		return meterTimeswitchCode;
	}

	public LlfcCode getLlfCode() {
		return llfCode;
	}

	public MpanCoreRaw getMpanCoreRaw() {
		return mpanCoreRaw;
	}

	public Pc getProfileClass() throws InternalException,
			HttpException {
		return Pc.getProfileClass(profileClassCode);
	}

	public Mtc getMeterTimeswitch() throws InternalException,
			HttpException {
		return Mtc.getMtc(mpanCoreRaw.getDso(),
				meterTimeswitchCode);
	}

	public Llfc getLlf() throws InternalException, HttpException {
		return mpanCoreRaw.getDso().getLlf(llfCode);
	}

	public MpanTop getMpanTop() throws InternalException, HttpException {
		return MpanTop.getMpanTop(getProfileClass(), getMeterTimeswitch(),
				getLlf());
	}

	public MpanCore getMpanCore(Organization organization)
			throws InternalException, HttpException {
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

	public Attr toXml(Document doc) {
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