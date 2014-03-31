/*******************************************************************************
 * 
 *  Copyright (c) 2005-2013 Wessex Water Services Limited
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

package net.sf.chellow.physical;

import java.net.URI;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.billing.Contract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Era extends PersistentEntity {


	static public Era getEra(String mpanCore, HhStartDate date) {
		if (date == null) {
			return (Era) Hiber
					.session()
					.createQuery(
							"from Era era where (era.impMpanCore = :mpanCore or era.expMpanCore = :mpanCore) and era.finishDate is null)")
					.setString("mpanCore", mpanCore).uniqueResult();
		} else {
			return (Era) Hiber
					.session()
					.createQuery(
							"from Era era where (era.impMpanCore = :mpanCore or era.expMpanCore = :mpanCore) and era.startDate.date <= :date and (era.finishDate.date >= :date or era.finishDate.date is null)")
					.setString("mpanCore", mpanCore)
					.setTimestamp("date", date.getDate()).uniqueResult();
		}
	}

	static public String normalizeMpanCore(String core) {
		core = core.replace(" ", "");
		if (core.length() != 13) {
			throw new UserException("The MPAN core (" + core
					+ ") must contain exactly 13 digits.");
		}
		for (char ch : core.toCharArray()) {
			if (!Character.isDigit(ch)) {
				throw new UserException(
						"Each character of an MPAN must be a digit.");
			}
		}

		int[] primes = { 3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43 };
		int sum = 0;
		for (int i = 0; i < primes.length; i++) {
			sum += Character.getNumericValue(core.charAt(i)) * primes[i];
		}
		int checkInt = sum % 11 % 10;
		int actualCheck = Character.getNumericValue(core.charAt(12));
		if (checkInt != actualCheck) {
			throw new UserException("The check digit is incorrect.");
		}
		return core.substring(0, 2) + " " + core.substring(2, 6) + " "
				+ core.substring(6, 10) + " " + core.substring(10, 13);
	}

	private Supply supply;

	private Set<SiteEra> siteEras;

	private Set<Channel> channels;

	private HhStartDate startDate;

	private HhStartDate finishDate;
	private Contract mopContract;
	private String mopAccount;

	private Contract hhdcContract;
	private String hhdcAccount;
	private String msn;
	private Pc pc;
	private Mtc mtc;
	private Cop cop;
	private Ssc ssc;
	private Llfc impLlfc;
	private Integer impSc;
	private Contract impSupplierContract;
	private String impSupplierAccount;
	private String impMpanCore;
	private String expMpanCore;
	private Llfc expLlfc;
	private Integer expSc;
	private Contract expSupplierContract;
	private String expSupplierAccount;

	Era() {
	}

	Era(Supply supply, HhStartDate startDate, HhStartDate finishDate,
			Contract mopContract, String mopAccount, Contract hhdcContract,
			String hhdcAccount, String msn, Pc pc, String mtcCode, Cop cop,
			Ssc ssc) throws HttpException {
		setChannels(new HashSet<Channel>());
		setSupply(supply);
		setSiteEras(new HashSet<SiteEra>());
		setPc(pc);
		Mtc anMtc = (Mtc) Hiber.session()
				.createQuery("from Mtc mtc where mtc.code = :code")
				.setString("code", mtcCode.trim()).setMaxResults(1)
				.uniqueResult();
		if (anMtc == null) {
			throw new UserException("MTC not recognized.");
		}
		setMtc(anMtc);
		setCop(cop);
		setSsc(ssc);
		setStartDate(startDate);
		setFinishDate(finishDate);
		setMopContract(mopContract);
		setMopAccount(mopAccount);
		setHhdcContract(hhdcContract);
		setHhdcAccount(hhdcAccount);
		setMsn(msn);
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Supply getSupply() {
		return supply;
	}

	public Set<SiteEra> getSiteEras() {
		return siteEras;
	}

	protected void setSiteEras(Set<SiteEra> siteEras) {
		this.siteEras = siteEras;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public Contract getMopContract() {
		return mopContract;
	}

	void setMopContract(Contract mopContract) {
		this.mopContract = mopContract;
	}

	public String getMopAccount() {
		return mopAccount;
	}

	void setMopAccount(String mopAccount) {
		this.mopAccount = mopAccount;
	}

	public Contract getHhdcContract() {
		return hhdcContract;
	}

	void setHhdcContract(Contract hhdcContract) {
		this.hhdcContract = hhdcContract;
	}

	public String getHhdcAccount() {
		return hhdcAccount;
	}

	void setHhdcAccount(String hhdcAccount) {
		this.hhdcAccount = hhdcAccount;
	}

	public Pc getPc() {
		return pc;
	}

	public String getMsn() {
		return msn;
	}

	void setMsn(String msn) {
		this.msn = msn;
	}

	void setPc(Pc pc) {
		this.pc = pc;
	}

	public Mtc getMtc() {
		return mtc;
	}

	void setMtc(Mtc mtc) {
		this.mtc = mtc;
	}

	public Cop getCop() {
		return cop;
	}

	void setCop(Cop cop) {
		this.cop = cop;
	}

	public Ssc getSsc() {
		return ssc;
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public Set<Channel> getChannels() {
		return channels;
	}

	void setChannels(Set<Channel> channels) {
		this.channels = channels;
	}

	public String getImpMpanCore() {
		return impMpanCore;
	}

	public void setImpMpanCore(String impMpanCore) {
		this.impMpanCore = impMpanCore;
	}

	public String getExpMpanCore() {
		return expMpanCore;
	}

	public void setExpMpanCore(String expMpanCore) {
		this.expMpanCore = expMpanCore;
	}

	public Llfc getImpLlfc() {
		return impLlfc;
	}

	public void setImpLlfc(Llfc impLlfc) {
		this.impLlfc = impLlfc;
	}

	public Integer getImpSc() {
		return impSc;
	}

	public void setImpSc(Integer impSc) {
		this.impSc = impSc;
	}

	public Contract getImpSupplierContract() {
		return impSupplierContract;
	}

	public void setImpSupplierContract(Contract impSupplierContract) {
		this.impSupplierContract = impSupplierContract;
	}

	public String getImpSupplierAccount() {
		return impSupplierAccount;
	}

	public void setImpSupplierAccount(String impSupplierAccount) {
		this.impSupplierAccount = impSupplierAccount;
	}

	public Llfc getExpLlfc() {
		return expLlfc;
	}

	public void setExpLlfc(Llfc expLlfc) {
		this.expLlfc = expLlfc;
	}

	public Integer getExpSc() {
		return expSc;
	}

	public void setExpSc(Integer expSc) {
		this.expSc = expSc;
	}

	public Contract getExpSupplierContract() {
		return expSupplierContract;
	}

	public void setExpSupplierContract(Contract expSupplierContract) {
		this.expSupplierContract = expSupplierContract;
	}

	public String getExpSupplierAccount() {
		return expSupplierAccount;
	}

	public void setExpSupplierAccount(String expSupplierAccount) {
		this.expSupplierAccount = expSupplierAccount;
	}

	public void attachSite(Site site) throws HttpException {
		attachSite(site, false);
	}

	public void attachSite(Site site, boolean isLocation) throws HttpException {
		boolean alreadyThere = false;
		for (SiteEra siteEra : siteEras) {
			if (siteEra.getSite().equals(site)) {
				alreadyThere = true;
				break;
			}
		}
		if (alreadyThere) {
			throw new UserException(
					"The site is already attached to this supply.");
		} else {
			SiteEra siteEra = new SiteEra(site, this, false);
			siteEras.add(siteEra);
			site.attachSiteEra(siteEra);
		}
		if (isLocation) {
			setPhysicalLocation(site);
		}
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}

	public MonadUri getEditUri() throws HttpException {
		return supply.getErasInstance().getEditUri().resolve(getUriId())
				.append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Channels.URI_ID.equals(uriId)) {
			return new Channels(this);
		} else {
			throw new NotFoundException();
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "era");
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			finishDate.setLabel("finish");
			element.appendChild(finishDate.toXml(doc));
		}
		if (hhdcAccount != null) {
			element.setAttribute("hhdc-account", hhdcAccount);
		}
		if (mopAccount != null) {
			element.setAttribute("mop-account", mopAccount);
		}
		element.setAttribute("msn", msn);
		if (impMpanCore != null) {
			element.setAttribute("imp-mpan-core", impMpanCore);
			Element supElem = impSupplierContract.toXml(doc);
			element.appendChild(supElem);
			supElem.setAttribute("is-import", Boolean.TRUE.toString());
			element.setAttribute("imp-supplier-account", impSupplierAccount);
			element.setAttribute("imp-sc", Integer.toString(impSc));
		}
		if (expMpanCore != null) {
			element.setAttribute("exp-mpan-core", expMpanCore);
			Element supElem = expSupplierContract.toXml(doc);
			element.appendChild(supElem);
			supElem.setAttribute("is-import", Boolean.FALSE.toString());
			element.setAttribute("exp-supplier-account", expSupplierAccount);
			element.setAttribute("exp-sc", Integer.toString(expSc));
		}
		return element;
	}

	public void setPhysicalLocation(Site site) throws HttpException {
		SiteEra targetSiteSupply = null;
		for (SiteEra siteSupply : siteEras) {
			if (site.equals(siteSupply.getSite())) {
				targetSiteSupply = siteSupply;
			}
		}
		if (targetSiteSupply == null) {
			throw new UserException("The site isn't attached to this supply.");
		}
		for (SiteEra siteSupply : siteEras) {
			siteSupply.setIsPhysical(siteSupply.equals(targetSiteSupply));
		}
		Hiber.flush();
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element eraElement = (Element) toXml(
				doc,
				new XmlTree("siteEras", new XmlTree("site")).put("pc")
						.put("impLlfc").put("expLlfc").put("mtc").put("cop")
						.put("ssc")
						.put("supply", new XmlTree("source").put("gspGroup"))
						.put("mopContract", new XmlTree("party"))
						.put("hhdcContract", new XmlTree("party")));
		source.appendChild(eraElement);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(MonadDate.getHoursXml(doc));
		source.appendChild(HhStartDate.getHhMinutesXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (Pc pc : (List<Pc>) Hiber.session()
				.createQuery("from Pc pc order by pc.code").list()) {
			source.appendChild(pc.toXml(doc));
		}
		for (Cop cop : (List<Cop>) Hiber.session()
				.createQuery("from Cop cop order by cop.code").list()) {
			source.appendChild(cop.toXml(doc));
		}
		for (GspGroup group : (List<GspGroup>) Hiber.session()
				.createQuery("from GspGroup group order by group.code").list()) {
			source.appendChild(group.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'M' order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'C' order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		for (Contract contract : (List<Contract>) Hiber
				.session()
				.createQuery(
						"from Contract contract where contract.role.code = 'X' order by contract.name")
				.list()) {
			source.appendChild(contract.toXml(doc));
		}
		source.setAttribute("num-eras",
				Integer.toString(supply.getEras().size()));
		return doc;
	}

	public Channels getChannelsInstance() {
		return new Channels(this);
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public void detachSite(Site site) throws HttpException {
		if (siteEras.size() < 2) {
			throw new UserException(
					"A supply has to be attached to at least one site.");
		}
		SiteEra siteEra = (SiteEra) Hiber
				.session()
				.createQuery(
						"from SiteEra siteEra where siteEra.era = :era and siteEra.site = :site")
				.setEntity("era", this).setEntity("site", site).uniqueResult();
		if (siteEra == null) {
			throw new UserException(
					"Can't detach this site, as it wasn't attached in the first place.");
		}
		siteEras.remove(siteEra);
		siteEras.iterator().next().setIsPhysical(true);
		Hiber.flush();
		site.detachSiteEra(siteEra);
		Hiber.flush();
	}

}
