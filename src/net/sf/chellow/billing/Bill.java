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
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

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
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.RawRegisterRead;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.RegisterRead;
import net.sf.chellow.physical.RegisterReads;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplyGeneration;
import net.sf.chellow.physical.Tpr;
import net.sf.chellow.physical.Units;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Bill extends PersistentEntity implements Urlable {
	public static void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {
			String roleName = GeneralImport.addField(csvElement, "Role Name",
					values, 0);
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
			String batchReference = GeneralImport.addField(csvElement,
					"Batch Reference", values, 2);

			Batch batch = contract.getBatch(batchReference);
			String mpanCoreStr = GeneralImport.addField(csvElement,
					"Mpan Core", values, 3);
			MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
			String issueDateStr = GeneralImport.addField(csvElement,
					"Issue Date", values, 4);
			Date issueDate = new MonadDate(issueDateStr).getDate();
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 5);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 6);
			HhStartDate finishDate = new HhStartDate(finishDateStr);
			String netStr = GeneralImport
					.addField(csvElement, "Net", values, 7);
			BigDecimal net = new BigDecimal(netStr);
			String vatStr = GeneralImport
					.addField(csvElement, "Vat", values, 8);
			BigDecimal vat = new BigDecimal(vatStr);
			String account = GeneralImport.addField(csvElement, "Reference",
					values, 9);

			String reference = GeneralImport.addField(csvElement, "Reference",
					values, 10);
			String typeCode = GeneralImport.addField(csvElement, "Type",
					values, 11);
			BillType type = BillType.getBillType(typeCode);

			String breakdown = GeneralImport.addField(csvElement, "Breakdown",
					values, 12);

			String kwhStr = GeneralImport.addField(csvElement, "kWh", values,
					13);
			BigDecimal kwh = new BigDecimal(kwhStr);

			Bill bill = batch.insertBill(mpanCore.getSupply(), account,
					reference, issueDate, startDate, finishDate, kwh, net, vat,
					type, breakdown);
			for (int i = 14; i < values.length; i += 11) {
				String meterSerialNumber = GeneralImport.addField(csvElement,
						"Meter Serial Number", values, i);
				String mpanStr = GeneralImport.addField(csvElement, "MPAN",
						values, i + 1);
				String coefficientStr = GeneralImport.addField(csvElement,
						"Coefficient", values, i + 2);
				BigDecimal coefficient = new BigDecimal(coefficientStr);
				String unitsStr = GeneralImport.addField(csvElement, "Units",
						values, i + 3);
				Units units = Units.getUnits(unitsStr);
				String tprStr = GeneralImport.addField(csvElement, "TPR",
						values, i + 4);
				Tpr tpr = Tpr.getTpr(tprStr);
				String previousDateStr = GeneralImport.addField(csvElement,
						"Previous Date", values, i + 5);
				HhStartDate previousDate = new HhStartDate(previousDateStr);
				String previousValueStr = GeneralImport.addField(csvElement,
						"Previous Value", values, i + 6);
				BigDecimal previousValue = new BigDecimal(previousValueStr);

				String previousTypeStr = GeneralImport.addField(csvElement,
						"Previous Type", values, i + 7);
				ReadType previousType = ReadType.getReadType(previousTypeStr);

				String presentDateStr = GeneralImport.addField(csvElement,
						"Present Date", values, i + 5);
				HhStartDate presentDate = new HhStartDate(presentDateStr);
				String presentValueStr = GeneralImport.addField(csvElement,
						"Present Value", values, i + 6);
				BigDecimal presentValue = new BigDecimal(presentValueStr);

				String presentTypeStr = GeneralImport.addField(csvElement,
						"Present Type", values, i + 7);
				ReadType presentType = ReadType.getReadType(presentTypeStr);
				bill.insertRead(tpr, coefficient, units, meterSerialNumber,
						mpanStr, previousDate, previousValue, previousType,
						presentDate, presentValue, presentType);
			}
		} else if (action.equals("update")) {
		}
	}

	public static Bill getBill(Long id) throws HttpException {
		Bill bill = (Bill) Hiber.session().get(Bill.class, id);
		if (bill == null) {
			throw new UserException("There isn't a bill with that id.");
		}
		return bill;
	}

	private Batch batch;

	private Supply supply;

	private Date issueDate;

	private HhStartDate startDate;

	private HhStartDate finishDate;

	private BigDecimal net;

	private BigDecimal vat;

	private String account;

	private String reference;

	private Boolean isPaid; // Null is pending, false is rejected.

	private BillType type;

	private String breakdown;

	private BigDecimal kwh;

	private Set<RegisterRead> reads;

	public Bill() {
	}

	public Bill(Batch batch, Supply supply) throws HttpException {
		setBatch(batch);
		setSupply(supply);
		setReference("Default Reference");
		setAccount("Default Account");
		setType(BillType.getBillType(BillType.TYPE_NORMAL));
		setBreakdown("");
		setKwh(new BigDecimal(0));
		setNet(new BigDecimal(0));
		setVat(new BigDecimal(0));
		setIssueDate(new Date());
		setStartDate(HhStartDate.roundDown(new Date()));
		setFinishDate(HhStartDate.roundDown(new Date()));
	}

	public Batch getBatch() {
		return batch;
	}

	public void setBatch(Batch batch) {
		this.batch = batch;
	}

	public Supply getSupply() {
		return supply;
	}

	public void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Date getIssueDate() {
		return issueDate;
	}

	protected void setIssueDate(Date issueDate) {
		this.issueDate = issueDate;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	protected void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	protected void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public BigDecimal getNet() {
		return net;
	}

	void setNet(BigDecimal net) {
		this.net = net;
	}

	public BigDecimal getVat() {
		return vat;
	}

	void setVat(BigDecimal vat) {
		this.vat = vat;
	}

	public String getReference() {
		return reference;
	}

	public void setReference(String reference) {
		this.reference = reference;
	}

	public String getAccount() {
		return account;
	}

	public void setAccount(String account) {
		this.account = account;
	}

	public Boolean getIsPaid() {
		return isPaid;
	}

	public void setIsPaid(Boolean isPaid) {
		this.isPaid = isPaid;
	}

	public BillType getType() {
		return type;
	}

	public void setType(BillType type) {
		this.type = type;
	}

	public String getBreakdown() {
		return breakdown;
	}

	public void setBreakdown(String breakdown) {
		this.breakdown = breakdown;
	}

	void setKwh(BigDecimal kwh) {
		this.kwh = kwh;
	}

	public BigDecimal getKwh() {
		return kwh;
	}

	void setReads(Set<RegisterRead> reads) {
		this.reads = reads;
	}

	public Set<RegisterRead> getReads() {
		return reads;
	}

	public void update(String account, String reference, Date issueDate,
			HhStartDate startDate, HhStartDate finishDate, BigDecimal kwh,
			BigDecimal net, BigDecimal vat, BillType type, Boolean isPaid,
			String breakdown) throws HttpException {
		List<SupplyGeneration> generations = supply.getGenerations(startDate,
				finishDate);
		if (generations.isEmpty()) {
			throw new UserException("The bill is before or after the supply.");
		}
		for (SupplyGeneration generation : generations) {
			List<Long> contractIds = new ArrayList<Long>();
			HhdcContract hhdcContract = generation.getHhdcContract();
			if (hhdcContract != null) {
				contractIds.add(hhdcContract.getId());
			}
			MopContract mopContract = generation.getMopContract();
			if (mopContract != null) {
				contractIds.add(mopContract.getId());
			}
			for (Mpan mpan : generation.getMpans()) {
				contractIds.add(mpan.getSupplierContract().getId());
			}
			if (!contractIds.contains(batch.getContract().getId())) {
				throw new UserException(
						"For the bill "
								+ getId()
								+ " of batch "
								+ batch.getId()
								+ " of contract "
								+ batch.getContract().getId()
								+ " there's no matching contract for one or more of the supply generations.");
			}
		}
		setReference(reference);
		setAccount(account);
		if (issueDate == null) {
			throw new InternalException("The issue date may not be null.");
		}
		setIssueDate(issueDate);
		if (startDate.getDate().after(finishDate.getDate())) {
			throw new UserException(
					"The bill start date can't be after the finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (kwh == null) {
			throw new InternalException("kwh can't be null.");
		}
		setKwh(kwh);
		setNet(net);
		setVat(vat);
		if (type == null) {
			throw new InternalException("Type can't be null.");
		}
		setType(type);
		setIsPaid(isPaid);
		setBreakdown(breakdown);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "bill");
		element.appendChild(new MonadDate("issue", issueDate).toXml(doc));
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXml(doc));
		element.setAttribute("kwh", kwh.toString());
		element.setAttribute("net", net.toString());
		element.setAttribute("vat", vat.toString());
		element.setAttribute("reference", reference);
		if (isPaid != null) {
			element.setAttribute("is-paid", Boolean.toString(isPaid));
		}
		element.setAttribute("breakdown", breakdown);
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendSeeOther(batch.billsInstance().getUri());
		} else {
			String account = inv.getString("account");
			String reference = inv.getString("reference");
			Date issueDate = inv.getDate("issue-date");
			Date startDate = inv.getDate("start");
			Date finishDate = inv.getDate("finish");
			BigDecimal kwh = inv.getBigDecimal("kwh");
			BigDecimal net = inv.getBigDecimal("net");
			BigDecimal vat = inv.getBigDecimal("vat");
			Long typeId = inv.getLong("type-id");
			Boolean isPaid = inv.getBoolean("isPaid");
			String breakdown = inv.getString("breakdown");

			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(account, reference, issueDate, new HhStartDate(startDate)
					.getNext(), new HhStartDate(finishDate), kwh, net, vat,
					BillType.getBillType(typeId), isPaid, breakdown);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billElement = (Element) toXml(doc, new XmlTree("batch",
				new XmlTree("contract", new XmlTree("party"))).put("reads")
				.put("supply"));
		source.appendChild(billElement);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws HttpException {
		return batch.billsInstance().getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RegisterReads.URI_ID.equals(uriId)) {
			return registerReadsInstance();
		} else {
			throw new NotFoundException();
		}
	}

	public RegisterReads registerReadsInstance() {
		return new RegisterReads(this);
	}

	public RegisterRead insertRead(Tpr tpr, BigDecimal coefficient,
			Units units, String meterSerialNumber, String mpanStr,
			HhStartDate previousDate, BigDecimal previousValue,
			ReadType previousType, HhStartDate presentDate,
			BigDecimal presentValue, ReadType presentType) throws HttpException {
		RegisterRead read = new RegisterRead(this, tpr, coefficient, units,
				meterSerialNumber, mpanStr, previousDate, previousValue,
				previousType, presentDate, presentValue, presentType);
		if (reads == null) {
			reads = new HashSet<RegisterRead>();
		}
		reads.add(read);
		Hiber.flush();
		read.attach();
		return read;
	}

	public RegisterRead insertRead(RawRegisterRead rawRead)
			throws HttpException {
		return insertRead(rawRead.getTpr(), rawRead.getCoefficient(), rawRead
				.getUnits(), rawRead.getMeterSerialNumber(), rawRead
				.getMpanStr(), rawRead.getPreviousDate(), rawRead
				.getPreviousValue(), rawRead.getPreviousType(), rawRead
				.getPresentDate(), rawRead.getPresentValue(), rawRead
				.getPresentType());
	}

	public void delete() throws HttpException {
		Hiber.session().delete(this);
		Hiber.flush();
	}
}