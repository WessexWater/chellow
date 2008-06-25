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

import java.util.List;

import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.Organization;
import net.sf.chellow.physical.PersistentEntity;

import org.hibernate.HibernateException;
import org.w3c.dom.Attr;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

public class Batch extends PersistentEntity implements Urlable {
	public static Batch getBatch(Long id) throws HttpException,
			InternalException {
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

	public Batch(Contract contract, String reference) {
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

	public void update(String reference) {
		setReference(reference);
	}

	public Node toXml(Document doc) throws HttpException {
		setTypeName("batch");
		Element element = (Element) super.toXml(doc);
		element.setAttributeNode((Attr) MonadString.toXml(doc, "reference",
				reference));
		return element;
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
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
	private void delete() throws InternalException, HttpException {
		for (Invoice invoice : (List<Invoice>) Hiber.session().createQuery(
				"from Invoice invoice where invoice.batch = :batch").setEntity(
				"batch", this).list()) {
			invoice.delete();
		}
		Hiber.session().delete(this);
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("service", new XmlTree(
						"provider", new XmlTree("organization")))));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return contract.batchesInstance().getUri().resolve(getUriId()).append(
				"/");
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		if (InvoiceImports.URI_ID.equals(uriId)) {
			return invoiceImportsInstance();
		} else if (Invoices.URI_ID.equals(uriId)) {
			return invoicesInstance();
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			DesignerException, HttpException, DeployerException {
		deleteBatch(this);
		inv.sendOk();
	}

	public Invoices invoicesInstance() {
		return new Invoices(this);
	}

	public InvoiceImports invoiceImportsInstance() {
		return new InvoiceImports(this);
	}

	@SuppressWarnings("unchecked")
	Invoice insertInvoice(InvoiceRaw rawInvoice) throws HttpException,
			InternalException {
		Invoice invoice = new Invoice(this, rawInvoice);
		Hiber.session().save(invoice);
		Hiber.flush();
		Organization organization = getContract().getOrganization();
		for (MpanRaw rawMpan : rawInvoice.getMpans()) {
			MpanCore mpanCore = organization.getMpanCore(rawMpan
					.getMpanCoreRaw());
			List<Mpan> candidateMpans = (List<Mpan>) Hiber
					.session()
					.createQuery(
							"from Mpan mpan where mpan.mpanCore = :mpanCore and mpan.mpanTop = :mpanTop and mpan.supplyGeneration.startDate.date <= :finishDate and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate.date >= :startDate) order by mpan.supplyGeneration.startDate.date desc")
					.setEntity("mpanCore", mpanCore).setEntity("mpanTop",
							rawMpan.getMpanTop()).setTimestamp("finishDate",
							rawInvoice.getFinishDate().getDate()).setTimestamp(
							"startDate", rawInvoice.getStartDate().getDate())
					.list();
			if (candidateMpans.isEmpty()) {
				throw new UserException("Problem with invoice '"
								+ rawInvoice.getReference()
								+ ". The invoice needs to be attached to the MPANs "
								+ rawInvoice.getMpanText() + " but the MPAN "
								+ rawMpan + " cannot be found between "
								+ " the half-hour ending "
								+ rawInvoice.getStartDate()
								+ " and the half-hour ending "
								+ rawInvoice.getFinishDate() + ".");
			}
			invoice.insertInvoiceMpan(candidateMpans.get(0));
		}
		Hiber.flush();
		Account account = organization.getAccount(getContract().getProvider(),
				rawInvoice.getAccountText());
		account.attach(invoice);
		return invoice;
	}
}