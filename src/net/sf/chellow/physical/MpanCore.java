/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.billing.Dso;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.NotFoundException;
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
			throw new NotFoundException("There isn't an MPAN with the core "
					+ core);
		}
		return mpanCore;

	}
	
	static public MpanCore findMpanCore(String core) throws HttpException {
		MpanCoreRaw raw = new MpanCoreRaw(core);
		return (MpanCore) Hiber
		.session()
		.createQuery(
				"from MpanCore mpanCore where mpanCore.dso = :dso and mpanCore.uniquePart = :uniquePart")
		.setEntity("dso", raw.getDso()).setString("uniquePart",
				raw.getUniquePart()).uniqueResult();
	}

	/*
	 * static public MpanCore getMpanCore(MonadLong id) throws
	 * ProgrammerException { return getMpanCore(id.getLong()); }
	 */
	private Supply supply;

	private Dso dso;

	private String uniquePart;

	private char checkDigit;

	// private Set<Mpan> mpans;

	public MpanCore() {
	}

	public MpanCore(Supply supply, String core) throws HttpException {
		setSupply(supply);
		// setMpans(new HashSet<Mpan>());
		update(core);
	}

	/*
	 * public MpanCore(Dso dso, MpanUniquePart uniquePart, CheckDigit
	 * checkDigit) throws HttpException { init(dso, uniquePart, checkDigit); }
	 */

	public void update(String core) throws HttpException {
		MpanCoreRaw coreRaw = new MpanCoreRaw(core);
		this.dso = coreRaw.getDso();
		this.uniquePart = coreRaw.getUniquePart();
		this.checkDigit = coreRaw.getCheckDigit();
	}

	public Supply getSupply() {
		return supply;
	}

	protected void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Dso getDso() {
		return dso;
	}

	protected void setDso(Dso dso) {
		this.dso = dso;
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
		return new MpanCoreRaw(dso.getCode() + uniquePart
				+ checkDigit);
	}

	/*
	 * public Set<Mpan> getMpans() { return mpans; }
	 * 
	 * void setMpans(Set<Mpan> mpans) { this.mpans = mpans; }
	 */
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
			return new MpanCoreRaw(dso.getCode() + uniquePart + checkDigit)
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

	public MonadUri getUri() {
		return null;
	}

	public void httpGet(Invocation inv) throws HttpException {
		throw new MethodNotAllowedException();
	}
	

	static public class MpanCoreRaw {
		private Dso dso;

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

		private void init(String dsoCode, String uniquePart, char checkDigit)
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
			if (!checkCheckDigit(dsoCode.toString() + uniquePart.toString(),
					Character.getNumericValue(checkDigit))) {

				throw new UserException(
						"This is not a valid MPAN core. It fails the checksum test.");
			}
			this.dso = Dso.getDso(dsoCode);
			this.uniquePart = uniquePart;
			this.checkDigit = checkDigit;
		}

		/*
		 * public MpanCoreRaw(String dsoCode, MpanUniquePart uniquePart, CheckDigit
		 * checkDigit) throws HttpException { init(dsoCode, uniquePart, checkDigit); }
		 */
		public Dso getDso() {
			return dso;
		}

		public String getUniquePart() {
			return uniquePart;
		}

		public char getCheckDigit() {
			return checkDigit;
		}

		public String toString() {
			return dso.getCode() + " " + uniquePart.toString().substring(0, 4)
					+ " " + uniquePart.toString().substring(4, 8) + " "
					+ uniquePart.toString().substring(8)
					+ checkDigit;
		}

		public String toStringNoSpaces() {
			return dso.getCode() + uniquePart.toString() + checkDigit;
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
				isEqual = getDso().equals(core.getDso())
						&& getUniquePart().equals(core.getUniquePart())
						&& getCheckDigit() == core.getCheckDigit();
			}
			return isEqual;
		}

		public int hashCode() {
			return dso.hashCode() + uniquePart.hashCode();
		}
	}
}