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
import java.io.UnsupportedEncodingException;
import java.net.URL;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Dso;
import net.sf.chellow.physical.DsoCode;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.physical.PersistentEntity;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import com.Ostermiller.util.CSVParser;

public class Provider extends PersistentEntity implements Urlable {
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

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Provider.class.getClassLoader();
			CSVParser parser = new CSVParser(
					new InputStreamReader(
							classLoader
									.getResource(
											"net/sf/chellow/physical/MarketParticipantRole.csv")
									.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 15
					|| !titles[0].trim().equals("Market Participant Id")
					|| !titles[1].trim().equals("Market Participant Role Code")
					|| !titles[2].trim().equals("Effective From Date {MPR}")
					|| !titles[3].trim().equals("Effective To Date {MPR}")
					|| !titles[4].trim().equals("Address Line 1")
					|| !titles[5].trim().equals("Address Line 2")
					|| !titles[6].trim().equals("Address Line 3")
					|| !titles[7].trim().equals("Address Line 4")
					|| !titles[8].trim().equals("Address Line 5")
					|| !titles[9].trim().equals("Address Line 6")
					|| !titles[10].trim().equals("Address Line 7")
					|| !titles[11].trim().equals("Address Line 8")
					|| !titles[12].trim().equals("Address Line 9")
					|| !titles[13].trim().equals("Post Code")
					|| !titles[14].trim().equals("Distributor Short Code")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "'Market Participant Id, Market Participant Role Code, Effective From Date {MPR}, Effective To Date {MPR}, Address Line 1, Address Line 2, Address Line 3, Address Line 4, Address Line 5, Address Line 6, Address Line 7, Address Line 8, Address Line 9, Post Code, Distributor Short Code'.");
			}
			SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy",
					Locale.UK);
			dateFormat.setCalendar(new GregorianCalendar(TimeZone
					.getTimeZone("GMT"), Locale.UK));
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				Participant participant = Participant.getParticipant(values[0]);
				MarketRole role = MarketRole.getMarketRole(values[1].charAt(0));
				Date validFrom = dateFormat.parse(values[2]);
				String validToStr = values[3];
				Date validTo = null;
				if (validToStr.length() != 0) {
					validTo = dateFormat.parse(values[3]);
				}
				char roleCode = role.getCode();
				if (roleCode == MarketRole.DISTRIBUTOR) {
					Dso dso = new Dso(values[4], participant, validFrom,
							validTo, new DsoCode(values[14]));
					Hiber.session().save(dso);
					Hiber.flush();
					ClassLoader dsoClassLoader = Dso.class.getClassLoader();
					DsoService dsoService;
					try {
						URL resource = dsoClassLoader
								.getResource("net/sf/chellow/billing/dso"
										+ dso.getCode().getString()
										+ "Service.py");
						if (resource != null) {
							InputStreamReader isr = new InputStreamReader(
									resource.openStream(), "UTF-8");
							StringWriter pythonString = new StringWriter();
							int c;
							while ((c = isr.read()) != -1) {
								pythonString.write(c);
							}
							dsoService = dso.insertService("main",
									new HhEndDate("2000-01-01T00:30Z"),
									pythonString.toString());
							RateScript dsoRateScript = dsoService
									.getRateScripts().iterator().next();
							isr = new InputStreamReader(classLoader
									.getResource(
											"net/sf/chellow/billing/dso"
													+ dso.getCode().getString()
													+ "ServiceRateScript.py")
									.openStream(), "UTF-8");
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
					Hiber.flush();
				}
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private String name;
	private Participant participant;
	private MarketRole role;
	private Date validFrom;
	private Date validTo;

	public Provider() {
	}

	public Provider(String name, Participant participant, char role,
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

	public Element toXml(Document doc) throws HttpException {
		String typeName = null;
		if (role.getCode() == MarketRole.DISTRIBUTOR) {
			typeName = "dso";
		} else {
			typeName = "provider";
		}
		setTypeName(typeName);
		Element element = (Element) super.toXml(doc);

		element.setAttribute("name", name);
		element.appendChild(MonadDate.toXML(validFrom, "from", doc));
		if (validTo != null) {
			element.appendChild(MonadDate.toXML(validTo, "to", doc));
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
		// TODO Auto-generated method stub
		return null;
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
		// TODO Auto-generated method stub

	}

	@Override
	public void httpPost(Invocation inv) throws HttpException {
		// TODO Auto-generated method stub

	}
}