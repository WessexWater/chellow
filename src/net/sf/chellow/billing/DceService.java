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

package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.hhimport.HhDataImportProcesses;
import net.sf.chellow.hhimport.stark.StarkAutomaticHhDataImporter;
import net.sf.chellow.hhimport.stark.StarkAutomaticHhDataImporters;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadInteger;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.ContractFrequency;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.SnagsChannel;
import net.sf.chellow.physical.SnagsSite;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class DceService extends Service {
	public static DceService getDceService(Long id) throws UserException,
			ProgrammerException {
		DceService service = findDceService(id);
		if (service == null) {
			throw UserException
					.newInvalidParameter("There isn't a DCE service with that id.");
		}
		return service;
	}

	public static DceService findDceService(Long id) throws UserException,
			ProgrammerException {
		return (DceService) Hiber.session().get(DceService.class, id);
	}

	private Dce provider;

	private ContractFrequency frequency;

	private int lag;

	public DceService() {
		setTypeName("dce-service");
	}

	public DceService(int type, String name, HhEndDate startDate,
			String chargeScript, Dce provider,
			ContractFrequency frequency, int lag) throws UserException,
			ProgrammerException, DesignerException {
		super(type, name, startDate, chargeScript);
		setProvider(provider);
		intrinsicUpdate(type, name, chargeScript,
			 frequency, lag);
	}

	public Dce getProvider() {
		return provider;
	}

	void setProvider(Dce provider) {
		this.provider = provider;
	}

	public ContractFrequency getFrequency() {
		return frequency;
	}

	void setFrequency(ContractFrequency frequency) {
		this.frequency = frequency;
	}

	public int getLag() {
		return lag;
	}

	void setLag(int lag) {
		this.lag = lag;
	}

	private void intrinsicUpdate(int type, String name, String chargeScript,
			ContractFrequency frequency, int lag) throws UserException,
			ProgrammerException, DesignerException {
		super.internalUpdate(type, name, chargeScript);
		setFrequency(frequency);
		setLag(lag);
	}

	@SuppressWarnings("unchecked")
	public void update(int type, String name, String chargeScript,
			ContractFrequency frequency, int lag) throws UserException,
			ProgrammerException, DesignerException {
		intrinsicUpdate(type, name, chargeScript,
				frequency, lag);
		updateNotification();
		// test if new dates agree with supply generation dates.
		
	}
	
	@SuppressWarnings("unchecked")
	void updateNotification() throws UserException, ProgrammerException, DesignerException {
		super.updateNotification();
		for (Mpan mpan : (List<Mpan>) Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.dceService = :dceService and mpan.supplyGeneration.startDate >= :startDate and (mpan.supplyGeneration.finishDate.date <= :finishDate or (mpan.supplyGeneration.finishDate.date is null and :finishDate is null))").setEntity("dceService", this)
				.setTimestamp("startDate", getStartDate().getDate()).setTimestamp(
						"finishDate", getFinishDate() == null ? null : getFinishDate().getDate()).list()) {
			throw UserException
					.newInvalidParameter("The supply '"
							+ mpan.getSupplyGeneration().getSupply().getId()
							+ "' has an MPAN with this contract that covers a time outside this contract.");
		}
	}

	/*
	 * public MonadInteger getNumberOfSnags() throws ProgrammerException {
	 * MonadInteger numberOfSnags = null; int numSnags = (Integer) Hiber
	 * .session() .createQuery( "select count(*) from SnagChannel snag where
	 * snag.contract.id = :contractId and snag.dateResolved.date is null and
	 * snag.startDate.date < :snagDate") .setLong("contractId",
	 * getId()).setDate( "snagDate", new Date(System.currentTimeMillis() -
	 * SnagChannel.SNAG_CHECK_LEAD_TIME)) .uniqueResult();
	 * 
	 * numSnags += (Integer) Hiber .session() .createQuery( "select count(*)
	 * from SnagSite snag where snag.contract.id = :contractId and
	 * snag.dateResolved.date is null and snag.startDate.date < :snagDate")
	 * .setLong("contractId", getId()).setDate( "snagDate", new
	 * Date(System.currentTimeMillis() - SnagChannel.SNAG_CHECK_LEAD_TIME))
	 * .uniqueResult(); try { numberOfSnags = new MonadInteger(numSnags); }
	 * catch (MonadInstantiationException e) { throw new ProgrammerException(e); }
	 * numberOfSnags.setLabel("numberOfSnags"); return numberOfSnags; }
	 */
	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof DceService) {
			DceService contract = (DceService) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return getProvider().servicesInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void httpPost(Invocation inv) throws ProgrammerException,
			UserException, DesignerException, DeployerException {
		int type = inv.getInteger("type");
		String name = inv.getString("name");
		String chargeScript = inv.getString("charge-script");
		ContractFrequency frequency = inv.getValidatable(
				ContractFrequency.class, "frequency");
		int lag = inv.getInteger("lag");
		if (!inv.isValid()) {
			throw UserException.newInvalidParameter(document());
		}
		update(type, name, chargeScript, frequency,
				lag);
		Hiber.commit();
		inv.sendOk(document());
	}

	protected Document document() throws ProgrammerException, UserException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(getXML(new XmlTree("provider", new XmlTree(
				"organization")), doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	public HhDataImportProcesses getHhDataImportProcessesInstance() {
		return new HhDataImportProcesses(this);
	}
	
	public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
			UserException {
		if (HhDataImportProcesses.URI_ID.equals(uriId)) {
			return getHhDataImportProcessesInstance();
		} else if (SnagsChannel.URI_ID.equals(uriId)) {
			return getSnagsChannelInstance();
		} else if (SnagsSite.URI_ID.equals(uriId)) {
			return getSnagsSiteInstance();
		} else if (StarkAutomaticHhDataImporter.URI_ID.equals(uriId)) {
			return StarkAutomaticHhDataImporters.getImportersInstance()
					.findImporter(this);
		} else {
			return null;
		}
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			UserException {
		// TODO Auto-generated method stub

	}

	public SnagsChannel getSnagsChannelInstance() {
		return new SnagsChannel(this);
	}

	public String toString() {
		return "Service id " + getId() + " " + getProvider() + " name "
				+ getName();
	}

	public SnagsSite getSnagsSiteInstance() {
		return new SnagsSite(this);
	}

	public Element toXML(Document doc) throws ProgrammerException,
			UserException {
		Element element = super.toXML(doc);

		element.setAttributeNode(frequency.toXML(doc));
		element.setAttributeNode(MonadInteger.toXml(doc, "lag", lag));
		element.setAttribute("has-stark-automatic-hh-data-importer",
				StarkAutomaticHhDataImporters.getImportersInstance()
						.findImporter(this) == null ? "false" : "true");
		return element;
	}
}