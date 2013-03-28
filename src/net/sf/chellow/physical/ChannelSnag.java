/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2011 Wessex Water Services Limited
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
import net.sf.chellow.monad.NotFoundException;

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
}
