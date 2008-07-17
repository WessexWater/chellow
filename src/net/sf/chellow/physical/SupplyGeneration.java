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

import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.billing.Account;
import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.billing.Invoice;
import net.sf.chellow.billing.InvoiceMpan;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.billing.SupplierContract;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
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
import net.sf.chellow.monad.types.MonadLong;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class SupplyGeneration extends PersistentEntity implements Urlable {
	static public SupplyGeneration getSupplyGeneration(MonadLong id)
			throws InternalException, HttpException {
		return getSupplyGeneration(id.getLong());
	}

	static public SupplyGeneration getSupplyGeneration(Long id)
			throws InternalException, HttpException {
		try {
			SupplyGeneration supplyGeneration = (SupplyGeneration) Hiber
					.session().get(SupplyGeneration.class, id);
			if (supplyGeneration == null) {
				throw new UserException(
						"There is no supply generation with that id.");
			}
			return supplyGeneration;
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	private Supply supply;

	private Set<SiteSupplyGeneration> siteSupplyGenerations;

	private HhEndDate startDate;

	private HhEndDate finishDate;

	private Mpan importMpan;

	private Mpan exportMpan;

	private Set<Mpan> mpans;

	private Meter meter;
	
	private Set<Channel> channels;

	SupplyGeneration(Supply supply, HhEndDate startDate, HhEndDate finishDate,
			Meter meter) throws HttpException {
		setChannels(new HashSet<Channel>());
		this.supply = supply;
		setSiteSupplyGenerations(new HashSet<SiteSupplyGeneration>());
		setMpans(new HashSet<Mpan>());
		intrinsicUpdate(startDate, finishDate, meter);
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Supply getSupply() {
		return supply;
	}

	public Set<SiteSupplyGeneration> getSiteSupplyGenerations() {
		return siteSupplyGenerations;
	}

	protected void setSiteSupplyGenerations(
			Set<SiteSupplyGeneration> siteSupplyGenerations) {
		this.siteSupplyGenerations = siteSupplyGenerations;
	}

	public HhEndDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhEndDate startDate) {
		this.startDate = startDate;
		startDate.setLabel("start");
	}

	public HhEndDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhEndDate finishDate) {
		this.finishDate = finishDate;
		if (finishDate != null) {
			finishDate.setLabel("finish");
		}
	}

	public Mpan getImportMpan() {
		return importMpan;
	}

	void setImportMpan(Mpan importMpan) {
		this.importMpan = importMpan;
	}

	public Mpan getMpan(IsImport isImport) {
		return isImport.getBoolean() ? getImportMpan() : getExportMpan();
	}
	
	public Set<Channel> getChannels() {
		return channels;
	}

	void setChannels(Set<Channel> channels) {
		this.channels = channels;
	}


	public Provider getDso() {
		Provider dso = null;
		if (getImportMpan() != null) {
			dso = getImportMpan().getMpanCore().getDso();
		}
		if (dso == null && getExportMpan() != null) {
			dso = getExportMpan().getMpanCore().getDso();
		}
		return dso;
	}

	public void attachSite(Site site) throws InternalException, HttpException {
		attachSite(site, false);
	}

	public void attachSite(Site site, boolean isLocation)
			throws InternalException, HttpException {
		boolean alreadyThere = false;
		for (SiteSupplyGeneration siteSupplyGeneration : siteSupplyGenerations) {
			if (siteSupplyGeneration.getSite().equals(site)) {
				alreadyThere = true;
				break;
			}
		}
		if (alreadyThere) {
			throw new UserException(
					"The site is already attached to this supply.");
		} else {
			SiteSupplyGeneration siteSupplyGeneration = new SiteSupplyGeneration(
					site, this, false);
			siteSupplyGenerations.add(siteSupplyGeneration);
			site.attachSiteSupplyGeneration(siteSupplyGeneration);
		}
		if (isLocation) {
			setPhysicalLocation(site);
		}
	}

	public void detachSite(Site site) throws HttpException, InternalException {
		if (siteSupplyGenerations.size() < 2) {
			throw new UserException(
					"A supply has to be attached to at least one site.");
		}
		SiteSupplyGeneration siteSupplyGeneration = (SiteSupplyGeneration) Hiber
				.session()
				.createQuery(
						"from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.site = :site")
				.setEntity("supplyGeneration", this).setEntity("site", site)
				.uniqueResult();
		if (siteSupplyGeneration == null) {
			throw new UserException(
					"Can't detach this site, as it wasn't attached in the first place.");
		}
		siteSupplyGenerations.remove(siteSupplyGeneration);
		siteSupplyGenerations.iterator().next().setIsPhysical(true);
		Hiber.flush();
		site.detachSiteSupplyGeneration(siteSupplyGeneration);
		Hiber.flush();
	}

	public void addOrUpdateMpans(MpanTop importMpanTop,
			MpanCore importMpanCore, Account importHhdceAccount,
			Account importSupplierAccount, boolean importHasImportKwh,
			boolean importHasImportKvarh, boolean importHasExportKwh,
			boolean importHasExportKvarh, Integer importAgreedSupplyCapacity,
			MpanTop exportMpanTop, MpanCore exportMpanCore,
			Account exportHhdceAccount, Account exportSupplierAccount,
			boolean exportHasImportKwh, boolean exportHasImportKvarh,
			boolean exportHasExportKwh, boolean exportHasExportKvarh,
			Integer exportAgreedSupplyCapacity) throws InternalException,
			HttpException, DesignerException {
		if (importMpanCore == null && exportMpanCore == null) {
			throw new UserException(document(),
					"A supply generation must have at least one MPAN.");
		}
		if (importMpanCore == null) {
			mpans.remove(importMpan);
			setImportMpan(null);
		} else {
			if (!importMpanCore.getSupply().equals(getSupply())) {
				throw new UserException(
						"This import MPAN core is not attached to this supply.");
			}
			if (!importMpanTop.getLlfc().getIsImport()) {
				throw new UserException(document(),
						"The import line loss factor '"
								+ importMpanTop.getLlfc()
								+ "' says that the MPAN is actually export.");
			}
			if (importMpan == null) {
				setImportMpan(new Mpan(this, importMpanTop, importMpanCore,
						importHhdceAccount, importSupplierAccount,
						importHasImportKwh, importHasImportKvarh,
						importHasExportKwh, importHasExportKvarh,
						importAgreedSupplyCapacity));
				mpans.add(importMpan);
			} else {
				importMpan.update(importMpanTop, importMpanCore,
						importHhdceAccount, importSupplierAccount,
						importHasImportKwh, importHasImportKvarh,
						importHasExportKwh, importHasExportKvarh,
						importAgreedSupplyCapacity);
			}
		}
		if (exportMpanCore == null) {
			mpans.remove(exportMpan);
			setExportMpan(null);
		} else {
			if (!exportMpanCore.getSupply().equals(getSupply())) {
				throw new UserException(
						"This export MPAN core is not attached to this supply.");
			}
			if (exportMpanTop.getLlfc().getIsImport()) {
				throw new UserException(
						"Problem with the export MPAN with core '"
								+ exportMpanCore + "'. The Line Loss Factor '"
								+ exportMpanTop.getLlfc()
								+ "' says that the MPAN is actually import.");
			}
			if (exportMpan == null) {
				setExportMpan(new Mpan(this, exportMpanTop, exportMpanCore,
						exportHhdceAccount, exportSupplierAccount,
						exportHasImportKwh, exportHasImportKvarh,
						exportHasExportKwh, exportHasExportKvarh,
						exportAgreedSupplyCapacity));
				mpans.add(exportMpan);
			} else {
				exportMpan.update(exportMpanTop, exportMpanCore,
						exportHhdceAccount, exportSupplierAccount,
						exportHasImportKwh, exportHasImportKvarh,
						exportHasExportKwh, exportHasExportKvarh,
						exportAgreedSupplyCapacity);
			}
		}

		Hiber.flush();

		// Check that if settlement MPANs then they're the same DSO.
		if (importMpanCore != null && exportMpanCore != null) {
			if (importMpanCore.getDso().getDsoCode().isSettlement()
					&& exportMpanCore.getDso().getDsoCode().isSettlement()
					&& !importMpanCore.getDso().equals(exportMpanCore.getDso())) {
				throw new UserException(
						"Two settlement MPAN generations on the same supply must have the same DSO.");
			}
			if (!importMpanTop.getLlfc().getVoltageLevel().equals(
					exportMpanTop.getLlfc().getVoltageLevel())) {
				throw new UserException(
						"The voltage level indicated by the Line Loss Factor must be the same for both the MPANs.");
			}
		}
		Provider dso = getDso();
		if (dso != null && dso.getDsoCode().equals(new DsoCode("22"))) {
			/*
			 * if (importMpan != null) { LineLossFactorCode code =
			 * importLineLossFactor.getCode(); if ((code.equals(new
			 * LineLossFactorCode("520")) || code.equals(new
			 * LineLossFactorCode("550")) || code .equals(new
			 * LineLossFactorCode("580"))) && getExportMpan() == null) { throw
			 * UserException .newOk("The Line Loss Factor of the import MPAN
			 * says that there should be an export MPAN, but there isn't one."); } }
			 */
			if (getExportMpan() != null && getImportMpan() != null) {
				LlfcCode code = getImportMpan().getMpanTop().getLlfc().getCode();
				if (!code.equals(new LlfcCode(520))
						&& !code.equals(new LlfcCode(550))
						&& !code.equals(new LlfcCode(580))) {
					throw new UserException(
							"The DSO is 22, there's an export MPAN and the Line Loss Factor of the import MPAN "
									+ getImportMpan()
									+ " can only be 520, 550 or 580.");
				}
			}
		}
		insertChannel(true, true);
		insertChannel(true, false);
		insertChannel(false, true);
		insertChannel(false, false);

		Hiber.flush();
		// more optimization possible here, doesn't necessarily need to check
		// data.
		getSupply().checkAfterUpdate(true, getStartDate(), getFinishDate());
		
	}

	public Mpan getExportMpan() {
		return exportMpan;
	}

	public void setExportMpan(Mpan exportMpan) {
		this.exportMpan = exportMpan;
	}

	public Set<Mpan> getMpans() {
		return mpans;
	}

	void setMpans(Set<Mpan> mpans) {
		this.mpans = mpans;
	}

	public Meter getMeter() {
		return meter;
	}

	void setMeter(Meter meter) {
		this.meter = meter;
	}

	public HhdcContract getHhdceContract(boolean isImport, boolean isKwh)
			throws HttpException {
		HhdcContract hhdceContract = null;
		if (importMpan != null) {
			hhdceContract = importMpan.getHhdceContract(isImport, isKwh);
		}
		if (hhdceContract == null && exportMpan != null) {
			hhdceContract = exportMpan.getHhdceContract(isImport, isKwh);
		}
		return hhdceContract;
	}

	public MpanCore getMpanCore(boolean isImport, boolean isKwh)
			throws HttpException {
		MpanCore mpanCore = null;
		if (importMpan != null
				&& importMpan.getHhdceContract(isImport, isKwh) != null) {
			mpanCore = importMpan.getMpanCore();
		}
		if (mpanCore == null && exportMpan != null
				&& exportMpan.getHhdceContract(isImport, isKwh) != null) {
			mpanCore = exportMpan.getMpanCore();
		}
		return mpanCore;
	}
	
	public Channel getChannel(boolean isImport, boolean isKwh) {
		for (Channel candidateChannel : channels) {
			if (candidateChannel.getIsImport() == isImport
					&& candidateChannel.getIsKwh() == isKwh) {
				return candidateChannel;
			}
		}
		return null;
	}

	void intrinsicUpdate(HhEndDate startDate, HhEndDate finishDate, Meter meter)
			throws InternalException, HttpException {
		if (finishDate != null
				&& startDate.getDate().after(finishDate.getDate())) {
			throw new UserException(
					"The generation start date can't be after the finish date.");
		}
		if (startDate == null) {
			throw new InternalException("start date can't be null.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		setMeter(meter);
	}

	void delete() throws HttpException, InternalException {
		List<SiteSupplyGeneration> ssGens = new ArrayList<SiteSupplyGeneration>();
		for (SiteSupplyGeneration ssGen : siteSupplyGenerations) {
			ssGens.add(ssGen);
		}
		for (SiteSupplyGeneration ssGen : ssGens) {
			siteSupplyGenerations.remove(ssGen);
			Hiber.flush();
			ssGen.getSite().detachSiteSupplyGeneration(ssGen);
			Hiber.flush();
		}
	}

	public void update(HhEndDate startDate, HhEndDate finishDate, Meter meter)
			throws InternalException, HttpException {
		HhEndDate originalStartDate = getStartDate();
		HhEndDate originalFinishDate = getFinishDate();
		if (startDate.equals(originalStartDate)
				&& ((finishDate != null && originalFinishDate != null && finishDate
						.equals(originalFinishDate)) || (finishDate == null && originalFinishDate == null))) {
			return;
		}
		SupplyGeneration previousSupplyGeneration = supply
				.getGenerationPrevious(this);
		if (previousSupplyGeneration != null) {
			if (!previousSupplyGeneration.getStartDate().getDate().before(
					startDate.getDate())) {
				throw new UserException(
						"The start date must be after the start date of the previous generation.");
			}
			previousSupplyGeneration.intrinsicUpdate(previousSupplyGeneration
					.getStartDate(), startDate.getPrevious(), meter);
		}
		SupplyGeneration nextSupplyGeneration = supply.getGenerationNext(this);
		if (nextSupplyGeneration != null) {
			if (finishDate == null) {
				throw new UserException(
						"The finish date must be before the finish date of the next generation.");
			}
			if (nextSupplyGeneration.getFinishDate() != null
					&& !finishDate.getDate().before(
							nextSupplyGeneration.getFinishDate().getDate())) {
				throw new UserException(
						"The finish date must be before the finish date of the next generation.");
			}
			nextSupplyGeneration.intrinsicUpdate(finishDate.getNext(),
					nextSupplyGeneration.getFinishDate(), nextSupplyGeneration
							.getMeter());
		}
		intrinsicUpdate(startDate, finishDate, meter);
		Hiber.flush();
		HhEndDate checkFinishDate = null;
		if (originalFinishDate != null && finishDate != null) {
			checkFinishDate = finishDate.getDate().after(
					originalFinishDate.getDate()) ? finishDate
					: originalFinishDate;
		}
		supply.checkAfterUpdate(true, startDate.getDate().before(
				originalStartDate.getDate()) ? startDate : originalStartDate,
				checkFinishDate);
	}

	public int compareTo(Object obj) {
		return getFinishDate().getDate().compareTo(
				((SupplyGeneration) obj).getFinishDate().getDate());
	}

	public void deleteMpan(Mpan mpan) throws HttpException, InternalException {
		if (mpans.size() < 2) {
			throw new UserException(
					"There must be at least one MPAN generation in each supply generation.");
		}
		mpans.remove(mpan);
	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		setTypeName("supply-generation");
		Element element = (Element) super.toXml(doc);
		element.appendChild(startDate.toXml(doc));
		if (finishDate != null) {
			element.appendChild(finishDate.toXml(doc));
		}
		for (Channel channel : channels) {
			element.appendChild(channel.toXml(doc));
		}
		return element;
	}
	
	void insertChannel(boolean isImport, boolean isKwh) {
		Channel channel = new Channel(this, isImport, isKwh);
		Hiber.session().save(channel);
		Hiber.flush();
		channels.add(channel);
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	private Organization organization() {
		return getSiteSupplyGenerations().iterator().next().getSite()
				.getOrganization();
	}

	@SuppressWarnings("unchecked")
	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element generationElement = (Element) toXml(doc, new XmlTree(
				"siteSupplyGenerations", new XmlTree("site", new XmlTree(
						"organization"))).put("meter").put("supply",
				new XmlTree("source")));
		source.appendChild(generationElement);
		source.appendChild(getSiteSupplyGenerations().iterator().next()
				.getSite().getOrganization().toXml(doc));
		for (Mpan mpan : mpans) {
			Element mpanElement = (Element) mpan.toXml(doc, new XmlTree(
					"mpanCore").put("mpanTop",
					new XmlTree("meterTimeswitch").put("llf"))
					.put("dceService").put("supplierAccount",
							new XmlTree("provider")).put("supplierService",
							new XmlTree("provider")));
			generationElement.appendChild(mpanElement);
			for (RegisterRead read : (List<RegisterRead>) Hiber.session()
					.createQuery(
							"from RegisterRead read where read.mpan = :mpan")
					.setEntity("mpan", mpan).list()) {
				mpanElement.appendChild(read.toXml(doc, new XmlTree("invoice",
						new XmlTree("batch", new XmlTree("service",
								new XmlTree("provider"))))));
			}
			for (InvoiceMpan invoiceMpan : (List<InvoiceMpan>) Hiber
					.session()
					.createQuery(
							"from InvoiceMpan invoiceMpan where invoiceMpan.mpan = :mpan")
					.setEntity("mpan", mpan).list()) {
				mpanElement.appendChild(invoiceMpan.toXml(doc, new XmlTree(
						"invoice", new XmlTree("batch", new XmlTree("service",
								new XmlTree("provider"))))));
			}
		}
		// Organization organization = organization();
		/*
		 * for (Dce dce : (List<Dce>) Hiber.session().createQuery( "from Dce
		 * dce where dce.organization = :organization")
		 * .setEntity("organization", organization).list()) { Element dceElement =
		 * dce.toXml(doc); source.appendChild(dceElement); for (HhdcContract
		 * dceService : (List<HhdcContract>) Hiber .session() .createQuery(
		 * "from DceService service where service.provider = :dce")
		 * .setEntity("dce", dce).list()) {
		 * dceElement.appendChild(dceService.toXml(doc)); } }
		 */
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		for (Pc profileClass : (List<Pc>) Hiber
				.session()
				.createQuery(
						"from ProfileClass profileClass order by profileClass.code")
				.list()) {
			source.appendChild(profileClass.toXml(doc));
		}
		return doc;
	}

	void deleteMpans() throws HttpException, InternalException {
		for (Mpan mpan : mpans) {
			mpan.delete();
		}
		mpans.clear();
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		if (inv.hasParameter("delete")) {
			try {
				supply.deleteGeneration(this);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendSeeOther(supply.getUri());
		} else if (inv.hasParameter("attach")) {
			SiteCode siteCode = inv.getValidatable(SiteCode.class, "site-code");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			Site site = organization().getSite(siteCode);
			attachSite(site);
			Hiber.commit();
			inv.sendOk(document());
		} else if (inv.hasParameter("detach")) {
			Long siteId = inv.getLong("site-id");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			Site site = organization().getSite(siteId);
			detachSite(site);
			Hiber.commit();
			inv.sendOk(document());
		} else if (inv.hasParameter("set-location")) {
			Long siteId = inv.getLong("site-id");
			if (!inv.isValid()) {
				throw new UserException();
			}
			Site site = organization().getSite(siteId);
			setPhysicalLocation(site);
			Hiber.commit();
			inv.sendOk(document());
		} else {
			Organization organization = organization();
			MpanTop importMpanTop = null;
			MpanCore importMpanCore = null;
			Integer importAgreedSupplyCapacity = null;
			Date startDate = inv.getDate("start-date");
			Date finishDate = null;
			String meterSerialNumber = inv.getString("meter-serial-number");
			HhdcContract importHhdceContract = null;
			Account importHhdceAccount = null;
			SupplierContract importSupplierContract = null;
			Account importSupplierAccount = null;
			boolean importHasImportKwh = false;
			boolean importHasImportKvarh = false;
			boolean importHasExportKwh = false;
			boolean importHasExportKvarh = false;
			boolean isEnded = inv.getBoolean("is-ended");
			if (isEnded) {
				finishDate = inv.getDate("finish-date");
			}
			try {
				Boolean hasImportMpan = inv.getBoolean("has-import-mpan");

				if (hasImportMpan) {
					Long importMpanCoreId = inv.getLong("import-mpan-core-id");
					importMpanCore = MpanCore.getMpanCore(importMpanCoreId);
					Long importProfileClassId = inv
							.getLong("import-profile-class-id");
					Pc importProfileClass = Pc
							.getPc(importProfileClassId);
					LlfcCode importLlfCode = new LlfcCode(inv
							.getInteger("import-llfc-code"));
					Llfc importLlf = importMpanCore.getDso().getLlfc(
							importLlfCode);
					MtcCode importMeterTimeswitchCode = inv
							.getValidatable(MtcCode.class,
									"import-meter-timeswitch-code");
					Mtc importMeterTimeswitch = Mtc
							.getMtc(importMpanCore.getDso(),
									importMeterTimeswitchCode);
					importMpanTop = MpanTop.getAnMpanTop(importProfileClass,
							importMeterTimeswitch, importLlf);
					importAgreedSupplyCapacity = inv
							.getInteger("import-agreed-supply-capacity");
					importHasImportKwh = inv
							.getBoolean("import-has-import-kwh");
					importHasImportKvarh = inv
							.getBoolean("import-has-import-kvarh");
					importHasExportKwh = inv
							.getBoolean("import-has-export-kwh");
					importHasExportKvarh = inv
							.getBoolean("import-has-export-kvarh");
					if (importHasImportKwh || importHasImportKvarh
							|| importHasExportKwh || importHasExportKvarh) {
						String importHhdceContractName = inv
								.getString("import-hhdce-contract-name");
						if (importHhdceContractName.length() != 0) {
							importHhdceContract = organization.getHhdcContract(importHhdceContractName);
							String hhdceAccountReference = inv.getString("hhdce-account-reference");
							importHhdceAccount = importHhdceContract.getAccount(hhdceAccountReference);
						}
					}
					String importSupplierContractName = inv
							.getString("import-supplier-contract-name");
					importSupplierContract = organization.getSupplierContract(importSupplierContractName);
					String importSupplierAccountReference = inv
							.getString("import-supplier-account-reference");
					importSupplierAccount = importSupplierContract
							.getAccount(importSupplierAccountReference);
				}
				MpanTop exportMpanTop = null;
				MpanCore exportMpanCore = null;
				Integer exportAgreedSupplyCapacity = null;
				Account exportHhdceAccount = null;
				HhdcContract exportHhdceContract = null;
				Account exportSupplierAccount = null;
				SupplierContract exportSupplierContract = null;
				boolean exportHasImportKwh = false;
				boolean exportHasImportKvarh = false;
				boolean exportHasExportKwh = false;
				boolean exportHasExportKvarh = false;
				boolean hasExportMpan = inv.getBoolean("has-export-mpan");
				if (hasExportMpan) {
					Long exportMpanCoreId = inv.getLong("export-mpan-core-id");
					exportMpanCore = MpanCore.getMpanCore(exportMpanCoreId);
					Long exportProfileClassId = inv
							.getLong("export-profile-class-id");
					Pc exportProfileClass = Pc
							.getPc(exportProfileClassId);
					LlfcCode exportLlfCode = new LlfcCode(inv
							.getInteger("export-llfc-code"));
					Llfc exportLlf = exportMpanCore.getDso().getLlfc(
							exportLlfCode);
					MtcCode exportMeterTimeswitchCode = inv
							.getValidatable(MtcCode.class,
									"export-meter-timeswitch-code");
					Mtc exportMeterTimeswitch = Mtc
							.getMtc(exportMpanCore.getDso(),
									exportMeterTimeswitchCode);
					exportMpanTop = MpanTop.getAnMpanTop(exportProfileClass,
							exportMeterTimeswitch, exportLlf);
					exportAgreedSupplyCapacity = inv
							.getInteger("export-agreed-supply-capacity");
					exportHasImportKwh = inv
							.getBoolean("export-has-import-kwh");
					exportHasImportKvarh = inv
							.getBoolean("export-has-import-kvarh");
					exportHasExportKwh = inv
							.getBoolean("export-has-export-kwh");
					exportHasExportKvarh = inv
							.getBoolean("export-has-export-kvarh");
					if (exportHasImportKwh || exportHasImportKvarh
							|| exportHasExportKwh || exportHasExportKvarh) {
						String exportHhdceContractName = inv
								.getString("export-hhdce-contract-name");
						if (exportHhdceContractName.length() != 0) {
							exportHhdceContract = organization.getHhdcContract(exportHhdceContractName);
							String exportHhdceAccountReference = inv.getString("export-hhdce-account-reference");
							exportHhdceAccount = exportHhdceContract.getAccount(exportHhdceAccountReference);
						}
					}
					String exportSupplierContractName = inv.getString("export-supplier-contract-name");
					exportSupplierContract = organization.getSupplierContract(exportSupplierContractName);
					String exportSupplierAccountReference = inv
							.getString("export-supplier-account-reference");
					exportSupplierAccount = exportSupplierContract
							.getAccount(exportSupplierAccountReference);
				}
				addOrUpdateMpans(importMpanTop, importMpanCore,
						importHhdceAccount, importSupplierAccount,
					 importHasImportKwh,
						importHasImportKvarh, importHasExportKwh,
						importHasExportKvarh, importAgreedSupplyCapacity,
						exportMpanTop, exportMpanCore, exportHhdceAccount,
						exportSupplierAccount,
						exportHasImportKwh, exportHasImportKvarh,
						exportHasExportKwh, exportHasExportKvarh,
						exportAgreedSupplyCapacity);
				Meter meter = null;
				if (meterSerialNumber != null
						&& meterSerialNumber.length() != 0) {
					meter = supply.findMeter(meterSerialNumber);
					if (meter == null) {
						meter = supply.insertMeter(meterSerialNumber);
					}
				}
				update(new HhEndDate(startDate), finishDate == null ? null
						: new HhEndDate(finishDate), meter);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return supply.getSupplyGenerationsInstance().getUri().resolve(
				getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		if (Channels.URI_ID.equals(uriId)) {
			return new Channels(this);
		} else {
		throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		// TODO Auto-generated method stub

	}

	public String toString() {
		return "SupplyGeneration id " + getId();
	}

	public void setPhysicalLocation(Site site) throws InternalException,
			HttpException {
		SiteSupplyGeneration targetSiteSupply = null;
		for (SiteSupplyGeneration siteSupply : siteSupplyGenerations) {
			if (site.equals(siteSupply.getSite())) {
				targetSiteSupply = siteSupply;
			}
		}
		if (targetSiteSupply == null) {
			throw new UserException("The site isn't attached to this supply.");
		}
		for (SiteSupplyGeneration siteSupply : siteSupplyGenerations) {
			siteSupply.setIsPhysical(siteSupply.equals(targetSiteSupply));
		}
		Hiber.flush();
	}

	public RegisterRead insertRegisterRead(RegisterReadRaw rawRegisterRead,
			Invoice invoice) throws HttpException, InternalException {
		Mpan importMpan = getImportMpan();
		Mpan exportMpan = getExportMpan();
		RegisterRead read = null;
		if (importMpan != null
				&& importMpan.getMpanRaw().equals(rawRegisterRead.getMpanRaw())) {
			read = invoice.insertRead(importMpan, rawRegisterRead);
		} else if (exportMpan != null
				&& exportMpan.getMpanRaw().equals(rawRegisterRead.getMpanRaw())) {
			read = invoice.insertRead(exportMpan, rawRegisterRead);
		} else {
			throw new UserException("For the supply " + getId()
					+ " neither the import MPAN " + importMpan
					+ " or the export MPAN " + exportMpan
					+ " match the register read MPAN "
					+ rawRegisterRead.getMpanRaw() + ".");
		}
		return read;
	}
	
	public Channels getChannelsInstance() {
		return new Channels(this);
	}
}