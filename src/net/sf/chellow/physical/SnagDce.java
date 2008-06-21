/*
 
 Copyright 2005 Meniscus Systems Ltd
 
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

import net.sf.chellow.billing.DceService;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;

public abstract class SnagDce extends Snag {
	static public SnagDce getSnag(Long id) throws InternalException, NotFoundException {
		SnagDce snag = (SnagDce) Hiber.session().get(SnagDce.class, id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	static public SnagDce getSnag(String id) throws InternalException, NotFoundException {
		return getSnag(Long.parseLong(id));
	}

	private DceService dceService;

	public SnagDce() {
	}

	public SnagDce(String description, DceService dceService)
			throws InternalException {
		super(description);
		this.dceService = dceService;
	}

	public DceService getDceService() {
		return dceService;
	}

	void setDceService(DceService dceService) {
		this.dceService = dceService;
	}

	public void update() {
	}

	public SnagDce copy() throws InternalException {
		SnagDce cloned;
		try {
			cloned = (SnagDce) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return "Contract: " + dceService;
	}
}