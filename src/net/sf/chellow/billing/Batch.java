/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
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

import java.math.BigDecimal;
import java.util.Date;
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
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.RawRegisterRead;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.ui.GeneralImport;

import org.hibernate.HibernateException;
import org.hibernate.exception.ConstraintViolationException;
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

	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String roleName = GeneralImport.addField(csvElement, "Role Name",
					values, 0);
			roleName = roleName.toLowerCase();
			String contractName = GeneralImport.addField(csvElement,
					"Contract Name", values, 1);
			Contract contract = null;

			if (roleName.equals("hhdc")) {
				contract = HhdcContract.getHhdcContract(contractName);
			} else if (roleName.equals("supplier")) {
				contract = SupplierContract.getSupplierContract(contractName);
			} else if (roleName.equals("mop")) {
				contract = MopContract.getMopContract(contractName);
			} else {
				throw new UserException(
						"The role name must be one of hhdc, supplier or mop.");
			}
			String reference = GeneralImport.addField(csvElement, "Reference",
					values, 2);

			String description = GeneralImport.addField(csvElement,
					"Description", values, 3);

			contract.insertBatch(reference, description);
		} else if (action.equals("update")) {
			String roleName = GeneralImport.addField(csvElement, "Role Name",
					values, 0);
			roleName = roleName.toLowerCase();

			String contractName = GeneralImport.addField(csvElement,
					"Contract Name", values, 1);
			Contract contract = null;

			if (roleName.equals("hhdc")) {
				contract = HhdcContract.getHhdcContract(contractName);
			} else if (roleName.equals("supplier")) {
				contract = SupplierContract.getSupplierContract(contractName);
			} else if (roleName.equals("mop")) {
				contract = MopContract.getMopContract(contractName);
			} else {
				throw new UserException(
						"The role name must be one of hhdc, supplier or mop.");
			}
			String oldReference = GeneralImport.addField(csvElement,
					"Old Reference", values, 2);
			Batch batch = contract.getBatch(oldReference);

			String newReference = GeneralImport.addField(csvElement,
					"New Reference", values, 3);

			String description = GeneralImport.addField(csvElement,
					"Description", values, 4);

			batch.update(newReference, description);
		}
	}

	private Contract contract;

	private String reference;

	private String description;

	public Batch() {
	}

	public Batch(Contract contract, String reference, String description)
			throws HttpException {
		setContract(contract);
		update(reference, description);
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

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
	}

	public void update(String reference, String description)
			throws HttpException {
		reference = reference.trim();
		if (reference.length() == 0) {
			throw new UserException("The batch reference can't be blank.");
		}
		setReference(reference);
		setDescription(description.trim());
		try {
			Hiber.flush();
		} catch (ConstraintViolationException e) {
			throw new UserException(
					"There's already a batch attached to the contract "
							+ getContract().getName() + " with the reference "
							+ reference + ".");
		}
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "batch");
		element.setAttribute("reference", reference);
		element.setAttribute("description", description);
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			Long contractId = getContract().getId();
			try {
				delete();
			} catch (HttpException e) {
				Batch batch = Batch.getBatch(getId());
				e.setDocument(batch.document());
				throw e;
			}
			Hiber.commit();
			inv.sendSeeOther(Contract.getContract(contractId).batchesInstance()
					.getUri());
		} else {
			String reference = inv.getString("reference");
			String description = inv.getString("description");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			Document doc = document();
			try {
				update(reference, description);
			} catch (UserException e) {
				e.setDocument(doc);
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private void delete() throws HttpException {
		Hiber.session()
				.createQuery("delete from Bill bill where bill.batch = :batch")
				.setEntity("batch", this).executeUpdate();
		Batch batch = Batch.getBatch(getId());
		Hiber.session().delete(batch);
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
		return contract.batchesInstance().getUri().resolve(getUriId())
				.append("/");
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

	public Bill insertBill(RawBill rawBill) throws HttpException {
		Bill bill = this.insertBill(rawBill.getAccount(),
				rawBill.getReference(), rawBill.getIssueDate(),
				rawBill.getStartDate(), rawBill.getFinishDate(),
				rawBill.getKwh(), rawBill.getNet(), rawBill.getVat(),
				rawBill.getGross(), rawBill.getType(), rawBill.getBreakdown());
		for (RawRegisterRead rawRead : rawBill.getRegisterReads()) {
			bill.insertRead(rawRead);
		}
		return bill;
	}

	public Bill insertBill(Supply supply, String account, String reference,
			Date issueDate, HhStartDate startDate, HhStartDate finishDate,
			BigDecimal kwh, BigDecimal net, BigDecimal vat, BigDecimal gross,
			BillType type, String breakdown) throws HttpException {
		Bill bill = new Bill(this, supply, account, reference, issueDate,
				startDate, finishDate, kwh, net, vat, gross, type, breakdown);
		Hiber.session().save(bill);
		Hiber.flush();
		return bill;
	}

	@SuppressWarnings("unchecked")
	public Bill insertBill(String account, String reference, Date issueDate,
			HhStartDate startDate, HhStartDate finishDate, BigDecimal kwh,
			BigDecimal net, BigDecimal vat, BigDecimal gross, BillType type,
			String breakdown) throws HttpException {
		List<Supply> supplyList = (List<Supply>) Hiber
				.session()
				.createQuery(
						"select mpan.supplyGeneration.supply from Mpan mpan where ((mpan.supplierContract = :contract and mpan.supplierAccount = :account) or (mpan.supplyGeneration.hhdcContract = :contract and mpan.supplyGeneration.hhdcAccount = :account) or (mpan.supplyGeneration.mopContract = :contract and mpan.supplyGeneration.mopAccount = :account)) order by mpan.core.dno.code, mpan.core.uniquePart")
				.setEntity("contract", getContract())
				.setString("account", account).list();
		if (supplyList.isEmpty()) {
			throw new UserException(
					"Can't find a supply generation with this contract and account number.");
		}
		return insertBill(supplyList.get(0), account, reference, issueDate,
				startDate, finishDate, kwh, net, vat, gross, type, breakdown);
	}
}
