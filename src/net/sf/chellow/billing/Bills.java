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
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.EntityList;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.MpanCore;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Bills extends EntityList {
	public static final UriPathElement URI_ID;

	static {
		try {
			URI_ID = new UriPathElement("bills");
		} catch (HttpException e) {
			throw new RuntimeException(e);
		}
	}

	private Batch batch;

	public Bills(Batch batch) {
		setBatch(batch);
	}

	public Batch getBatch() {
		return batch;
	}

	void setBatch(Batch batch) {
		this.batch = batch;
	}

	public UriPathElement getUrlId() {
		return URI_ID;
	}

	public MonadUri getUri() throws HttpException {
		return batch.getUri().resolve(getUrlId()).append("/");
	}

	public void httpPost(Invocation inv) throws HttpException {
		String mpanCoreStr = inv.getString("mpan-core");
		String account = inv.getString("account");
		String reference = inv.getString("reference");
		Date issueDate = inv.getDate("issue");
		Date startDate = inv.getDate("start");
		Date finishDate = inv.getDate("finish");
		BigDecimal kwh = inv.getBigDecimal("kwh");
		BigDecimal net = inv.getBigDecimal("net");
		BigDecimal vat = inv.getBigDecimal("vat");
		Long billTypeId = inv.getLong("bill-type-id");
		String breakdown = inv.getString("breakdown");

		if (!inv.isValid()) {
			throw new UserException(document());
		}
		try {
			batch.insertBill(MpanCore.getMpanCore(mpanCoreStr).getSupply(),
					account, reference, issueDate, new HhStartDate(startDate),
					new HhStartDate(finishDate), kwh, net, vat, BillType
							.getBillType(billTypeId), breakdown);
		} catch (UserException e) {
			e.setDocument(document());
			throw e;
		}
		Hiber.commit();
		inv.sendOk(document());
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	@SuppressWarnings("unchecked")
	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billsElement = toXml(doc);
		source.appendChild(billsElement);
		billsElement.appendChild(batch.toXml(doc, new XmlTree("contract",
				new XmlTree("party"))));
		for (Bill bill : (List<Bill>) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.batch = :batch order by bill.startDate.date desc")
				.setEntity("batch", batch).list()) {
			billsElement.appendChild(bill.toXml(doc, new XmlTree("supply")
					.put("type")));
		}
		for (BillType type : (List<BillType>) Hiber.session().createQuery(
				"from BillType type order by type.code").list()) {
			source.appendChild(type.toXml(doc));
		}
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public Bill getChild(UriPathElement uriId) throws HttpException {
		Bill bill = (Bill) Hiber
				.session()
				.createQuery(
						"from Bill bill where bill.batch = :batch and bill.id = :billId")
				.setEntity("batch", batch).setLong("billId",
						Long.parseLong(uriId.getString())).uniqueResult();
		if (bill == null) {
			throw new NotFoundException();
		}
		return bill;
	}

	public Element toXml(Document doc) throws HttpException {
		Element billsElement = doc.createElement("bills");
		return billsElement;
	}
}
