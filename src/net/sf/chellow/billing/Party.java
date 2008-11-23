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
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mdd;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class Party extends PersistentEntity {
	static public Party getParty(String participantCode, char roleCode)
			throws HttpException {
		return getParty(Participant.getParticipant(participantCode), MarketRole
				.getMarketRole(roleCode));
	}

	static public Party getParty(String participantCode, String roleCode)
			throws HttpException {
		return getParty(Participant.getParticipant(participantCode), MarketRole
				.getMarketRole(roleCode));
	}

	static public Party getParty(Participant participant, MarketRole role)
			throws HttpException {
		Party party = (Party) Hiber
				.session()
				.createQuery(
						"from Party party where party.participant = :participant and party.role = :role")
				.setEntity("participant", participant).setEntity("role", role)
				.uniqueResult();
		if (party == null) {
			throw new NotFoundException();
		}
		return party;
	}

	static public void loadFromCsv(ServletContext sc) throws HttpException {
		Debug.print("Starting to add Parties.");
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
			if (roleCode == MarketRole.DISTRIBUTOR) {
				Dso dso = new Dso(values[4], participant, validFrom, validTo,
						values[14]);
				Hiber.session().save(dso);
				Hiber.close();
				ClassLoader dsoClassLoader = Provider.class.getClassLoader();
				DsoContract dsoService;
				try {
					URL resource = dsoClassLoader
							.getResource("net/sf/chellow/billing/dso"
									+ dso.getCode() + "Service.py");
					if (resource != null) {
						InputStreamReader isr = new InputStreamReader(resource
								.openStream(), "UTF-8");
						StringWriter pythonString = new StringWriter();
						int c;
						while ((c = isr.read()) != -1) {
							pythonString.write(c);
						}
						dsoService = dso.insertContract("main", new HhEndDate(
								"2000-01-01T00:30Z"), null, pythonString
								.toString(), "");
						RateScript dsoRateScript = dsoService.getRateScripts()
								.iterator().next();
						isr = new InputStreamReader(dsoClassLoader.getResource(
								"net/sf/chellow/billing/dso" + dso.getCode()
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
			} else {
				Provider provider = new Provider(values[4], participant,
						roleCode, validFrom, validTo);
				Hiber.session().save(provider);
				Hiber.close();
			}
		}
		Debug.print("Finished adding Providers.");
	}

	private String name;
	private Participant participant;
	private MarketRole role;
	private Date validFrom;
	private Date validTo;

	public Party() {
	}

	public Party(String name, Participant participant, char role,
			Date validFrom, Date validTo) throws HttpException {
		setName(name);
		setParticipant(participant);
		setRole(MarketRole.getMarketRole(role));
		setValidFrom(validFrom);
		setValidTo(validTo);
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

	public Element toXml(Document doc, String elementName) throws HttpException {
		Element element = super.toXml(doc, elementName);

		element.setAttribute("name", name);
		element.appendChild(MonadDate.toXML(validFrom, "from", doc));
		if (validTo != null) {
			element.appendChild(MonadDate.toXML(validTo, "to", doc));
		}
		return element;
	}

	public Element toXml(Document doc) throws HttpException {
		return toXml(doc, "party");
	}

	/*
	 * public Account getAccount(String accountText) throws HttpException {
	 * Account account = (Account) Hiber .session() .createQuery( "from Account
	 * account where account.provider = :provider and account.reference =
	 * :accountReference") .setEntity("provider",
	 * this).setString("accountReference", accountText.trim()).uniqueResult();
	 * if (account == null) { throw new UserException("There isn't an account
	 * for '" + getName() + "' with the reference '" + accountText + "'."); }
	 * return account; }
	 */
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
		throw new NotFoundException();
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
}