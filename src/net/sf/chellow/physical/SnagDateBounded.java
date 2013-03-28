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

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;

import org.hibernate.Query;

public abstract class SnagDateBounded extends Snag {

	private HhStartDate startDate;

	private HhStartDate finishDate;

	public SnagDateBounded() {
	}

	public SnagDateBounded(String description, HhStartDate startDate,
			HhStartDate finishDate) throws HttpException {
		super(description);
		update(startDate, finishDate);
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
		if (startDate != null) {
			startDate.setLabel("start");
		}
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
		if (finishDate != null) {
			finishDate.setLabel("finish");
		}
	}

	public void update() {
	}

	public void updateStartDate(HhStartDate startDate) throws InternalException {
		update(startDate, finishDate);
	}

	public void updateFinishDate(HhStartDate finishDate) throws InternalException {
		update(startDate, finishDate);
	}

	public void update(HhStartDate startDate, HhStartDate finishDate)
			throws InternalException {
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new InternalException(
					"Start date can't be after finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
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


	private static void deleteSnagDateBounded(SnagToAdd snagToDelete)
			throws HttpException {
		for (SnagDateBounded snag : snagToDelete.getCoveredSnags()) {
			//Debug.print("snag " + snag.toString());
			//Debug.print("snagToDelete " + snagToDelete.toString());
			boolean outLeft = snag.getStartDate().before(
					snagToDelete.getStartDate());
			//Debug.print("Outleft " + outLeft);
			boolean outRight = HhStartDate.isAfter(snag.getFinishDate(),
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

	public static void deleteChannelSnag(Channel channel, String description,
			HhStartDate startDate, HhStartDate finishDate) throws HttpException {
		deleteSnagDateBounded(new ChannelSnagToAdd(channel, description,
				startDate, finishDate));
	}


	
	private static interface SnagToAdd {
		public List<? extends SnagDateBounded> getCoveredSnags();

		public List<? extends SnagDateBounded> getCoveredSnags(
				HhStartDate startDate, HhStartDate finishDate);

		public SnagDateBounded newSnag() throws InternalException,
				HttpException;

		public SnagDateBounded newSnag(HhStartDate startDate, HhStartDate finishDate)
				throws InternalException, HttpException;

		public HhStartDate getStartDate();

		public HhStartDate getFinishDate();

		public void insertSnag(SnagDateBounded snag);

		public void deleteSnag(SnagDateBounded snag);
	}

	private static class ChannelSnagToAdd implements SnagToAdd {
		private Channel channel;

		private String description;

		private HhStartDate startDate;

		private HhStartDate finishDate;

		public ChannelSnagToAdd(Channel channel, String description,
				HhStartDate startDate, HhStartDate finishDate) {
			this.channel = channel;
			this.description = description;
			this.startDate = startDate;
			this.finishDate = finishDate;
		}

		public HhStartDate getFinishDate() {
			return finishDate;
		}

		public SnagDateBounded newSnag() throws HttpException {
			return new ChannelSnag(description, channel, startDate, finishDate);
		}

		public void insertSnag(SnagDateBounded snag) {
			ChannelSnag channelSnag = (ChannelSnag) snag;
			ChannelSnag.insertChannelSnag(channelSnag);
		}

		public HhStartDate getStartDate() {
			return startDate;
		}

		public SnagDateBounded newSnag(HhStartDate startDate, HhStartDate finishDate)
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
		public List<ChannelSnag> getCoveredSnags(HhStartDate startDate,
				HhStartDate finishDate) {
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
}
