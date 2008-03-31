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

import java.util.List;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.DnoService;
import net.sf.chellow.billing.DnoServices;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dso extends Provider {
	static public Dso getDso(DsoCode code) throws ProgrammerException,
			UserException {
		Dso dso = findDso(code.getString());
		if (dso == null) {
			throw UserException.newOk("There is no DSO with the code '" + code
					+ "'.");
		}
		return dso;
	}

	static public Dso findDso(String code) throws ProgrammerException,
			UserException {
		return (Dso) Hiber.session().createQuery(
				"from Dso as dso where " + "dso.code.string = :code")
				.setString("code", code).uniqueResult();
	}

	static public Dso getDso(Long id) throws ProgrammerException,
			UserException {
		Dso dso = (Dso) Hiber.session().get(Dso.class, id);
		if (dso == null) {
			throw UserException.newOk("There isn't a DSO with that id.");
		}
		return dso;
	}

	public static Dso insertDso(String name, DsoCode code)
			throws ProgrammerException, UserException, DesignerException {

		Dso dso = null;
		try {
			dso = new Dso(name, code);
			Hiber.session().save(dso);
			Hiber.flush();
		} catch (HibernateException e) {
			if (Data
					.isSQLException(e,
							"ERROR: duplicate key violates unique constraint \"site_code_key\"")) {
				throw UserException
						.newOk("A site with this code already exists.");
			} else {
				throw new ProgrammerException(e);
			}
		}
		return dso;
	}

	private DsoCode code;

	public Dso() {
	}

	public Dso(String name, DsoCode code) throws UserException,
			ProgrammerException {
		update(name, code);
	}

	void setCode(DsoCode code) {
		this.code = code;
	}

	public DsoCode getCode() {
		return code;
	}

	public void update(String name, DsoCode code) throws UserException,
			ProgrammerException {
		setCode(code);
		super.update(name);
	}

	public boolean isSettlement() {
		return Integer.parseInt(code.toString()) < 24;
	}

	/*
	 * @SuppressWarnings("unchecked") public List<LineLossFactor>
	 * getLineLossFactors(ProfileClass profileClass) { return (List<LineLossFactor>)
	 * Hiber .session() .createQuery( "from LineLossFactor lineLossFactor where
	 * lineLossFactor.dso = :dso and lineLossFactor.profileClass =
	 * :profileClass") .setEntity("dso", this).setEntity("profileClass",
	 * profileClass) .list(); }
	 * 
	 * @SuppressWarnings("unchecked") public List<LineLossFactor>
	 * getLineLossFactors() { return (List<LineLossFactor>) Hiber .session()
	 * .createQuery( "from LineLossFactor lineLossFactor where
	 * lineLossFactor.dso = :dso order by lineLossFactor.code.string")
	 * .setEntity("dso", this).list(); }
	 */
	public LineLossFactor getLineLossFactor(int code) throws UserException,
			ProgrammerException {
		LineLossFactor lineLossFactor = (LineLossFactor) Hiber
				.session()
				.createQuery(
						"from LineLossFactor llf where llf.dno = :dno and llf.code = :code")
				.setEntity("dno", this).setInteger("code", code).uniqueResult();
		if (lineLossFactor == null) {
			throw UserException
					.newInvalidParameter("There is no line loss factor with the code "
							+ code + " associated with this DNO.");
		}
		return lineLossFactor;
	}

	public String toString() {
		return "Code: " + code + " Name: " + getName();
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		setTypeName("dso");
		Element element = (Element) super.toXML(doc);

		element.setAttribute("code", code.toString());
		return element;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return Chellow.DSOS_INSTANCE.getUri().resolve(getUriId()).append("/");
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXML(doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (DnoServices.URI_ID.equals(uriId)) {
			return new DnoServices(this);
		} else if (LineLossFactors.URI_ID.equals(uriId)) {
			return new LineLossFactors(this);
		} else if (MpanTops.URI_ID.equals(uriId)) {
			return new MpanTops(this);
		} else {
			throw UserException.newNotFound();
		}
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	@Override
	public List<SupplyGeneration> supplyGenerations(Account account) {
		// TODO Auto-generated method stub
		return null;
	}

	public DnoService insertService(String name, HhEndDate startDate,
			String chargeScript) throws UserException, ProgrammerException,
			DesignerException {
		DnoService service = findService(name);
		if (service == null) {
			service = new DnoService(name, startDate, chargeScript, this);
		} else {
			throw UserException
					.newInvalidParameter("There is already a DSO service with this name.");
		}
		Hiber.session().save(service);
		Hiber.flush();
		return service;
	}

	public DnoServices servicesInstance() {
		return new DnoServices(this);
	}

	@Override
	public DnoService getService(String name) throws UserException,
			ProgrammerException {
		DnoService dsoService = findService(name);
		if (dsoService == null) {
			throw UserException.newInvalidParameter("The DSO service " + name
					+ " doesn't exist.");
		}
		return dsoService;
	}

	public DnoService findService(String name) throws UserException,
			ProgrammerException {
		return (DnoService) Hiber
				.session()
				.createQuery(
						"from DsoService service where service.provider = :provider and service.name = :serviceName")
				.setEntity("provider", this).setString("serviceName", name)
				.uniqueResult();
	}

	public LineLossFactor insertLineLossFactor(int code, String description,
			String voltageLevel, boolean isSubstation, boolean isImport)
			throws ProgrammerException, UserException {
		return LineLossFactor.insertLineLossFactor(this, code, description,
				voltageLevel, isSubstation, isImport);
	}
}