/*
 
 Copyright 2008 Meniscus Systems Ltd
 
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

package net.sf.chellow.billing;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Organization;

public abstract class Contract extends Service {
	private Organization organization;

	public Contract() {
	}

	public Contract(Provider provider, Organization organization, String name,
			HhEndDate startDate, String chargeScript) throws HttpException {
		super(provider, Service.TYPE_CONTRACT, name, startDate, chargeScript);
		setOrganization(organization);
	}

	public Organization getOrganization() {
		return organization;
	}

	void setOrganization(Organization organization) {
		this.organization = organization;
	}

	public Batch insertBatch(String reference) {
		Batch batch = new Batch(this, reference);
		Hiber.session().save(batch);
		return batch;
	}

	public void internalUpdate(Provider provider, String name,
			String chargeScript) throws HttpException {
		super.internalUpdate(provider, Service.TYPE_CONTRACT, name,
				chargeScript);
	}

	public void update(String name, String chargeScript) throws HttpException {
		super.update(Service.TYPE_CONTRACT, name, chargeScript);
	}
}