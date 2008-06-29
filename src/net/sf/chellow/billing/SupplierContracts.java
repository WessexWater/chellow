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

import java.util.Date;
import java.util.List;

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
import net.sf.chellow.monad.XmlDescriber;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Organization;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;

@SuppressWarnings("serial")
public class SupplierContracts implements Urlable, XmlDescriber {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("supplier-contracts");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Organization organization;

	public SupplierContracts(Organization organization) {
		this.organization = organization;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return organization.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		String participantCode = inv.getString("participant-code");
		String name = inv.getString("name");
		Date startDate = inv.getDate("start-date");
		String chargeScript = inv.getString("charge-script");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		Provider provider = Provider.getProvider(participantCode,
				MarketRole.SUPPLIER);
		SupplierContract contract = organization.insertSupplierContract(
				provider, name, HhEndDate.roundDown(startDate), chargeScript);
		Hiber.commit();
		inv.sendCreated(document(), contract.getUri());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element contractsElement = toXml(doc);
		source.appendChild(contractsElement);
		contractsElement.appendChild(organization.toXml(doc));
		for (SupplierContract contract : (List<SupplierContract>) Hiber
				.session()
				.createQuery(
						"from SupplierContract contract order by contract.name")
				.list()) {
			contractsElement.appendChild(contract.toXml(doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public SupplierContract getChild(UriPathElement uriId) throws HttpException,
			InternalException {
		SupplierContract contract = (SupplierContract) Hiber
				.session()
				.createQuery(
						"from SupplierContract contract where contract.id = :contractId")
				.setLong("contractId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (contract == null) {
			throw new NotFoundException();
		}
		return contract;
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Element toXml(Document doc) throws InternalException, HttpException {
		Element contractsElement = doc.createElement("supplier-contracts");
		return contractsElement;
	}

	public Node toXml(Document doc, XmlTree tree) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
	/*
	public List<SupplyGeneration> supplyGenerations(Account account) {
		return Hiber
				.session()
				.createQuery(
						"select mpan.supplyGeneration from Mpan mpan where mpan.supplierAccount = :account order by mpan.supplyGeneration.startDate.date")
				.setEntity("account", account).list();
	}
	*/
}