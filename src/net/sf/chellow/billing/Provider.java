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

package net.sf.chellow.billing;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.net.URL;
import java.util.Date;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.DsoCode;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.LlfcCode;
import net.sf.chellow.physical.Llfcs;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mdd;
import net.sf.chellow.physical.MpanTops;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.PersistentEntity;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Provider extends PersistentEntity implements Urlable {
	static public Provider getDso(DsoCode code) throws HttpException {
		Provider dso = findDso(code.getString());
		if (dso == null) {
			throw new UserException("There is no DSO with the code '" + code
					+ "'.");
		}
		return dso;
	}

	static public Provider findDso(String code) throws HttpException {
		return (Provider) Hiber.session().createQuery(
				"from Provider provider where provider.dsoCode.string = :code")
				.setString("code", code).uniqueResult();
	}

	static public Provider getProvider(String participantCode, char roleCode)
			throws HttpException {
		Provider provider = (Provider) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.participant.code = :participantCode and provider.role.code = :roleCode")
				.setString("participantCode", participantCode).setCharacter(
						"roleCode", roleCode).uniqueResult();
		if (provider == null) {
			throw new NotFoundException();
		}
		return provider;
	}

	static public Provider getProvider(long id) throws HttpException {
		Provider provider = (Provider) Hiber.session().get(Provider.class, id);
		if (provider == null) {
			throw new NotFoundException();
		}
		return provider;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Providers.");
		Mdd mdd = new Mdd(sc, "MarketParticipantRole", new String[] {
				"Market Participant Id", "Market Participant Role Code",
				"Effective From Date {MPR}", "Effective To Date {MPR}",
				"Address Line 1", "Address Line 2", "Address Line 3",
				"Address Line 4", "Address Line 5", "Address Line 6",
				"Address Line 7", "Address Line 8", "Address Line 9",
				"Post Code", "Distributor Short Code" });
		for (String[] values = mdd.getLine(); values != null; values = mdd
				.getLine()) {
			Participant participant = Participant.getParticipant(values[0]);
			MarketRole role = MarketRole.getMarketRole(values[1].charAt(0));
			Date validFrom = mdd.toDate(values[2]);
			Date validTo = mdd.toDate(values[3]);
			char roleCode = role.getCode();
			DsoCode dsoCode = roleCode == MarketRole.DISTRIBUTOR ? new DsoCode(
					values[14]) : null;
			Provider provider = new Provider(values[4], participant, roleCode,
					validFrom, validTo, dsoCode);
			Hiber.session().save(provider);
			Hiber.close();
			if (roleCode == MarketRole.DISTRIBUTOR) {
				ClassLoader dsoClassLoader = Provider.class.getClassLoader();
				DsoService dsoService;
				try {
					URL resource = dsoClassLoader
							.getResource("net/sf/chellow/billing/dso"
									+ provider.getDsoCode().getString()
									+ "Service.py");
					if (resource != null) {
						InputStreamReader isr = new InputStreamReader(resource
								.openStream(), "UTF-8");
						StringWriter pythonString = new StringWriter();
						int c;
						while ((c = isr.read()) != -1) {
							pythonString.write(c);
						}
						dsoService = provider.insertDsoService("main",
								new HhEndDate("2000-01-01T00:30Z"),
								pythonString.toString());
						RateScript dsoRateScript = dsoService.getRateScripts()
								.iterator().next();
						isr = new InputStreamReader(dsoClassLoader.getResource(
								"net/sf/chellow/billing/dso"
										+ provider.getDsoCode().getString()
										+ "ServiceRateScript.py").openStream(),
								"UTF-8");
						pythonString = new StringWriter();
						while ((c = isr.read()) != -1) {
							pythonString.write(c);
						}
						dsoRateScript.update(dsoRateScript.getStartDate(),
								dsoRateScript.getFinishDate(), pythonString
										.toString());
					}
				} catch (IOException e) {
					throw new InternalException(e);
				}
			}
		}
		Debug.print("Finished adding Providers.");
	}

	private String name;
	private Participant participant;
	private MarketRole role;
	private Date validFrom;
	private Date validTo;
	private DsoCode dsoCode;

	public Provider() {
	}

	public Provider(String name, Participant participant, char role,
			Date validFrom, Date validTo, DsoCode dsoCode) throws HttpException {
		setName(name);
		setParticipant(participant);
		setRole(MarketRole.getMarketRole(role));
		setValidFrom(validFrom);
		setValidTo(validTo);
		setDsoCode(dsoCode);
	}

	public String getName() {
		return name;
	}

	void setName(String name) {
		this.name = name;
	}

	public Participant getParticipant() {
		return participant;
	}

	void setParticipant(Participant participant) {
		this.participant = participant;
	}

	public MarketRole getRole() {
		return role;
	}

	void setRole(MarketRole role) {
		this.role = role;
	}

	public Date getValidFrom() {
		return validFrom;
	}

	void setValidFrom(Date from) {
		this.validFrom = from;
	}

	public Date getValidTo() {
		return validTo;
	}

	void setValidTo(Date to) {
		this.validTo = to;
	}

	void setDsoCode(DsoCode dsoCode) {
		this.dsoCode = dsoCode;
	}

	public DsoCode getDsoCode() {
		return dsoCode;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "provider");

		element.setAttribute("name", name);
		element.appendChild(MonadDate.toXML(validFrom, "from", doc));
		if (validTo != null) {
			element.appendChild(MonadDate.toXML(validTo, "to", doc));
		}
		if (dsoCode != null) {
			element.setAttribute("dso-code", dsoCode.toString());
		}
		return element;
	}

	public Account getAccount(String accountText) throws HttpException {
		Account account = (Account) Hiber
				.session()
				.createQuery(
						"from Account account where account.provider = :provider and account.reference = :accountReference")
				.setEntity("provider", this).setString("accountReference",
						accountText.trim()).uniqueResult();
		if (account == null) {
			throw new UserException("There isn't an account for '" + getName()
					+ "' with the reference '" + accountText + "'.");
		}
		return account;
	}

	@SuppressWarnings("unchecked")
	/*
	 * abstract public List<SupplyGeneration> supplyGenerations(Account
	 * account);
	 * 
	 * public abstract Service getService(String name) throws HttpException,
	 * InternalException;
	 */
	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Llfcs.URI_ID.equals(uriId)) {
			return new Llfcs(this);
		} else if (MpanTops.URI_ID.equals(uriId)) {
			return new MpanTops(this);
		} else {
			throw new NotFoundException();
		}
	}

	@Override
	public MonadUri getUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void httpDelete(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("participant").put("role")));
		inv.sendOk(doc);
	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}

	public DsoService findDsoService(String name) throws HttpException,
			InternalException {
		return (DsoService) Hiber
				.session()
				.createQuery(
						"from DsoService service where service.provider = :provider and service.name = :serviceName")
				.setEntity("provider", this).setString("serviceName", name)
				.uniqueResult();
	}

	public DsoService insertDsoService(String name, HhEndDate startDate,
			String chargeScript) throws HttpException {
		DsoService service = findDsoService(name);
		if (service == null) {
			service = new DsoService(this, name, startDate, chargeScript);
		} else {
			throw new UserException(
					"There is already a DSO service with this name.");
		}
		Hiber.session().save(service);
		Hiber.flush();
		return service;
	}

	public DsoServices dsoServicesInstance() {
		return new DsoServices(this);
	}

	public Llfc getLlfc(LlfcCode code) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validTo is null")
				.setEntity("dso", this).setInteger("code", code.getInteger())
				.uniqueResult();
		if (llfc == null) {
			throw new UserException("There is no ongoing LLFC with the code "
					+ code + " associated with this DNO.");
		}
		return llfc;
	}

	public Llfc getLlfc(LlfcCode code, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dso", this).setInteger("code", code.getInteger())
				.setTimestamp("date", date).uniqueResult();
		if (llfc == null) {
			throw new UserException(
					"There is no line loss factor with the code " + code
							+ " associated with the DNO '"
							+ getDsoCode().toString() + "' for the date "
							+ date.toString() + ".");
		}
		return llfc;
	}
}