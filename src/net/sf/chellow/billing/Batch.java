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

package net.sf.chellow.billing;

import java.math.BigDecimal;
import java.net.URI;
import java.net.URISyntaxException;
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
				contract = Contract.getHhdcContract(contractName);
			} else if (roleName.equals("supplier")) {
				contract = Contract.getSupplierContract(contractName);
			} else if (roleName.equals("mop")) {
				contract = Contract.getMopContract(contractName);
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
				contract = Contract.getHhdcContract(contractName);
			} else if (roleName.equals("supplier")) {
				contract = Contract.getSupplierContract(contractName);
			} else if (roleName.equals("mop")) {
				contract = Contract.getMopContract(contractName);
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

	public MonadUri getEditUri() throws HttpException {
		return contract.batchesInstance().getEditUri().resolve(getUriId())
				.append("/");
	}

	public URI getViewUri() throws HttpException {
		String report = null;
		String contractUrl = contract.getEditUri().toString();
		if (contractUrl.contains("supplier-contracts")) {
			report = "91";
		} else if (contractUrl.contains("hhdc-contracts")) {
			report = "203";
		} else if (contractUrl.contains("mop-contracts")) {
			report = "193";
		} else {
			throw new InternalException("Unkown contract type.");
		}
		try {
			return new URI("/reports/" + report + "/output/?batch-id="
					+ getId());
		} catch (URISyntaxException e) {
			throw new InternalException(e);
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("contract", new XmlTree(
				"party"))));
		return doc;
	}

	public BillImports billImportsInstance() {
		return new BillImports(this);
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

	public Bills billsInstance() {
		return new Bills(this);
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "batch");
		element.setAttribute("reference", reference);
		element.setAttribute("description", description);
		return element;
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

	@SuppressWarnings("unchecked")
	public Bill insertBill(String account, String reference, Date issueDate,
			HhStartDate startDate, HhStartDate finishDate, BigDecimal kwh,
			BigDecimal net, BigDecimal vat, BigDecimal gross, BillType type,
			String breakdown) throws HttpException {
		List<Supply> supplyList = (List<Supply>) Hiber
				.session()
				.createQuery(
						"select era.supply from Era era where (era.impSupplierContract = :contract and era.impSupplierAccount = :account) or (era.expSupplierContract = :contract and era.expSupplierAccount = :account) or (era.hhdcContract = :contract and era.hhdcAccount = :account) or (era.mopContract = :contract and era.mopAccount = :account)) order by era.impMpanCore, era.expMpanCore")
				.setEntity("contract", getContract())
				.setString("account", account).list();
		if (supplyList.isEmpty()) {
			throw new UserException(
					"Can't find an era with this contract and account number.");
		}
		return insertBill(supplyList.get(0), account, reference, issueDate,
				startDate, finishDate, kwh, net, vat, gross, type, breakdown);
	}

}
