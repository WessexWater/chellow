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

package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.hhimport.HhDataImportProcesses;
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
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.Snag;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class SupplierContract extends Contract {
	public static SupplierContract getSupplierContract(Long id)
			throws HttpException, InternalException {
		SupplierContract service = findSupplierService(id);
		if (service == null) {
			throw new UserException(
					"There isn't a supplier service with that id.");
		}
		return service;
	}

	public static SupplierContract findSupplierService(Long id) {
		return (SupplierContract) Hiber.session().get(SupplierContract.class,
				id);
	}

	public SupplierContract() {
	}

	public SupplierContract(Provider supplier, Organization organization,
			String name, HhEndDate startDate, String chargeScript)
			throws HttpException {
		super(supplier, organization, name, startDate, chargeScript);
		if (supplier.getRole().getCode() != MarketRole.SUPPLIER) {
			throw new UserException(
					"The provider must have the role of supplier.");
		}
	}

	public void update(String name, String chargeScript) throws HttpException {
		super.update(name, chargeScript);
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof SupplierContract) {
			SupplierContract contract = (SupplierContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return getOrganization().getUri().resolve(getUriId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		String chargeScript = inv.getString("charge-script");
		if (inv.hasParameter("test")) {
			Long billId = inv.getLong("bill-id");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			try {
				Bill bill = Bill.getBill(billId);
				Document doc = document();
				Element source = doc.getDocumentElement();
				source.appendChild(bill.getElement(chargeScript).toXml(doc));
				inv.sendOk(doc);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
		} else {
			String name = inv.getString("name");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(name, chargeScript);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	@SuppressWarnings("unchecked")
	void updateNotification(HhEndDate startDate, HhEndDate finishDate)
			throws HttpException {
		List<Mpan> mpansOutside = Hiber
				.session()
				.createQuery(
						"from Mpan mpan where mpan.supplierAccount.contract.id = :contractId and mpan.supplyGeneration.startDate.date < :startDate and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate > :finishDate) order by mpan.supplyGeneration.startDate.date desc")
				.setLong("contractId", this.getId()).setTimestamp("startDate",
						getStartDate().getDate()).setTimestamp(
						"finishDate",
						getFinishDate() == null ? null : getFinishDate()
								.getDate()).list();
		if (!mpansOutside.isEmpty()) {
			throw new UserException(document(),
					mpansOutside.size() > 1 ? "The MPANs with cores "
							+ mpansOutside.get(0).getMpanCore()
							+ " and "
							+ mpansOutside.get(mpansOutside.size() - 1)
									.getMpanCore() + " use this service"
							: "An MPAN with core "
									+ mpansOutside.get(0).getMpanCore()
									+ " uses this service and lies outside "
									+ startDate
									+ " to "
									+ (finishDate == null ? "ongoing"
											: finishDate + "."));
		}
		super.updateNotification(startDate, finishDate);
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("provider")
				.put("organization")));
		for (Provider provider : (List<Provider>) Hiber
				.session()
				.createQuery(
						"from Provider provider where provider.role.code = :roleCode order by provider.name")
				.setCharacter("roleCode", MarketRole.SUPPLIER).list()) {
			source.appendChild(provider.toXml(doc, new XmlTree("participant")));
		}
		source.appendChild(new MonadDate().toXml(doc));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public int compareTo(SupplierContract arg0) {
		return 0;
	}

	public Snag getSnag(UriPathElement uriId) throws HttpException {
		Snag snag = (Snag) Hiber
				.session()
				.createQuery(
						"from Snag snag where snag.contract = :contract and snag.id = :snagId")
				.setEntity("contract", this).setLong("snagId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	public HhDataImportProcesses getHhDataImportProcessesInstance() {
		return new HhDataImportProcesses(this);
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Batches.URI_ID.equals(uriId)) {
			return new Batches(this);
		} else if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else if (AccountSnags.URI_ID.equals(uriId)) {
			return new AccountSnags(this);
		} else if (BillSnags.URI_ID.equals(uriId)) {
			return new BillSnags(this);
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public String toString() {
		return "Contract id " + getId() + " " + getProvider() + " name "
				+ getName();
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "supplier-contract");
		return element;
	}

	public void deleteAccount(Account account) throws HttpException {
		if (account.getContract().getProvider().getRole().getCode() != MarketRole.SUPPLIER) {
			throw new InternalException(
					"The account isn't attached to this contract.");
		}
		if (((Long) Hiber
				.session()
				.createQuery(
						"select count(*) from Mpan mpan where mpan.supplierAccount = :supplierAccount")
				.setEntity("supplierAccount", account).uniqueResult()) > 0) {
			throw new UserException(
					"An account can't be deleted if there are still MPANs attached to it.");
		}
		Hiber.session().delete(account);
		Hiber.flush();
	}

}