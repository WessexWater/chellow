/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SiteSupplyGeneration extends PersistentEntity {
	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		String siteCode = GeneralImport.addField(csvElement,
				"Site Code", values, 0);
		Site site = Site.getSite(siteCode);
		String mpanCoreStr = GeneralImport.addField(csvElement, "MPAN Core", values, 1);
		MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
		String startDateStr = GeneralImport.addField(csvElement, "Generation Start Date", values, 2);
		HhStartDate startDate = new HhStartDate(startDateStr);
		SupplyGeneration supplyGeneration = mpanCore.getSupply().getGeneration(startDate);
		if (action.equals("insert")) {
			String isLocationStr = GeneralImport.addField(csvElement,
					"Is Location?", values, 3);
			boolean isLocation = Boolean.parseBoolean(isLocationStr);
			supplyGeneration.attachSite(site, isLocation);
			Hiber.flush();
		}
	}

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
