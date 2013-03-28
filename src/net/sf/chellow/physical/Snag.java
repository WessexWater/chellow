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

import java.util.Date;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.NotFoundException;

public abstract class Snag extends PersistentEntity implements Cloneable {

	static public Snag getSnag(Long id) throws InternalException, NotFoundException {
		Snag snag = (Snag) Hiber.session().get(Snag.class, id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	static public Snag getSnag(String id) throws InternalException, NotFoundException {
		return getSnag(Long.parseLong(id));
	}

	private Date dateCreated;

	private boolean isIgnored;

	private String description;

	public Snag() {
	}

	public Snag(String description) throws InternalException {
		setDateCreated(new Date());
		this.description = description;
		this.isIgnored = false;
	}

	public Date getDateCreated() {
		return dateCreated;
	}

	void setDateCreated(Date dateCreated) {
		this.dateCreated = dateCreated;
	}

	public boolean getIsIgnored() {
		return isIgnored;
	}

	public void setIsIgnored(boolean isIgnored) {
		this.isIgnored = isIgnored;
		
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public void update() {
	}

	public Snag copy() throws InternalException {
		Snag cloned;
		try {
			cloned = (Snag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}
}
