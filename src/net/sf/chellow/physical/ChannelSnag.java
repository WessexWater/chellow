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

import java.net.URI;
import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class ChannelSnag extends SnagDateBounded {
	public static final long SNAG_CHECK_LEAD_TIME = 1000 * 60 * 60 * 24 * 5;

	public static final String SNAG_NEGATIVE = "Negative values";

	public static final String SNAG_ESTIMATED = "Estimated";

	public static final String SNAG_MISSING = "Missing";

	public static final String SNAG_DATA_IGNORED = "Data ignored";

	public static void insertChannelSnag(ChannelSnag snag) {
		Hiber.session().save(snag);
	}

	public static void deleteChannelSnag(ChannelSnag snag) {
		Hiber.session().delete(snag);
	}

	public static ChannelSnag getChannelSnag(Long id) throws HttpException {
		ChannelSnag snag = (ChannelSnag) Hiber.session().get(ChannelSnag.class,
				id);

		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	@SuppressWarnings("unchecked")
	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"MPAN Core", values, 0);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			String isImportStr = GeneralImport.addField(csvElement,
					"Is Import?", values, 1);
			boolean isImport = Boolean.parseBoolean(isImportStr);
			String isKwhStr = GeneralImport.addField(csvElement, "Is Kwh?",
					values, 2);
			boolean isKwh = Boolean.parseBoolean(isKwhStr);
			String snagDescription = GeneralImport.addField(csvElement,
					"Snag Description", values, 3);
			String startStr = GeneralImport.addField(csvElement, "From",
					values, 4);
			HhStartDate startDate = new HhStartDate(startStr);
			String finishStr = GeneralImport.addField(csvElement, "To", values,
					5);
			HhStartDate finishDate = null;
			if (finishStr.length() > 0) {
				finishDate = new HhStartDate(finishStr);
			}
			for (SupplyGeneration generation : mpanCore.getSupply()
					.getGenerations(startDate, finishDate)) {
				Query channelQuery = null;
				if (finishDate == null) {
					channelQuery = Hiber
							.session()
							.createQuery(
									"from ChannelSnag snag where snag.channel.supplyGeneration = :generation and snag.channel.isImport = :isImport and snag.channel.isKwh = :isKwh and snag.isIgnored is false and snag.description = :description and (snag.finishDate is null or snag.finishDate.date >= :startDate)");
				} else {
					channelQuery = Hiber
							.session()
							.createQuery(
									"from ChannelSnag snag where snag.channel.supplyGeneration = :generation and snag.channel.isImport = :isImport and snag.channel.isKwh = :isKwh and snag.isIgnored is false and snag.description = :description and snag.startDate.date <= :finishDate and (snag.finishDate is null or snag.finishDate.date >= :startDate)")
							.setTimestamp("finishDate", finishDate.getDate());
				}
				for (ChannelSnag snag : (List<ChannelSnag>) channelQuery
						.setEntity("generation", generation).setBoolean(
								"isImport", isImport)
						.setBoolean("isKwh", isKwh).setString("description",
								snagDescription).setTimestamp("startDate",
								startDate.getDate()).list()) {
					snag.setIsIgnored(true);
				}
			}
		} else if (action.equals("update")) {
		}
	}

	private Channel channel;

	public ChannelSnag() {
	}

	public ChannelSnag(String description, Channel channel,
			HhStartDate startDate, HhStartDate finishDate) throws HttpException {
		super(description, startDate, finishDate);
		this.channel = channel;
	}

	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}

	public void update() {
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "channel-snag");
		return element;
	}

	public ChannelSnag copy() throws InternalException {
		ChannelSnag cloned;
		try {
			cloned = (ChannelSnag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("channel",
				new XmlTree("supplyGeneration", new XmlTree("supply")))));
		return doc;
	}

	public MonadUri getEditUri() throws HttpException {
		return getChannel().snagsInstance().getEditUri().resolve(getUriId())
				.append("/");
	}

	protected boolean isCombinable(ChannelSnag snag) throws HttpException {
		if (!super.isCombinable(snag)) {
			return false;
		}
		return getChannel().equals(snag.getChannel());
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
