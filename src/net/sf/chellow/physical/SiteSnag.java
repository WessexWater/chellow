/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.NotFoundException;

public class SiteSnag extends SnagDateBounded {
	public static void insertSiteSnag(SiteSnag snag) {
		Hiber.session().save(snag);
	}

	public static SiteSnag getSiteSnag(Long id) throws HttpException {
		SiteSnag snag = (SiteSnag) Hiber.session().get(SiteSnag.class, id);

		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	private Site site;

	public SiteSnag() {
	}

	public SiteSnag(String description, Site site, HhStartDate startDate,
			HhStartDate finishDate) throws HttpException {
		super(description, startDate, finishDate);
		this.site = site;
	}

	public Site getSite() {
		return site;
	}

	void setSite(Site site) {
		this.site = site;
	}

	public SiteSnag copy() throws InternalException {
		SiteSnag cloned;
		try {
			cloned = (SiteSnag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}
}
