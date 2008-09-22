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

package net.sf.chellow.physical;

import net.sf.chellow.billing.Dso;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MethodNotAllowedException;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MpanCore extends PersistentEntity {
	static public MpanCore getMpanCore(Long id) throws InternalException {
		return (MpanCore) Hiber.session().get(MpanCore.class, id);
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

	public MpanCore(Supply supply, MpanCoreRaw core) throws HttpException {
		setSupply(supply);
// setMpans(new HashSet<Mpan>());
		update(core);
	}
/*
 * public MpanCore(Dso dso, MpanUniquePart uniquePart, CheckDigit checkDigit)
 * throws HttpException { init(dso, uniquePart, checkDigit); }
 */

	public void update(MpanCoreRaw core)
			throws HttpException {
		this.dso = core.getDso();
		this.uniquePart = core.getUniquePart();
		this.checkDigit = core.getCheckDigit();
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
		MpanCoreRaw core = new MpanCoreRaw(dso.getCode() + uniquePart + checkDigit);
		core.setLabel("core");
		return core;
	}
/*
	public Set<Mpan> getMpans() {
		return mpans;
	}

	void setMpans(Set<Mpan> mpans) {
		this.mpans = mpans;
	}
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
			return new MpanCoreRaw(dso.getCode() + uniquePart + checkDigit).toString();
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
}