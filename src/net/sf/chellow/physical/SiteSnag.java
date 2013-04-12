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

import java.net.URI;
import java.util.List;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.Chellow;
import net.sf.chellow.ui.GeneralImport;

public class SiteSnag extends SnagDateBounded {
	
	 @SuppressWarnings("unchecked")
     public static void generalImport(String action, String[] values,
                     Element csvElement) throws HttpException {
             if (action.equals("insert")) {
                     String siteCodeStr = GeneralImport.addField(csvElement,
                                     "Site Code", values, 0);
                     Site site = Site.getSite(siteCodeStr);
                     String snagDescription = GeneralImport.addField(csvElement,
                                     "Snag Description", values, 1);
                     String startDateStr = GeneralImport.addField(csvElement,
                                     "Start Date", values, 2);
                     HhStartDate startDate = new HhStartDate(startDateStr);
                     String finishDateStr = GeneralImport.addField(csvElement,
                                     "Finish Date", values, 3);
                     HhStartDate finishDate = new HhStartDate(finishDateStr);

                     for (SiteSnag snag : (List<SiteSnag>) Hiber
                                     .session()
                                     .createQuery(
                                                     "from SiteSnag snag where snag.site = :site and snag.description = :description and snag.startDate.date <= :finishDate and (snag.finishDate is null or snag.finishDate.date >= :startDate)")
                                     .setEntity("site", site).setString("description",
                                                     snagDescription).setTimestamp("startDate",
                                                     startDate.getDate()).setTimestamp("finishDate",
                                                     finishDate.getDate()).list()) {
                             snag.setIsIgnored(true);
                     }
             } else if (action.equals("update")) {
             }
     }
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
	
	public void delete() {
        Hiber.session().delete(this);
}
	
	@Override
    public URI getViewUri() throws HttpException {
            // TODO Auto-generated method stub
            return null;
    }
	
	public Element toXml(Document doc) throws HttpException {
        Element element = super.toXml(doc, "site-snag");
        return element;
}
	
	public MonadUri getEditUri() throws HttpException {
        return Chellow.SITE_SNAGS_INSTANCE.getEditUri().resolve(getUriId()).append(
                        "/");
}
}
