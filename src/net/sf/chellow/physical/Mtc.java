/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.text.DateFormat;
import java.text.ParseException;
import java.util.Date;
import java.util.Locale;

import net.sf.chellow.billing.DsoService;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.billing.RateScript;
import net.sf.chellow.data08.Data;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadBoolean;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

import com.Ostermiller.util.CSVParser;

public class Mtc extends PersistentEntity {
	static public Mtc getMtc(Dso dso,
			MtcCode meterTimeswitchCode)
			throws InternalException, HttpException {
		return findMtc(dso, meterTimeswitchCode, true);
	}

	static public Mtc findMtc(Dso dso,
			MtcCode mtcCode, boolean throwException)
			throws InternalException, HttpException {
		dso = mtcCode.hasDso() ? dso : null;
		Mtc mtc = null;
		if (dso == null) {
			mtc = (Mtc) Hiber
					.session()
					.createQuery(
							"from Mtc as mtc where mtc.dso is null and mtc.code.integer = :mtcCode")
					.setInteger("mtcCode",
							mtcCode.getInteger()).uniqueResult();
		} else {
			mtc = (Mtc) Hiber
					.session()
					.createQuery(
							"from Mtc as mtc where mtc.dso = :dso and mtc.code.integer = :mtcCode")
					.setEntity("dso", dso).setInteger("mtcCode",
							mtcCode.getInteger()).uniqueResult();
		}
		if (throwException && mtc == null) {
			throw new UserException
					("There isn't a meter timeswitch with DSO '"
							+ (dso == null ? dso : dso.getCode())
							+ "' and Meter Timeswitch Code '"
							+ mtcCode + "'");
		}
		return mtc;
	}

	static public Mtc getMtc(Long id) throws HttpException {
		Mtc mtc = (Mtc) Hiber.session()
				.get(Mtc.class, id);
		if (mtc == null) {
			throw new UserException
					("There is no meter timeswitch with that id.");
		}
		return mtc;
	}

	static public Mtc insertMeterTimeswitch(Dso dso,
			String mtcCode, String description, boolean isUnmetered)
			throws InternalException, HttpException {
		return insertMtc(dso, new MtcCode(mtcCode),
				description, isUnmetered);
	}

