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

import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class DcsService extends Service {
	public static DcsService getContractDcs(Long id) throws InternalException, UserException {
		DcsService contract = (DcsService) Hiber.session().get(
				DcsService.class, id);
		if (contract == null) {
			throw new UserException
					("There isn't a DCS contract with that id.");
		}
		return contract;
	}

	private Dcs provider;

	public DcsService() {
		setTypeName("contract-dcs");
	}

	public DcsService(int type, String name, HhEndDate startDate, HhEndDate finishDate,
			String chargeScript, Dcs dcs) throws HttpException {
		intrinsicUpdate(type, name, chargeScript, dcs);
	}

	public Dcs getProvider() {
		return provider;
	}

	void setProvider(Dcs provider) {
		this.provider = provider;
	}

	protected void intrinsicUpdate(int type, String name, String chargeScript, Dcs provider) throws HttpException {
		super.update(type, name, chargeScript);
		setProvider(provider);
	}

	/*
	 * public MonadInteger getNumberOfSnags() throws ProgrammerException {
	 * MonadInteger numberOfSnags = null; int numSnags = (Integer) Hiber
	 * .session() .createQuery( "select count(*) from ChannelSnag snag where
	 * snag.contract.id = :contractId and snag.dateResolved.date is null and
	 * snag.startDate.date < :snagDate") .setLong("contractId",
	 * getId()).setDate( "snagDate", new Date(System.currentTimeMillis() -
	 * ChannelSnag.SNAG_CHECK_LEAD_TIME)) .uniqueResult();
	 * 
	 * numSnags += (Integer) Hiber .session() .createQuery( "select count(*)
	 * from SnagSite snag where snag.contract.id = :contractId and
	 * snag.dateResolved.date is null and snag.startDate.date < :snagDate")
	 * .setLong("contractId", getId()).setDate( "snagDate", new
	 * Date(System.currentTimeMillis() - ChannelSnag.SNAG_CHECK_LEAD_TIME))
	 * .uniqueResult(); try { numberOfSnags = new MonadInteger(numSnags); }
	 * catch (MonadInstantiationException e) { throw new ProgrammerException(e); }
	 * numberOfSnags.setLabel("numberOfSnags"); return numberOfSnags; }
	 */
	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof DcsService) {
			DcsService contract = (DcsService) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws HttpException {
		return provider.contractsInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		int type = inv.getInteger("type");
		String name = inv.getString("name");
		String chargeScript = inv.getString("charge-script");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		update(type, name, chargeScript);
		Hiber.commit();
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("dcs").put("organization")));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	/*
	 * public Snag getSnag(UriPathElement uriId) throws UserException,
	 * ProgrammerException { Snag snag = (Snag) Hiber .session() .createQuery(
	 * "from Snag snag where snag.contract = :contract and snag.id = :snagId")
	 * .setEntity("contract", this).setLong("snagId",
	 * Long.parseLong(uriId.getString())).uniqueResult(); if (snag == null) {
	 * throw UserException.newNotFound(); } return snag; }
	 * 
	 * public SnagsChannel getSnagsChannelInstance() { return new
	 * SnagsChannel(this); }
	 * 
	 * public SnagsSite getSnagsSiteInstance() { return new SnagsSite(this); }
	 * 
	 * public HhDataImportProcesses getHhDataImportProcessesInstance() { return
	 * new HhDataImportProcesses(this); }
	 * 
	 * public Urlable getChild(UriPathElement uriId) throws ProgrammerException,
	 * UserException { if (HhDataImportProcesses.URI_ID.equals(uriId)) { return
	 * getHhDataImportProcessesInstance(); } else if
	 * (SnagsChannel.URI_ID.equals(uriId)) { return getSnagsChannelInstance(); }
	 * else if (SnagsSite.URI_ID.equals(uriId)) { return getSnagsSiteInstance(); }
	 * else if (StarkAutomaticHhDataImporter.URI_ID.equals(uriId)) { return
	 * StarkAutomaticHhDataImporters.getImportersInstance() .findImporter(this); }
	 * else { return null; } }
	 */
	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public String toString() {
		return "Contract id " + getId() + " " + getProvider() + " name "
				+ getName();
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}