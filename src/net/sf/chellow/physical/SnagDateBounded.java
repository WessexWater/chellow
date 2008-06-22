/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import java.util.List;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.AccountSnag;
import net.sf.chellow.billing.DceService;
import net.sf.chellow.billing.Service;
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

	/*
	 * public void resolve(boolean isIgnored) throws ProgrammerException,
	 * UserException { setDateResolved(new MonadDate());
	 * setIsIgnored(isIgnored); }
	 */
	public void update() {
	}

	public void updateStartDate(HhEndDate startDate) throws InternalException {
		update(startDate, finishDate);
	}

	public void updateFinishDate(HhEndDate finishDate)
			throws InternalException {
		update(startDate, finishDate);
	}

	public void update(HhEndDate startDate, HhEndDate finishDate)
			throws InternalException {
		if (startDate.getDate().after(finishDate.getDate())) {
			throw new InternalException(
					"Start date can't be after finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		Element element = (Element) super.toXml(doc);

		element.appendChild(startDate.toXml(doc));
		element.appendChild(finishDate.toXml(doc));
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

	@SuppressWarnings("unchecked")
	private static void addSnagDateBounded(SnagToAdd snagToAdd)
			throws InternalException, HttpException {
		SnagDateBounded unresolved = snagToAdd.getIsResolved() ? null
				: snagToAdd.newSnag();
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
				if (unresolved != null) {
					unresolved.setFinishDate(HhEndDate.getNext(snag
							.getFinishDate()));
					unresolved.setStartDate(HhEndDate.getNext(snag
							.getFinishDate()));
				}
			}
			if (unresolved != null) {
				if (unresolved.getStartDate().getDate().before(
						snag.getStartDate().getDate())
						&& !snagToAdd.getIsResolved()) {
					unresolved.setFinishDate(snag.getStartDate().getPrevious());
					snagToAdd.insertSnag(unresolved);
					unresolved = snagToAdd.newSnag(snag.getFinishDate()
							.getNext(), snag.getFinishDate().getNext());
				} else {
					unresolved.setFinishDate(snag.getFinishDate().getNext());
					unresolved.setStartDate(snag.getFinishDate().getNext());
				}
			}
		}
		if (unresolved != null
				&& !unresolved.getStartDate().getDate().after(
						snagToAdd.getFinishDate().getDate())) {
			unresolved.setFinishDate(snagToAdd.getFinishDate());
			snagToAdd.insertSnag(unresolved);
		}
		for (SnagDateBounded snag : snagToAdd.getCoveredSnags()) {
			if (snagToAdd.getIsResolved()) {
				if (snag.getDateResolved() == null) {
					snag.resolve(false);
				} else if (snag.getIsIgnored() == true) {
					snag.setIsIgnored(false);
				}
			} else if (snag.getDateResolved() != null && !snag.getIsIgnored()) {
				snag.deResolve();
			}
			snag.setService(snagToAdd.getService());
		}
		SnagDateBounded previousSnag = null;
		for (SnagDateBounded snag : snagToAdd.getCoveredSnags(snagToAdd
				.getStartDate().getPrevious(), snagToAdd.getFinishDate()
				.getNext())) {
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

	public static void addChannelSnag(DceService contractDce, Channel channel,
			String description, HhEndDate startDate, HhEndDate finishDate,
			boolean isResolved) throws InternalException, HttpException {
		addSnagDateBounded(new ChannelSnagToAdd(contractDce, channel,
				description, startDate, finishDate, isResolved));
	}

	public static void addSiteSnag(DceService contractDce, Site site,
			String description, HhEndDate startDate, HhEndDate finishDate,
			boolean isResolved) throws InternalException, HttpException {
		addSnagDateBounded(new SiteSnagToAdd(contractDce, site, description,
				startDate, finishDate, isResolved));
	}

	public static void addAccountSnag(Service service, Account account,
			String description, HhEndDate startDate, HhEndDate finishDate,
			boolean isResolved) throws InternalException, HttpException {
		addSnagDateBounded(new AccountSnagToAdd(service, account, description,
				startDate, finishDate, isResolved));
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

		public boolean getIsResolved();

		public Service getService();

		public void deleteSnag(SnagDateBounded snag);
	}

	private static class ChannelSnagToAdd implements SnagToAdd {
		private DceService dceService;

		private Channel channel;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		private boolean isResolved;

		public ChannelSnagToAdd(DceService dceService, Channel channel,
				String description, HhEndDate startDate, HhEndDate finishDate,
				boolean isResolved) {
			this.dceService = dceService;
			this.channel = channel;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
			this.isResolved = isResolved;
		}

		public HhEndDate getFinishDate() {
			return finishDate;
		}

		private Query getQuery() {
			return Hiber
					.session()
					.createQuery(
							"from ChannelSnag snag where snag.channel = :channel and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.description = :description order by snag.startDate.date")
					.setEntity("channel", channel).setTimestamp("finishDate",
							finishDate.getDate()).setTimestamp("startDate",
							startDate.getDate()).setString("description",
							description);
		}

		public SnagDateBounded newSnag() throws InternalException,
				HttpException {
			return new ChannelSnag(description, dceService, channel, startDate,
					finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			ChannelSnag channelSnag = (ChannelSnag) snag;
			ChannelSnag.insertChannelSnag(channelSnag);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws InternalException, HttpException {
			return new ChannelSnag(description, dceService, channel, startDate,
					finishDate);
		}

		public boolean getIsResolved() {
			return isResolved;
		}

		public DceService getService() {
			return dceService;
		}

		public void deleteSnag(SnagDateBounded snag) {
			ChannelSnag channelSnag = (ChannelSnag) snag;
			ChannelSnag.deleteChannelSnag(channelSnag);
		}

		@SuppressWarnings("unchecked")
		public List<ChannelSnag> getCoveredSnags() {
			return getCoveredSnags(startDate, finishDate);
		}

		@SuppressWarnings("unchecked")
		public List<ChannelSnag> getCoveredSnags(HhEndDate startDate,
				HhEndDate finishDate) {
			return (List<ChannelSnag>) getQuery().setTimestamp("startDate",
					startDate.getDate()).setTimestamp("finishDate",
					finishDate.getDate()).list();
		}

	}

	private static class SiteSnagToAdd implements SnagToAdd {
		private DceService dceService;

		private Site site;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		private boolean isResolved;

		private Query query;

		public SiteSnagToAdd(DceService dceService, Site site,
				String description, HhEndDate startDate, HhEndDate finishDate,
				boolean isResolved) {
			this.dceService = dceService;
			this.site = site;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
			this.isResolved = isResolved;
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

		public SnagDateBounded newSnag() throws InternalException,
				HttpException {
			return new SiteSnag(description, dceService, site, startDate,
					finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			SiteSnag snagSite = (SiteSnag) snag;
			SiteSnag.insertSiteSnag(snagSite);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws InternalException, HttpException {
			return new SiteSnag(description, dceService, site, startDate,
					finishDate);
		}

		public boolean getIsResolved() {
			return isResolved;
		}

		public DceService getService() {
			return dceService;
		}

		public void deleteSnag(SnagDateBounded snag) {
			SiteSnag snagSite = (SiteSnag) snag;
			snagSite.delete();
		}

		@SuppressWarnings("unchecked")
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
		private Service service;

		private Account account;

		private String description;

		private HhEndDate startDate;

		private HhEndDate finishDate;

		private boolean isResolved;

		private Query query;

		public AccountSnagToAdd(Service service, Account account,
				String description, HhEndDate startDate, HhEndDate finishDate,
				boolean isResolved) {
			this.service = service;
			this.account = account;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
			this.isResolved = isResolved;
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

		public SnagDateBounded newSnag() throws InternalException,
				HttpException {
			return new AccountSnag(description, service, account, startDate,
					finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			AccountSnag accountSnag = (AccountSnag) snag;
			AccountSnag.insertSnagAccount(accountSnag);
		}

		public HhEndDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhEndDate startDate, HhEndDate finishDate)
				throws InternalException, HttpException {
			return new AccountSnag(description, service, account, startDate,
					finishDate);
		}

		public boolean getIsResolved() {
			return isResolved;
		}

		public Service getService() {
			return service;
		}

		public void deleteSnag(SnagDateBounded snag) {
			AccountSnag.deleteAccountSnag((AccountSnag) snag);
		}

		@SuppressWarnings("unchecked")
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

	public boolean isCombinable(SnagDateBounded snag)
			throws InternalException, HttpException {
		boolean combinable = getFinishDate().getDate().getTime() == snag
				.getStartDate().getPrevious().getDate().getTime()
				&& getService().equals(snag.getService());
		if (combinable) {
			combinable = snag.getProgress().equals(getProgress());
		}
		if (combinable) {
			if (getDateResolved() == null && snag.getDateResolved() == null) {
				combinable = true;
			} else if ((getDateResolved() != null && snag.getDateResolved() != null)
					&& getDateResolved().equals(snag.getDateResolved())
					&& getIsIgnored() == snag.getIsIgnored()) {
				combinable = true;
			} else {
				combinable = false;
			}
		}
		return combinable;
	}
}