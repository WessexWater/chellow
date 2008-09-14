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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SiteSupplyGeneration extends PersistentEntity {
	/*
	 * static public SiteSupplyGeneration getSiteSupply(MonadLong id) throws
	 * HttpException { SiteSupplyGeneration site = (SiteSupplyGeneration)
	 * Hiber.session().get( SiteSupplyGeneration.class, id.getLong()); if (site ==
	 * null) { throw new UserException("There is no site-supply with " + "that
	 * id."); } return site; }
	 */
	private Site site;

	private SupplyGeneration supplyGeneration;

	private boolean isPhysical;

	SiteSupplyGeneration() {
	}

	SiteSupplyGeneration(Site site, SupplyGeneration supplyGeneration,
			boolean isPhysical) {
		setSite(site);
		setSupplyGeneration(supplyGeneration);
		setIsPhysical(isPhysical);
	}

	public Site getSite() {
		return site;
	}

	public void setSite(Site site) {
		this.site = site;
	}

	public SupplyGeneration getSupplyGeneration() {
		return supplyGeneration;
	}

	protected void setSupplyGeneration(SupplyGeneration supplyGeneration) {
		this.supplyGeneration = supplyGeneration;
	}

	public boolean getIsPhysical() {
		return isPhysical;
	}

	protected void setIsPhysical(boolean isPhysical) {
		this.isPhysical = isPhysical;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "site-supply-generation");

		element.setAttribute("is-physical", Boolean.toString(isPhysical));
		return element;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;

		if (obj instanceof SiteSupplyGeneration) {
			isEqual = ((SiteSupplyGeneration) obj).getId().equals(getId());
		}
		return isEqual;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		throw new NotFoundException();
	}

	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}