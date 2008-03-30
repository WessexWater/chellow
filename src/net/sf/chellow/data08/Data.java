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

package net.sf.chellow.data08;

import java.sql.BatchUpdateException;
import java.sql.SQLException;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.physical.Source;

import org.hibernate.HibernateException;
import org.hibernate.Session;

public class Data {
	/*
	static SiteNameDataSource siteNameDataSource;
*/
	//public final static int PAGE_SIZE = 100;

	public Data() {
	}

	static public boolean isSQLException(HibernateException e, String message) {
		boolean isSQLException = false;

		if (e.getCause() instanceof BatchUpdateException) {
			BatchUpdateException be = (BatchUpdateException) e.getCause();
			if (be.getNextException() instanceof SQLException) {
				SQLException sqle = (SQLException) be.getNextException();
				isSQLException = sqle.getMessage().equals(message);
			}
		}
		return isSQLException;
	}

	protected Session session() throws ProgrammerException {
		try {
			return Hiber.session();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}
/*
	public static void setSiteNameDataSource(
			SiteNameDataSource siteNameDataSource) {
		Data.siteNameDataSource = siteNameDataSource;
	}
*/
	/*
	public static SiteNameDataSource getSiteNameDataSource() {
		return Data.siteNameDataSource;
	}
*/
	public void deleteSource(Source source) throws ProgrammerException {
		try {
			session().delete(source);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}
/*
	public List getDsos() throws ProgrammerException {
		try {
			return session().createQuery("from Dso dso").list();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}
*/
	/*
	public List getSources() throws ProgrammerException {
		try {
			return session().createQuery("from Source source").list();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}
	*/
/*
	public List getVoltageLevels() throws ProgrammerException {
		try {
			return session().createQuery("from VoltageLevel voltageLevel")
					.list();
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}
*/
/*
	public void updateMPAN(MpanCore mpan, MpanCoreRaw core)
			throws InvalidArgumentException, MonadInstantiationException,
			ProgrammerException {
		Dso dso = Dso.getDso(core.getDsoCode());

		mpan.update(dso, core.getUniquePart(), core.getCheckDigit());
		Hiber.flush();
	}
*/
	/*
	public SupplyGeneration getSupplyGeneration(MonadLong id)
			throws ProgrammerException, UserException {
		try {
			SupplyGeneration generation = (SupplyGeneration) session().get(
					SupplyGeneration.class, id.getLong());
			if (generation == null) {
				throw UserException.newOk("There is no generation with that id.");
			}
			return generation;
		} catch (HibernateException e) {
			throw new ProgrammerException(e);
		}
	}
*/
	/*
	public void updateSite(Site site, SiteCode code)
			throws ProgrammerException, UserException {
		site.setCode(code);
		Hiber.flush();
	}
	*/
}