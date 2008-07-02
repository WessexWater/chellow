/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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

import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Organizations implements Urlable {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("orgs");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	public static Organization insertOrganization(String name)
			throws HttpException {
		return insertOrganization(name, 0);
	}

	public static Organization insertOrganization(String name, long id)
			throws InternalException, HttpException {

		Organization organization = null;
		try {
			organization = new Organization(name);
			organization.setId(id);
			Hiber.session().save(organization);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw new UserException
						("A site with this code already exists.");
			} else {
				throw new InternalException(e);
			}
		}
		return organization;
	}

	public Organizations() {
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = (Element) doc.getFirstChild();

		for (Organization organization : getOrganizations()) {
			source.appendChild(organization.toXml(doc));
		}
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		String name = inv.getString("name");
		if (!inv.isValid()) {
			throw new UserException(doc, null);
		}
		Organization organization = insertOrganization(name);
		Hiber.commit();
		inv.sendCreated(organization.getUri());
	}

	public MonadUri getUri() throws HttpException {
			return Chellow.ROOT_URI.resolve(getUriId())
					.append("/");
	}

	public Organization getChild(UriPathElement uriId)
			throws HttpException {
		long organizationId;
		try {
			organizationId = Long.parseLong(uriId.toString());
		} catch (NumberFormatException e) {
			throw new NotFoundException();
		}
		Organization organization = (Organization) Hiber.session().createQuery(
				"from Organization as organization where "
						+ "organization.id = :organizationId").setLong(
				"organizationId", organizationId).uniqueResult();
		if (organization == null) {
			throw new NotFoundException();
		}
		return organization;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public UriPathElement getUriId() {
		return URI_ID;
	}

	@SuppressWarnings("unchecked")
	public List<Organization> getOrganizations() throws InternalException,
			HttpException {
		return (List<Organization>) Hiber.session().createQuery(
				"from Organization organization order by organization.id")
				.list();
	}
}