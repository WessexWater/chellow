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

import net.sf.chellow.billing.Provider;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.physical.CheckDigit;
import net.sf.chellow.physical.DsoCode;
import net.sf.chellow.physical.MpanUniquePart;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

public class MpanCoreRaw extends MonadObject {
	private DsoCode dsoCode;

	private MpanUniquePart uniquePart;

	private CheckDigit checkDigit;

	public MpanCoreRaw(String mpanCore) throws HttpException {
		this(null, mpanCore);
	}

	public MpanCoreRaw(String label, String mpanCore)
			throws InternalException, HttpException {
		setLabel(label);
		mpanCore = mpanCore.replace(" ", "");
		if (mpanCore.length() != 13) {
			throw new UserException("The MPAN core (" + mpanCore
					+ ") must contain exactly 13 digits.");
		}
		init(new DsoCode(mpanCore.substring(0, 2)), new MpanUniquePart(mpanCore
				.substring(2, 12)), new CheckDigit(new Character(mpanCore
				.charAt(mpanCore.length() - 1))));
	}

	private void init(DsoCode dsoCode, MpanUniquePart uniquePart,
			CheckDigit checkDigit) throws HttpException {
		if (dsoCode == null || uniquePart == null || checkDigit == null) {
			throw new InternalException("No nulls allowed.");
		}
		if (!checkCheckDigit(dsoCode.toString() + uniquePart.toString(),
				Character
						.getNumericValue(checkDigit.getCharacter().charValue()))) {

			throw new UserException(
					"This is not a valid MPAN core. It fails the checksum test.");
		}

		this.dsoCode = dsoCode;
		this.uniquePart = uniquePart;
		this.checkDigit = checkDigit;
	}

	public MpanCoreRaw(DsoCode dsoCode, MpanUniquePart uniquePart,
			CheckDigit checkDigit) throws InternalException, HttpException {
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

	public Attr toXml(Document doc) {
		Attr attr = doc.createAttribute(getLabel());
		attr.setValue(toString());
		return attr;
	}

	private boolean checkCheckDigit(String toCheck, int checkDigit) {
		  int[] primes = {3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43};
		  int sum = 0;
		  for (int i = 0; i < primes.length; i++) {
		    sum += Character.getNumericValue(toCheck.charAt(i)) * primes[i];
		  }
		  return sum % 11 % 10 == checkDigit;
		}

	public Provider getDso() throws HttpException {
		return Provider.getDso(dsoCode);
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