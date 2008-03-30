/*
 
 Copyright 2005 Meniscus Systems Ltd
 
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
import net.sf.chellow.physical.CheckDigit;
import net.sf.chellow.physical.Dso;
import net.sf.chellow.physical.DsoCode;
import net.sf.chellow.physical.MpanUniquePart;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MpanCoreRaw extends MonadObject {
	private DsoCode dsoCode;

	private MpanUniquePart uniquePart;

	private CheckDigit checkDigit;

	public MpanCoreRaw(String mpanCore) throws ProgrammerException,
			UserException {
		this(null, mpanCore);
	}

	public MpanCoreRaw(String label, String mpanCore)
			throws ProgrammerException, UserException {
		setLabel(label);
		mpanCore = mpanCore.replace(" ", "");
		if (mpanCore.length() != 13) {
			throw UserException.newInvalidParameter(new VFMessage(
					"The MPAN core (" + mpanCore
							+ ") must contain exactly 13 digits."));
		}
		init(new DsoCode(mpanCore.substring(0, 2)), new MpanUniquePart(mpanCore
				.substring(2, 12)), new CheckDigit(new Character(mpanCore
				.charAt(mpanCore.length() - 1))));
	}

	private void init(DsoCode dsoCode, MpanUniquePart uniquePart,
			CheckDigit checkDigit) throws ProgrammerException, UserException {
		setTypeName("mpan-core-raw");
		if (dsoCode == null || uniquePart == null || checkDigit == null) {
			throw new ProgrammerException("No nulls allowed.");
		}
		if (!checkCheckDigit(dsoCode.toString() + uniquePart.toString(),
				Character
						.getNumericValue(checkDigit.getCharacter().charValue()))) {

			throw UserException
					.newInvalidParameter("This is not a valid MPAN core. It fails the checksum test.");
		}

		this.dsoCode = dsoCode;
		this.uniquePart = uniquePart;
		this.checkDigit = checkDigit;
	}

	public MpanCoreRaw(DsoCode dsoCode, MpanUniquePart uniquePart,
			CheckDigit checkDigit) throws ProgrammerException, UserException {
		init(dsoCode, uniquePart, checkDigit);
	}

	public DsoCode getDsoCode() {
		return dsoCode;
	}

	public MpanUniquePart getUniquePart() {
		return uniquePart;
	}

	public CheckDigit getCheckDigit() {
		return checkDigit;
	}

	public String toString() {
		return dsoCode.toString() + " " + uniquePart.toString().substring(0, 4)
				+ " " + uniquePart.toString().substring(4, 8) + " "
				+ uniquePart.toString().substring(8)
				+ checkDigit.getCharacter().charValue();
	}

	public String toStringNoSpaces() {
		return dsoCode.toString() + uniquePart.toString()
				+ checkDigit.toString();
	}

	public Attr toXML(Document doc) {
		Attr attr = doc.createAttribute(getLabel());

		attr.setValue(toString());
		return attr;
	}

	private boolean checkCheckDigit(String toCheck, int checkDigit) {
		int total = numericValue(toCheck, 0) * 3 + numericValue(toCheck, 1) * 5
				+ numericValue(toCheck, 2) * 7 + numericValue(toCheck, 3) * 13
				+ numericValue(toCheck, 4) * 17 + numericValue(toCheck, 5) * 19
				+ numericValue(toCheck, 6) * 23 + numericValue(toCheck, 7) * 29
				+ numericValue(toCheck, 8) * 31 + numericValue(toCheck, 9) * 37
				+ numericValue(toCheck, 10) * 41 + numericValue(toCheck, 11)
				* 43;
		return total % 11 % 10 == checkDigit;
	}

	private int numericValue(String str, int position) {
		return Character.getNumericValue(str.charAt(position));
	}

	public Dso getDso() throws ProgrammerException, UserException {
		return Dso.getDso(dsoCode);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof MpanCoreRaw) {
			MpanCoreRaw core = (MpanCoreRaw) obj;
			isEqual = getDsoCode().equals(core.getDsoCode())
					&& getUniquePart().equals(core.getUniquePart())
					&& getCheckDigit().equals(core.getCheckDigit());
		}
		return isEqual;
	}

	public int hashCode() {
		return dsoCode.hashCode() + uniquePart.hashCode()
				+ checkDigit.hashCode();
	}
}