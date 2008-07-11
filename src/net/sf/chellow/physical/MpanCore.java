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

import java.util.HashSet;
import java.util.Set;

import net.sf.chellow.billing.Provider;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;


import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class MpanCore extends PersistentEntity {
	static public MpanCore getMpanCore(Long id) throws InternalException {
		try {
			return (MpanCore) Hiber.session().get(MpanCore.class, id);
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}
/*
	static public MpanCore getMpanCore(MonadLong id) throws ProgrammerException {
		return getMpanCore(id.getLong());
	}
*/
	private Supply supply;

	private Provider dso;

	private MpanUniquePart uniquePart;

	private CheckDigit checkDigit;

	private Set<Mpan> mpans;

	public MpanCore() {
	}

	public MpanCore(Supply supply, MpanCoreRaw core)
			throws 	HttpException {
		setSupply(supply);
		Provider importDso = Provider.getDso(core.getDsoCode());
		setMpans(new HashSet<Mpan>());
		init(importDso, core.getUniquePart(), core.getCheckDigit());
	}

	public MpanCore(Provider dso, MpanUniquePart uniquePart, CheckDigit checkDigit)
			throws InternalException,
			HttpException {
		init(dso, uniquePart, checkDigit);
	}

	private void init(Provider dso, MpanUniquePart uniquePart, CheckDigit checkDigit)
			throws InternalException,
			HttpException {
			update(dso, uniquePart, checkDigit);
	}

	public void update(Provider dso, MpanUniquePart uniquePart, CheckDigit checkDigit)
			throws
			InternalException, HttpException {
		new MpanCoreRaw(dso.getDsoCode(), uniquePart, checkDigit);
		this.dso = dso;
		this.uniquePart = uniquePart;
		this.checkDigit = checkDigit;
	}

	public Supply getSupply() {
		return supply;
	}

	protected void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Provider getDso() {
		return dso;
	}

	protected void setDso(Provider dso) {
		this.dso = dso;
	}

	public MpanUniquePart getUniquePart() {
		return uniquePart;
	}

	protected void setUniquePart(MpanUniquePart uniquePart) {
		uniquePart.setLabel("uniquePart");
		this.uniquePart = uniquePart;
	}

	public CheckDigit getCheckDigit() {
		return checkDigit;
	}

	protected void setCheckDigit(CheckDigit checkDigit) {
		checkDigit.setLabel("checkDigit");
		this.checkDigit = checkDigit;
	}

	public MpanCoreRaw getCore() throws HttpException {
			MpanCoreRaw core = new MpanCoreRaw(dso.getDsoCode(), uniquePart,
					checkDigit);
			core.setLabel("core");
			return core;
	}

	public Set<Mpan> getMpans() {
		return mpans;
	}

	void setMpans(Set<Mpan> mpans) {
		this.mpans = mpans;
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
			return getCore().toString();
		} catch (InternalException e) {
			throw new RuntimeException(e);
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		setTypeName("mpan-core");
		Element element = (Element) super.toXml(doc);

		element.setAttributeNode(uniquePart.toXml(doc));
		element.setAttributeNode(checkDigit.toXml(doc));
		element.setAttributeNode(getCore().toXml(doc));
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException, InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}

	public void httpPost(Invocation inv) throws InternalException, HttpException {
		// TODO Auto-generated method stub
		
	}

	public void httpDelete(Invocation inv) throws InternalException, DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub
		
	}
}