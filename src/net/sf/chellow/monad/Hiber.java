/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
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

package net.sf.chellow.monad;

import java.util.logging.Logger;

import org.hibernate.HibernateException;
import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.Transaction;
import org.hibernate.cfg.Configuration;

public class Hiber {
	private static SessionFactory sessionFactory;

	private static Configuration conf = new Configuration()
			.configure("hibernate/hibernate.cfg.xml");

	private static final ThreadLocal<Session> session = new ThreadLocal<Session>();

	static {
		try {

			sessionFactory = conf.buildSessionFactory();
		} catch (Throwable ex) {
			Logger.getLogger("").severe(
					"Caught error. " + ex.getClass().getName()
							+ ex.getMessage());
			throw new ExceptionInInitializerError(ex);
		}
	}

	static public void regenerateSessionFactory() {
		try {
			sessionFactory = conf.buildSessionFactory();
		} catch (Throwable ex) {
			Logger.getLogger("").severe(
					"Caught error. " + ex.getClass().getName()
							+ ex.getMessage());
			throw new ExceptionInInitializerError(ex);
		}
	}

	static public Session session() throws HibernateException {
		Session s = session.get();
		if (s == null) {
			s = sessionFactory.openSession();
			session.set(s);
		}

		Transaction tx = s.getTransaction();
		if (tx == null) {
			s.beginTransaction();
		} else if (!tx.isActive()) {
			s.beginTransaction();
		}
		
		return s;
	}

	static public void close() throws HibernateException {
		Session s = session.get();

		if (s != null) {
			Transaction tx = s.getTransaction();
			if (tx != null && tx.isActive()) {
				tx.commit();
			}
			s.close();
			session.set(null);
		}
	}

	static public void commit() throws HibernateException {
		Transaction tx = session().getTransaction();

		if (tx != null) {
			tx.commit();
		}
	}

	static public void rollBack() throws HibernateException {
		Transaction tx = session().getTransaction();
		if (tx != null) {
			tx.rollback();
		}
	}

	static public void flush() {
		session().flush();
	}

	static public Configuration getConfiguration() {
		return conf;
	}
}
