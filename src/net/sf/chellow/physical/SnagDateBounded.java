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

import java.util.List;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class SnagDateBounded extends Snag {

	private HhEndDate startDate;

	private HhEndDate finishDate;

	public SnagDateBounded() {
	}

	public SnagDateBounded(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		super(description);
		update(startDate, finishDate);
	}

	public HhEndDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhEndDate startDate) {
		this.startDate = startDate;
		if (startDate != null) {
			startDate.setLabel("start");
		}
	}

	public HhEndDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhEndDate finishDate) {
		this.finishDate = finishDate;
		if (finishDate != null) {
			finishDate.setLabel("finish");
		}
	}

	public void update() {
	}

	public void updateStartDate(HhEndDate startDate) throws InternalException {
		update(startDate, finishDate);
	}

	public void updateFinishDate(HhEndDate finishDate) throws InternalException {
		update(startDate, finishDate);
	}

	public void update(HhEndDate startDate, HhEndDate finishDate)
			throws InternalException {
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new InternalException(
					"Start date can't be after finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
	}

	public Element toXml(Document doc, String elementName) throws HttpException {
		Element element = super.toXml(doc, elementName);

		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			element.appendChild(finishDate.toXml(doc));
		}
		return element;
	}

	public SnagDateBounded copy() throws InternalException {
		SnagDateBounded cloned;
		try {
			cloned = (SnagDateBounded) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return "Start date: " + startDate + " Finish date: " + finishDate;
	}

	private static void addSnagDateBounded(SnagToAdd snagToAdd)
			throws HttpException {
		SnagDateBounded background = snagToAdd.newSnag();
		for (SnagDateBounded snag : snagToAdd.getCoveredSnags()) {
			//Debug.print("snag in covered snag is : " + snag.toString());
			if (HhEndDate.isAfter(snag.getFinishDate(), snagToAdd
					.getFinishDate())) {
				SnagDateBounded outerSnag = snag.copy();
				outerSnag.setStartDate(snagToAdd.getFinishDate().getNext());
				snag.setFinishDate(snagToAdd.getFinishDate());
				snagToAdd.insertSnag(outerSnag);
				Hiber.flush();
			}
			if (snag.getStartDate().before(snagToAdd.getStartDate())) {
				SnagDateBounded outerSnag = snag.copy();
				outerSnag.setFinishDate(snagToAdd.getStartDate().getPrevious());
				snag.setStartDate(snagToAdd.getStartDate());
				snagToAdd.insertSnag(outerSnag);
				Hiber.flush();
				if (snag.getFinishDate() == null) {
					background = null;
				}
				if (background != null) {
					background.setFinishDate(snag.getFinishDate().getNext());
					background.setStartDate(snag.getFinishDate().getNext());
				}
			}
			if (background != null) {
				if (background.getStartDate().before(snag.getStartDate())) {
					background.setFinishDate(snag.getStartDate().getPrevious());
					snagToAdd.insertSnag(background);
					if (snag.getFinishDate() == null) {
						background = null;
					} else {
						background = snagToAdd.newSnag(snag.getFinishDate()
								.getNext(), snag.getFinishDate().getNext());
					}
				} else if (snag.getFinishDate() == null) {
					background = null;
				} else {
					background.setFinishDate(snag.getFinishDate().getNext());
					background.setStartDate(snag.getFinishDate().getNext());
				}
			}
		}
		if (background != null
				&& !background.getStartDate().after(snagToAdd.getFinishDate())) {
			background.setFinishDate(snagToAdd.getFinishDate());
			snagToAdd.insertSnag(background);
		}
		SnagDateBounded previousSnag = null;
		for (SnagDateBounded snag : snagToAdd.getCoveredSnags(snagToAdd
				.getStartDate().getPrevious(),
				snagToAdd.getFinishDate() == null ? null : snagToAdd
						.getFinishDate().getNext())) {
			boolean combinable = false;
			if (previousSnag != null) {
				combinable = previousSnag.isCombinable(snag);
				if (combinable) {
					previousSnag.updateFinishDate(snag.getFinishDate());
					snagToAdd.deleteSnag(snag);
				}
			}
			if (!combinable) {
				previousSnag = snag;
			}
		}
	}

	private static void deleteSnagDateBounded(SnagToAdd snagToDelete)
			throws HttpException {
		for (SnagDateBounded snag : snagToDelete.getCoveredSnags()) {
			//Debug.print("snag " + snag.toString());
			//Debug.print("snagToDelete " + snagToDelete.toString());
			boolean outLeft = snag.getStartDate().before(
					snagToDelete.getStartDate());
			//Debug.print("Outleft " + outLeft);
			boolean outRight = HhEndDate.isAfter(snag.getFinishDate(),
					snagToDelete.getFinishDate());
			//Debug.print("Outright " + outRight);
			if (outLeft && outRight) {
				//Debug.print("Outright && outleft");
				SnagDateBounded outerSnag = snag.copy();
				snag.setFinishDate(snagToDelete.getStartDate().getPrevious());
				outerSnag.setStartDate(snagToDelete.getFinishDate().getNext());
				snagToDelete.insertSnag(outerSnag);
				//Debug.print("snag is " + snag);
				//Debug.print("outer snag" + outerSnag);
			} else if (outLeft) {
				snag.setFinishDate(snagToDelete.getStartDate().getPrevious());
			} else if (outRight) {
				snag.setStartDate(snagToDelete.getFinishDate().getNext());
			} else {
				snagToDelete.deleteSnag(snag);
			}
			Hiber.flush();
		}
	}

	public static void deleteSupplySnag(Supply supply, Contract contract,
			String description, HhEndDate startDate, HhEndDate finishDate)
			throws HttpException {
		deleteSnagDateBounded(new SupplySnagToAdd(supply, contract,
				description, startDate, finishDate));
	}

	public static void deleteChannelSnag(Channel channel, String description,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		deleteSnagDateBounded(new ChannelSnagToAdd(channel, description,
				startDate, finishDate));
	}

	public static void deleteSiteSnag(Site site, String description,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		deleteSnagDateBounded(new SiteSnagToAdd(site, description, startDate,
				finishDate));
	}

	public static void addChannelSnag(Channel channel, String description,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		addSnagDateBounded(new ChannelSnagToAdd(channel, description,
				startDate, finishDate));
	}

	public static void addSiteSnag(Site site, String description,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		addSnagDateBounded(new SiteSnagToAdd(site, description, startDate,
				finishDate));
	}

	public static void addSupplySnag(Supply supply, Contract contract,
			String description, HhEndDate startDate, HhEndDate finishDate)
			throws HttpException {
		addSnagDateBounded(new SupplySnagToAdd(supply, contract, description,
				startDate, finishDate));
	}

	private static interface SnagToAdd {
		public List<? extends SnagDateBounded> getCoveredSnags();

		public List<? extends SnagDateBounded> getCoveredSnags(
				HhEndDate startDate, HhEndDate finishDate);

		public SnagDateBounded newSnag() throws InternalException,
				HttpException;

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws InternalException, HttpException;

		public HhEndDate getStartDate();

		public HhEndDate getFinishDate();

		public void insertSnag(SnagDateBounded snag);

		public void deleteSnag(SnagDateBounded snag);
	}

	private static class ChannelSnagToAdd implements SnagToAdd {
		private Channel channel;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		public ChannelSnagToAdd(Channel channel, String description,
				HhEndDate startDate, HhEndDate finishDate) {
			this.channel = channel;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
		}

		public HhEndDate getFinishDate() {
			return finishDate;
		}

		public SnagDateBounded newSnag() throws HttpException {
			return new ChannelSnag(description, channel, startDate, finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			ChannelSnag channelSnag = (ChannelSnag) snag;
			ChannelSnag.insertChannelSnag(channelSnag);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws HttpException {
			return new ChannelSnag(description, channel, startDate, finishDate);
		}

		public void deleteSnag(SnagDateBounded snag) {
			ChannelSnag channelSnag = (ChannelSnag) snag;
			ChannelSnag.deleteChannelSnag(channelSnag);
		}

		public List<ChannelSnag> getCoveredSnags() {
			return getCoveredSnags(startDate, finishDate);
		}

		@SuppressWarnings("unchecked")
		public List<ChannelSnag> getCoveredSnags(HhEndDate startDate,
				HhEndDate finishDate) {
			Query query = null;
			if (finishDate == null) {
				query = Hiber
						.session()
						.createQuery(
								"from ChannelSnag snag where snag.channel = :channel and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.description = :description order by snag.startDate.date");
			} else {
				query = Hiber
						.session()
						.createQuery(
								"from ChannelSnag snag where snag.channel = :channel and snag.startDate.date <= :finishDate and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.description = :description order by snag.startDate.date")
						.setTimestamp("finishDate", finishDate.getDate());
			}
			return (List<ChannelSnag>) query.setTimestamp("startDate",
					startDate.getDate()).setEntity("channel", channel)
					.setString("description", description).list();
		}
	}

	private static class SiteSnagToAdd implements SnagToAdd {
		private Site site;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		private Query query;

		public SiteSnagToAdd(Site site, String description,
				HhEndDate startDate, HhEndDate finishDate) {
			this.site = site;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
			query = Hiber
					.session()
					.createQuery(
							"from SiteSnag snag where snag.site = :site and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.description = :description order by snag.startDate.date")
					.setEntity("site", site).setString("description",
							description.toString());
		}

		public HhEndDate getFinishDate() {
			return finishDate;
		}

		public SnagDateBounded newSnag() throws HttpException {
			return new SiteSnag(description, site, startDate, finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			SiteSnag snagSite = (SiteSnag) snag;
			SiteSnag.insertSiteSnag(snagSite);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws HttpException {
			return new SiteSnag(description, site, startDate, finishDate);
		}

		public void deleteSnag(SnagDateBounded snag) {
			SiteSnag snagSite = (SiteSnag) snag;
			snagSite.delete();
		}

		public List<SiteSnag> getCoveredSnags() {
			return getCoveredSnags(startDate, finishDate);
		}

		@SuppressWarnings("unchecked")
		public List<SiteSnag> getCoveredSnags(HhEndDate startDate,
				HhEndDate finishDate) {
			return (List<SiteSnag>) query.setTimestamp("finishDate",
					finishDate.getDate()).setTimestamp("startDate",
					startDate.getDate()).list();
		}
	}

	private static class SupplySnagToAdd implements SnagToAdd {
		private Supply supply;

		private Contract contract;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		public SupplySnagToAdd(Supply supply, Contract contract,
				String description, HhEndDate startDate, HhEndDate finishDate) {
			this.supply = supply;
			this.contract = contract;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
		}

		public HhEndDate getFinishDate() {
			return finishDate;
		}

		public SnagDateBounded newSnag() throws HttpException {
			return new SupplySnag(supply, contract, description, startDate,
					finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			SupplySnag supplySnag = (SupplySnag) snag;
			SupplySnag.insertSupplySnag(supplySnag);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws HttpException {
			return new SupplySnag(supply, contract, description, startDate,
					finishDate);
		}

		public void deleteSnag(SnagDateBounded snag) {
			SupplySnag.deleteAccountSnag((SupplySnag) snag);
		}

		public List<SupplySnag> getCoveredSnags() {
			return getCoveredSnags(startDate, finishDate);
		}

		@SuppressWarnings("unchecked")
		public List<SupplySnag> getCoveredSnags(HhEndDate startDate,
				HhEndDate finishDate) {
			//Debug.print("Getting covered snags.");
			Query query = null;
			if (finishDate == null) {
				//Debug.print("finish date is null");
				query = Hiber
						.session()
						.createQuery(
								"from SupplySnag snag where snag.supply = :supply and snag.contract = :contract and snag.description = :description and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) order by snag.startDate.date");
			} else {
			    //Debug.print("finish date isn't null, in fact it's " + finishDate + " supply is " + supply + " contract " + contract);
				query = Hiber
						.session()
						.createQuery(
								"from SupplySnag snag where snag.supply = :supply and snag.contract = :contract and snag.description = :description and (snag.finishDate.date is null or snag.finishDate.date >= :startDate) and snag.startDate.date <= :finishDate order by snag.startDate.date")
						.setTimestamp("finishDate", finishDate.getDate());
			}
			//Debug.print(" list size " + query.setEntity("supply", supply)
			//		.setEntity("contract", contract).setString("description",
			//				description).setTimestamp("startDate",
			//				startDate.getDate()).list().size());
			return (List<SupplySnag>) query.setEntity("supply", supply)
					.setEntity("contract", contract).setString("description",
							description).setTimestamp("startDate",
							startDate.getDate()).list();
		}

		public String toString() {
			return "Account " + supply.getId() + " description " + description
					+ " start " + startDate + " finish " + finishDate;
		}
	}

	protected boolean isCombinable(SnagDateBounded snag) throws HttpException {
		return snag.getStartDate().getPrevious().equals(getFinishDate())
				&& getIsIgnored() == snag.getIsIgnored();
	}
}
