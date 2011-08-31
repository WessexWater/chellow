/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.physical;

import java.net.URI;

import net.sf.chellow.billing.Dno;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MpanCore extends PersistentEntity {
	static public MpanCore getMpanCore(Long id) throws InternalException {
		return (MpanCore) Hiber.session().get(MpanCore.class, id);
	}
	
	static public MpanCore getMpanCore(String core) throws HttpException {
		MpanCore mpanCore = findMpanCore(core);
		if (mpanCore == null) {
			throw new UserException("There isn't an MPAN with the core "
					+ core);
		}
		return mpanCore;

	}
	
	static public MpanCore findMpanCore(String core) throws HttpException {
		MpanCoreRaw raw = new MpanCoreRaw(core);
		return (MpanCore) Hiber
		.session()
		.createQuery(
				"from MpanCore mpanCore where mpanCore.dno = :dno and mpanCore.uniquePart = :uniquePart")
		.setEntity("dno", raw.getDno()).setString("uniquePart",
				raw.getUniquePart()).uniqueResult();
	}

	private Supply supply;

	private Dno dno;

	private String uniquePart;

	private char checkDigit;

	public MpanCore() {
	}

	public MpanCore(Supply supply, String core) throws HttpException {
		setSupply(supply);
		update(core);
	}

	public void update(String core) throws HttpException {
		MpanCoreRaw coreRaw = new MpanCoreRaw(core);
		this.dno = coreRaw.getDno();
		this.uniquePart = coreRaw.getUniquePart();
		this.checkDigit = coreRaw.getCheckDigit();
	}

	public Supply getSupply() {
		return supply;
	}

	protected void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Dno getDno() {
		return dno;
	}

	protected void setDno(Dno dno) {
		this.dno = dno;
	}

	public String getUniquePart() {
		return uniquePart;
	}

	protected void setUniquePart(String uniquePart) {
		this.uniquePart = uniquePart;
	}

	public char getCheckDigit() {
		return checkDigit;
	}

	protected void setCheckDigit(char checkDigit) {
		this.checkDigit = checkDigit;
	}

	public MpanCoreRaw getCore() throws HttpException {
		return new MpanCoreRaw(dno.getCode() + uniquePart
				+ checkDigit);
	}

	public boolean equals(Object object) {
		boolean isEqual = false;
		if (object instanceof MpanCore) {
			MpanCore mpan = (MpanCore) object;
			isEqual = mpan.getId().equals(getId());
		}
		return isEqual;
	}

	public String toString() {
		try {
			return new MpanCoreRaw(dno.getCode() + uniquePart + checkDigit)
					.toString();
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "mpan-core");

		element.setAttribute("uniquePart", uniquePart);
		element.setAttribute("checkDigit", Character.toString(checkDigit));
		element.setAttribute("core", toString());
		return element;
	}

	public MonadUri getEditUri() {
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
	

	static public class MpanCoreRaw {
		private Dno dno;

		private String uniquePart;

		private char checkDigit;

		public MpanCoreRaw(String mpanCore) throws HttpException {
			mpanCore = mpanCore.replace(" ", "");
			if (mpanCore.length() != 13) {
				throw new UserException("The MPAN core (" + mpanCore
						+ ") must contain exactly 13 digits.");
			}
			init(mpanCore.substring(0, 2), mpanCore.substring(2, 12), mpanCore
					.charAt(mpanCore.length() - 1));
		}

		private void init(String dnoCode, String uniquePart, char checkDigit)
				throws HttpException {
			for (char ch : uniquePart.toCharArray()) {
				if (!Character.isDigit(ch)) {
					throw new UserException(
							"Each character of an MPAN must be a digit.");
				}
			}
			if (!Character.isDigit(checkDigit)) {
				throw new UserException(
						"Each character of an MPAN must be a digit.");
			}
			if (!checkCheckDigit(dnoCode.toString() + uniquePart.toString(),
					Character.getNumericValue(checkDigit))) {

				throw new UserException(
						"This is not a valid MPAN core. It fails the checksum test.");
			}
			this.dno = Dno.getDno(dnoCode);
			this.uniquePart = uniquePart;
			this.checkDigit = checkDigit;
		}

		public Dno getDno() {
			return dno;
		}

		public String getUniquePart() {
			return uniquePart;
		}

		public char getCheckDigit() {
			return checkDigit;
		}

		public String toString() {
			return dno.getCode() + " " + uniquePart.toString().substring(0, 4)
					+ " " + uniquePart.toString().substring(4, 8) + " "
					+ uniquePart.toString().substring(8)
					+ checkDigit;
		}

		public String toStringNoSpaces() {
			return dno.getCode() + uniquePart.toString() + checkDigit;
		}

		private boolean checkCheckDigit(String toCheck, int checkDigit) {
			int[] primes = { 3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43 };
			int sum = 0;
			for (int i = 0; i < primes.length; i++) {
				sum += Character.getNumericValue(toCheck.charAt(i)) * primes[i];
			}
			return sum % 11 % 10 == checkDigit;
		}

		public boolean equals(Object obj) {
			boolean isEqual = false;

			if (obj instanceof MpanCoreRaw) {
				MpanCoreRaw core = (MpanCoreRaw) obj;
				isEqual = getDno().equals(core.getDno())
						&& getUniquePart().equals(core.getUniquePart())
						&& getCheckDigit() == core.getCheckDigit();
			}
			return isEqual;
		}

		public int hashCode() {
			return dno.hashCode() + uniquePart.hashCode();
		}
	}


	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
