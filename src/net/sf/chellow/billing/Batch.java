/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
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

package net.sf.chellow.billing;

import java.util.List;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.RawRegisterRead;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.physical.SupplySnag;

import org.hibernate.HibernateException;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Batch extends PersistentEntity {
	public static Batch getBatch(Long id) throws HttpException {
		Batch batch = (Batch) Hiber.session().get(Batch.class, id);
		if (batch == null) {
			throw new UserException("There isn't a batch with that id.");
		}
		return batch;
	}

	public static void deleteBatch(Batch batch) throws InternalException {
		try {
			Hiber.session().delete(batch);
			Hiber.flush();
		} catch (HibernateException e) {
			throw new InternalException(e);
		}
	}

	private Contract contract;

	private String reference;

	public Batch() {
	}

	public Batch(Contract contract, String reference) throws HttpException {
		setContract(contract);
		update(reference);
	}

	public Contract getContract() {
		return contract;
	}

	public void setContract(Contract contract) {
		this.contract = contract;
	}

	public String getReference() {
		return reference;
	}

	public void setReference(String reference) {
		this.reference = reference;
	}

	public void update(String reference) throws HttpException {
		if (reference.trim().length() == 0) {
			throw new UserException("The batch reference can't be blank.");
		}
		setReference(reference);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "batch");
		element.setAttribute("reference", reference);
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			try {
				delete();
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendSeeOther(contract.batchesInstance().getUri());
		} else {
			String reference = inv.getString("reference");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(reference);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	@SuppressWarnings("unchecked")
	private void delete() throws HttpException {
		for (Bill bill : (List<Bill>) Hiber.session().createQuery(
				"from Bill bill where bill.batch = :batch").setEntity("batch",
				this).list()) {
			bill.delete();
		}
		Hiber.session().delete(this);
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("contract", new XmlTree(
				"party"))));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws HttpException {
		return contract.batchesInstance().getUri().resolve(getUriId()).append(
				"/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (BillImports.URI_ID.equals(uriId)) {
			return billImportsInstance();
		} else if (Bills.URI_ID.equals(uriId)) {
			return billsInstance();
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws HttpException {
		deleteBatch(this);
		inv.sendOk();
	}

	public Bills billsInstance() {
		return new Bills(this);
	}

	public BillImports billImportsInstance() {
		return new BillImports(this);
	}

	@SuppressWarnings("unchecked")
	Bill insertBill(RawBill rawBill) throws HttpException {
		List<Supply> supplyList = (List<Supply>) Hiber
				.session()
				.createQuery(
						"select mpan.supplyGeneration.supply from Mpan mpan where ((mpan.supplierContract = :contract and mpan.supplierAccount = :account) or (mpan.supplyGeneration.hhdcContract = :contract and mpan.supplyGeneration.hhdcAccount = :account) or (mpan.supplyGeneration.mopContract = :contract and mpan.supplyGeneration.mopAccount = :account)) and mpan.supplyGeneration.startDate.date <= :billFinish and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate.date >= :billFinish) order by mpan.core.dso.code, mpan.core.uniquePart")
				.setEntity("contract", getContract()).setString("account",
						rawBill.getAccount()).setTimestamp("billFinish",
						rawBill.getFinishDate().getDate()).list();
		if (supplyList.isEmpty()) {
			throw new UserException(
					"Can't find a supply generation with this contract and account number.");
		}
		Hiber.flush();
		Supply supply = supplyList.get(0);
		Bill bill = new Bill(this, supply);
		Hiber.session().save(bill);
		Hiber.flush();
		bill.update(rawBill.getReference(), rawBill.getIssueDate(), rawBill
				.getStartDate(), rawBill.getFinishDate(), rawBill.getKwh(),
				rawBill.getNet(), rawBill.getVat(), rawBill.getType(), null,
				false, rawBill.getBreakdown());
		for (RawRegisterRead rawRead : rawBill.getRegisterReads()) {
			bill.insertRead(rawRead);
		}

		List<SupplyGeneration> generations = supply.getGenerations(bill
				.getStartDate(), bill.getFinishDate());

		// what about missing bill snags??????
		for (SupplyGeneration generation : generations) {
			HhStartDate st = generation.getStartDate().before(
					bill.getStartDate()) ? bill.getStartDate() : generation
					.getStartDate();
			HhStartDate fn = bill.getFinishDate().before(
					generation.getFinishDate()) ? bill.getFinishDate()
					: generation.getFinishDate();
			HhdcContract hhdcContract = generation.getHhdcContract();
			if (hhdcContract != null
					&& hhdcContract.getId() == contract.getId()) {
				supply
						.deleteSnag(hhdcContract, SupplySnag.MISSING_BILL, st,
								fn);
			}
			Mpan importMpan = generation.getImportMpan();
			if (importMpan != null
					&& importMpan.getSupplierContract().getId().equals(
							contract.getId())) {
				// Debug.print("Deleting snag from " + st + " to " + fn +
				// " sup con " + importMpan.getSupplierContract().toString());
				supply.deleteSnag(importMpan.getSupplierContract(),
						SupplySnag.MISSING_BILL, st, fn);
			}
			Mpan exportMpan = generation.getExportMpan();
			if (exportMpan != null
					&& exportMpan.getSupplierContract().getId().equals(
							contract.getId())) {
				supply.deleteSnag(exportMpan.getSupplierContract(),
						SupplySnag.MISSING_BILL, st, fn);
			}
		}
		return bill;
	}
}