	static public Mtc insertMtc(Dso dso,
			MtcCode mtcCode, String description,
			boolean isUnmetered) throws HttpException {

		Mtc mtc = null;
		try {
			mtc = new Mtc(dso, mtcCode,
					description, isUnmetered);
			Hiber.session().save(mtc);
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
		return mtc;
	}

	static public void loadFromCsv() throws HttpException {
		try {
			ClassLoader classLoader = Mtc.class.getClassLoader();
			CSVParser parser = new CSVParser(
					new InputStreamReader(
							classLoader
									.getResource(
											"net/sf/chellow/physical/MeterTimeswitchClass.csv")
									.openStream(), "UTF-8"));
			parser.setCommentStart("#;!");
			parser.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = parser.getLine();

			if (titles.length < 11
					|| !titles[0].trim().equals("Meter Timeswitch Class Id")
					|| !titles[1].trim().equals("Effective From Settlement Date {MTC}")
					|| !titles[2].trim().equals("Effective To Settlement Date {MTC}")
					|| !titles[3].trim().equals("Meter Timeswitch Class Description")
					|| !titles[4].trim().equals("MTC Common Code Indicator")
					|| !titles[5].trim().equals("MTC Related Metering System Indicator")
					|| !titles[6].trim().equals("MTC Meter Type Id")
					|| !titles[7].trim().equals("MTC Payment Type Id")
					|| !titles[8].trim().equals("MTC Communication Indicator")
					|| !titles[9].trim().equals("MTC Type Indicator")
					|| !titles[10].trim().equals("MTC TPR Count")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "Meter Timeswitch Class Id, Effective From Settlement Date {MTC}, Effective To Settlement Date {MTC}, Meter Timeswitch Class Description, MTC Common Code Indicator, MTC Related Metering System Indicator, MTC Meter Type Id, MTC Payment Type Id, MTC Communication Indicator, MTC Type Indicator, MTC TPR Count.");
			}
			DateFormat dateFormat = DateFormat.getDateTimeInstance(
					DateFormat.SHORT, DateFormat.SHORT, Locale.UK);
			for (String[] values = parser.getLine(); values != null; values = parser
					.getLine()) {
				if (values[4].equals("T")) {
				Mtc.insertMtc(null, new MtcCode(values[0]), values[3], isUnmetered)
				Participant participant = Participant.getParticipant(values[0]);
				MarketRole role = MarketRole.getMarketRole(values[1].charAt(0));
				Date from = dateFormat.parse(values[2]);
				Date to = dateFormat.parse(values[3]);
				char roleCode = role.getCode();
				if (roleCode == MarketRole.DISTRIBUTOR) {
						Dso dso = new Dso(values[4], participant,
								from, to, new DsoCode(values[14]));
						Hiber.session().save(dso);
						Hiber.flush();
						ClassLoader dsoClassLoader = Dso.class.getClassLoader();
						DsoService dsoService;
						try {
							InputStreamReader isr = new InputStreamReader(dsoClassLoader
									.getResource(
											"net/sf/chellow/billing/dso"
													+ dso.getCode().getString() + "Service.py")
									.openStream(), "UTF-8");
							StringWriter pythonString = new StringWriter();
							int c;
							while ((c = isr.read()) != -1) {
								pythonString.write(c);
							}
							dsoService = dso.insertService("main", new HhEndDate(
									"2000-01-01T00:30Z"), pythonString.toString());
							RateScript dsoRateScript = dsoService.getRateScripts().iterator()
									.next();
							isr = new InputStreamReader(classLoader.getResource(
									"net/sf/chellow/billing/dso" + dso.getCode().getString()
											+ "ServiceRateScript.py").openStream(), "UTF-8");
							pythonString = new StringWriter();
							while ((c = isr.read()) != -1) {
								pythonString.write(c);
							}
							dsoRateScript.update(dsoRateScript.getStartDate(), dsoRateScript
									.getFinishDate(), pythonString.toString());
						} catch (IOException e) {
							throw new InternalException(e);
						}
				} else {
				Provider provider = new Provider(values[4], participant, roleCode,
						from, to);
				Hiber.session().save(provider);
				Hiber.flush();
				}}
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		} catch (ParseException e) {
			throw new InternalException(e);
		}
	}

	private Dso dso;

	private MtcCode code;

	private String description;

	private boolean isRelatedMetering;
	private MtcMeterType meterType;
	private Date from;
	private Date to;

	// private Set<LineLossFactor> lineLossFactors;

	// private Set<Ssc> registers;

	public Mtc() {
		setTypeName("meter-timeswitch");
	}

	public Mtc(Dso dso, MtcCode code,
			String description, boolean isUnmetered)
			throws InternalException, HttpException {
		this(null, dso, code, description, isUnmetered);
	}

	public Mtc(String label, Dso dso, MtcCode code,
			String description, boolean isUnmetered)
			throws InternalException, HttpException {
		this();
		boolean hasDso = code.hasDso();
		if (hasDso && dso == null) {
			throw new UserException("The MTC " + code
					+ " requires a DSO.");

		} else if (!hasDso && dso != null) {
			throw new UserException("The MTC " + code
					+ " does not have a DSO.");
		}
		setLabel(label);
		setDso(dso);
		setCode(code);
		setDescription(description);
		setIsUnmetered(isUnmetered);
	}

	void setDso(Dso dso) {
		this.dso = dso;
	}

	public Dso getDso() {
		return dso;
	}

	public MtcCode getCode() {
		return code;
	}

	void setCode(MtcCode code) {
		this.code = code;
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public boolean getIsUnmetered() {
		return isUnmetered;
	}

	void setIsUnmetered(boolean isUnmetered) {
		this.isUnmetered = isUnmetered;
	}

	/*
	 * public Set<LineLossFactor> getLineLossFactors() { return
	 * lineLossFactors; }
	 * 
	 * protected void setLineLossFactors(Set<LineLossFactor> lineLossFactors) {
	 * this.lineLossFactors = lineLossFactors; }
	 * 
	 * public Set<Ssc> getRegisters() { return registers; }
	 * 
	 * protected void setRegisters(Set<Ssc> registers) { this.registers =
	 * registers; }
	 */
	public String toString() {
		return code + " - " + description + " (DSO "
				+ (dso == null ? null : dso.getCode()) + ")";
	}

	public Node toXml(Document doc) throws InternalException, HttpException {
		Element element = (Element) super.toXml(doc);

		element.setAttributeNode(code.toXml(doc));
		element.setAttribute("description", description);
		element.setAttributeNode(MonadBoolean.toXml(doc, "is-unmetered",
				isUnmetered));
		return element;
	}

	public MonadUri getUri() {
		return null;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();

		source.appendChild(toXml(doc, new XmlTree("dso")));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}
	/*
	 * public void insertRegister(Ssc.Units units, String tprString) throws
	 * ProgrammerException, UserException { Set<Tpr> tprs = new HashSet<Tpr>();
	 * for (String tprCode : tprString.split(",")) { Tpr tpr =
	 * Tpr.getTpr(tprCode); tprs.add(tpr); } registers.add(new Ssc(this, units,
	 * tprs)); }
	 */
}