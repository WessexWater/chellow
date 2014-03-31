/*******************************************************************************
 * 
 *  Copyright (c) 2005 - 2014 Wessex Water Services Limited
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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Channel extends PersistentEntity {

	private Era era;

	private boolean impRelated;

	public Channel() {
	}

	public Channel(Era era, boolean impRelated) {
		this.era = era;
		this.impRelated = impRelated;
	}

	public Era getEra() {
		return era;
	}

	void setEra(Era era) {
		this.era = era;
	}

	public boolean getImpRelated() {
		return impRelated;
	}

	void setImpRelated(boolean impRelated) {
		this.impRelated = impRelated;
	}


	public void addSnag(String description, HhStartDate startDate,
			HhStartDate finishDate) throws HttpException {
		Snag.addSnag(null, this, description, startDate, finishDate);
	}

	void deleteSnag(String description, HhStartDate startDate,
			HhStartDate finishDate) throws HttpException {
		Snag.removeSnag(null, this, description, startDate, finishDate);
	}

	public void deleteSnag(String description, HhStartDate date)
			throws HttpException {
		deleteSnag(description, date, date);
	}


	@SuppressWarnings("unchecked")
	public void onEraChange() throws HttpException {
		List<Snag> snags = (List<Snag>) Hiber
				.session()
				.createQuery(
						"from Snag snag where snag.channel = :channel and snag.startDate.date < snag.channel.era.startDate.date order by snag.startDate.date")
				.setEntity("channel", this).list();
		if (!snags.isEmpty()) {
			HhStartDate startDate = snags.get(0).getStartDate();
			HhStartDate finishDate = era.getStartDate().getPrevious();
			deleteSnag(Snag.SNAG_MISSING, startDate, finishDate);
			deleteSnag(Snag.SNAG_DATA_IGNORED, startDate, finishDate);
			deleteSnag(Snag.SNAG_NEGATIVE, startDate, finishDate);
			deleteSnag(Snag.SNAG_ESTIMATED, startDate, finishDate);
		}
		if (era.getFinishDate() != null) {
			HhStartDate startDate = era.getFinishDate().getNext();
			deleteSnag(Snag.SNAG_MISSING, startDate, null);
			deleteSnag(Snag.SNAG_DATA_IGNORED, startDate, null);
			deleteSnag(Snag.SNAG_NEGATIVE, startDate, null);
			deleteSnag(Snag.SNAG_ESTIMATED, startDate, null);
		}

		// find date of first datum
		HhDatum firstDatum = (HhDatum) Hiber
				.session()
				.createQuery(
						"from HhDatum datum where datum.channel = :channel order by datum.startDate.date")
				.setEntity("channel", this).setMaxResults(1).uniqueResult();
		if (firstDatum == null) {
			addSnag(Snag.SNAG_MISSING, era.getStartDate(), era.getFinishDate());
		} else {
			if (firstDatum.getStartDate().getDate()
					.after(era.getStartDate().getDate())) {
				addSnag(Snag.SNAG_MISSING, era.getStartDate(), firstDatum
						.getStartDate().getPrevious());
			}
			HhDatum lastDatum = (HhDatum) Hiber
					.session()
					.createQuery(
							"from HhDatum datum where datum.channel = :channel order by datum.startDate.date desc")
					.setEntity("channel", this).setMaxResults(1).uniqueResult();
			if (era.getFinishDate() == null
					|| lastDatum.getStartDate().getDate()
							.before(era.getFinishDate().getDate())) {
				addSnag(Snag.SNAG_MISSING, lastDatum.getStartDate().getNext(),
						era.getFinishDate());
			}
		}
	}

	public MonadUri getEditUri() throws HttpException {
		return era.getChannelsInstance().getEditUri().resolve(getUriId())
				.append("/");
	}

	public Element toXml(Document doc) throws HttpException {
		return null;
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("era", new XmlTree("supply"))));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public HhData getHhDataInstance() {
		return new HhData(this);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (HhData.URI_ID.equals(uriId)) {
			return new HhData(this);
		} else if (ChannelSnags.URI_ID.equals(uriId)) {
			return snagsInstance();
		} else {
			return null;
		}
	}

	public ChannelSnags snagsInstance() {
		return new ChannelSnags(this);
	}
}
