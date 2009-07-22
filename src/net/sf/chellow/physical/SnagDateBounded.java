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

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.AccountSnag;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;

import org.hibernate.Query;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class SnagDateBounded extends Snag {

	private HhEndDate startDate;

	private HhEndDate finishDate;

	public SnagDateBounded() {
	}

	public SnagDateBounded(String description, HhEndDate startDate,
			HhEndDate finishDate) throws InternalException, HttpException {
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
			if (snag.getFinishDate().getDate().after(
					snagToAdd.getFinishDate().getDate())) {
				SnagDateBounded outerSnag = snag.copy();
				outerSnag.setStartDate(HhEndDate.getNext(snagToAdd
						.getFinishDate()));
				snag.setFinishDate(snagToAdd.getFinishDate());
				snagToAdd.insertSnag(outerSnag);
				Hiber.flush();
			}
			if (snag.getStartDate().getDate().before(
					snagToAdd.getStartDate().getDate())) {
				SnagDateBounded outerSnag = snag.copy();
				outerSnag.setFinishDate(HhEndDate.getPrevious(snagToAdd
						.getStartDate()));
				snag.setStartDate(snagToAdd.getStartDate());
				snagToAdd.insertSnag(outerSnag);
				Hiber.flush();
				background.setFinishDate(HhEndDate
						.getNext(snag.getFinishDate()));
				background
						.setStartDate(HhEndDate.getNext(snag.getFinishDate()));
			}
			if (background.getStartDate().getDate().before(
					snag.getStartDate().getDate())) {
				background.setFinishDate(snag.getStartDate().getPrevious());
				snagToAdd.insertSnag(background);
				background = snagToAdd.newSnag(snag.getFinishDate().getNext(),
						snag.getFinishDate().getNext());
			} else {
				background.setFinishDate(snag.getFinishDate().getNext());
				background.setStartDate(snag.getFinishDate().getNext());
			}
		}
		if (!background.getStartDate().after(snagToAdd.getFinishDate())) {
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

	private static void deleteSnagDateBounded(SnagToAdd snagToAdd)
			throws HttpException {
		for (SnagDateBounded snag : snagToAdd.getCoveredSnags()) {
			boolean outLeft = snag.getStartDate().getDate().before(
					snagToAdd.getStartDate().getDate());
			boolean outRight = snag.getFinishDate().getDate().after(
					snagToAdd.getFinishDate().getDate());
			if (outLeft && outRight) {
				SnagDateBounded outerSnag = snag.copy();
				snag.setFinishDate(snagToAdd.getStartDate().getPrevious());
				outerSnag.setStartDate(snagToAdd.getFinishDate().getNext());
				snagToAdd.insertSnag(outerSnag);
			} else if (outLeft) {
				snag.setFinishDate(snagToAdd.getStartDate().getPrevious());
			} else if (outRight) {
				snag.setStartDate(snagToAdd.getFinishDate().getNext());
			} else {
				snagToAdd.deleteSnag(snag);
			}
			Hiber.flush();
		}
	}

	public static void deleteAccountSnag(Account account, String description,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		deleteSnagDateBounded(new AccountSnagToAdd(account, description,
				startDate, finishDate));
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

	public static void addAccountSnag(Account account, String description,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		addSnagDateBounded(new AccountSnagToAdd(account, description,
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
								"from ChannelSnag snag where snag.channel = :channel and snag.finishDate.date >= :startDate and snag.description = :description order by snag.startDate.date");
			} else {
				query = Hiber
						.session()
						.createQuery(
								"from ChannelSnag snag where snag.channel = :channel and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.description = :description order by snag.startDate.date")
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

	private static class AccountSnagToAdd implements SnagToAdd {
		private Account account;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		private Query query;

		public AccountSnagToAdd(Account account, String description,
				HhEndDate startDate, HhEndDate finishDate) {
			this.account = account;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
			query = Hiber
					.session()
					.createQuery(
							"from AccountSnag snag where snag.account = :account and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.description = :description order by snag.startDate.date")
					.setEntity("account", account).setString("description",
							description.toString());
		}

		public HhEndDate getFinishDate() {
			return finishDate;
		}

		public SnagDateBounded newSnag() throws HttpException {
			return new AccountSnag(description, account, startDate, finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			AccountSnag accountSnag = (AccountSnag) snag;
			AccountSnag.insertSnagAccount(accountSnag);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws HttpException {
			return new AccountSnag(description, account, startDate, finishDate);
		}

		public void deleteSnag(SnagDateBounded snag) {
			AccountSnag.deleteAccountSnag((AccountSnag) snag);
		}

		public List<AccountSnag> getCoveredSnags() {
			return getCoveredSnags(startDate, finishDate);
		}

		@SuppressWarnings("unchecked")
		public List<AccountSnag> getCoveredSnags(HhEndDate startDate,
				HhEndDate finishDate) {
			return (List<AccountSnag>) query.setTimestamp("finishDate",
					finishDate.getDate()).setTimestamp("startDate",
					startDate.getDate()).list();
		}
	}

	protected boolean isCombinable(SnagDateBounded snag) throws HttpException {
		return getFinishDate().getDate().getTime() == snag.getStartDate()
				.getPrevious().getDate().getTime()
				&& getIsIgnored() == snag.getIsIgnored();
	}
}
