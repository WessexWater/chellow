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

import java.util.Date;

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
import net.sf.chellow.physical.Ssc;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MpanRaw extends MonadObject {
	private PcCode pcCode;

	private MtcCode mtcCode;

	private LlfcCode llfcCode;

	private MpanCoreRaw mpanCoreRaw;

	public MpanRaw(String mpan) throws HttpException {
		this(null, mpan);
	}

	public MpanRaw(String label, String mpan) throws HttpException {
		setLabel(label);
		mpan = mpan.replace(" ", "");
		if (mpan.length() != 21) {
			throw new UserException("The MPAN must contain exactly 21 digits.");
		}
		init(new PcCode(Integer.parseInt(mpan.substring(0, 2))), new MtcCode(
				mpan.substring(2, 5)), new LlfcCode(mpan.substring(5, 8)),
				new MpanCoreRaw(mpan.substring(8)));
	}

	private void init(PcCode pcCode, MtcCode mtcCode, LlfcCode llfCode,
			MpanCoreRaw mpanCoreRaw) throws InternalException {
		if (pcCode == null || mtcCode == null || mpanCoreRaw == null) {
			throw new InternalException("No nulls allowed.");
		}
		this.pcCode = pcCode;
		this.mtcCode = mtcCode;
		this.llfcCode = llfCode;
		this.mpanCoreRaw = mpanCoreRaw;
	}

	public MpanRaw(PcCode pcCode, MtcCode mtcCode, LlfcCode llfcCode,
			MpanCoreRaw mpanCoreRaw) throws InternalException {
		init(pcCode, mtcCode, llfcCode, mpanCoreRaw);
	}

	public PcCode getPcCode() {
		return pcCode;
	}

	public MtcCode getMtcCode() {
		return mtcCode;
	}

	public LlfcCode getLlfcCode() {
		return llfcCode;
	}

	public MpanCoreRaw getMpanCoreRaw() {
		return mpanCoreRaw;
	}

	public Pc getPc() throws HttpException {
		return Pc.getPc(pcCode);
	}

	public Mtc getMtc() throws HttpException {
		return Mtc.getMtc(mpanCoreRaw.getDso(), mtcCode);
	}

	public Llfc getLlfc() throws HttpException {
		return mpanCoreRaw.getDso().getLlfc(llfcCode);
	}

	public MpanTop getMpanTop(Ssc ssc, Date date) throws HttpException {
		return MpanTop.getMpanTop(getPc(), getMtc(), getLlfc(), ssc, date);
	}

	public MpanCore getMpanCore(Organization organization) throws HttpException {
		return organization.getMpanCore(mpanCoreRaw);
	}

	public String toString() {
		return pcCode.toString() + " " + mtcCode.toString() + " "
				+ llfcCode.toString() + " " + mpanCoreRaw.toString();
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
			isEqual = getPcCode().equals(mpan.getPcCode())
					&& getMtcCode().equals(mpan.getMtcCode())
					&& getLlfcCode().equals(mpan.getLlfcCode())
					&& getMpanCoreRaw().equals(mpan.getMpanCoreRaw());
		}
		return isEqual;
	}

	public int hashCode() {
		return getPcCode().hashCode() + getMtcCode().hashCode()
				+ getLlfcCode().hashCode() + getMpanCoreRaw().hashCode();
	}
}