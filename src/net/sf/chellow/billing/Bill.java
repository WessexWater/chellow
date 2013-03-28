/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2012 Wessex Water Services Limited
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
import java.util.Set;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.RegisterRead;
import net.sf.chellow.physical.Supply;

public class Bill extends PersistentEntity {
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

	private BigDecimal gross;

	private String account;

	private String reference;

	private BillType type;

	private String breakdown;

	private BigDecimal kwh;

	private Set<RegisterRead> reads;

	public Bill() {
	}

	public Bill(Batch batch, Supply supply, String account, String reference,
			Date issueDate, HhStartDate startDate, HhStartDate finishDate,
			BigDecimal kwh, BigDecimal net, BigDecimal vat, BigDecimal gross,
			BillType type, String breakdown) throws HttpException {
		setBatch(batch);
		setSupply(supply);
		update(account, reference, issueDate, startDate, finishDate, kwh, net,
				vat, gross, type, breakdown);
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

	public BigDecimal getGross() {
		return gross;
	}

	void setGross(BigDecimal gross) {
		this.gross = gross;
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
			BigDecimal net, BigDecimal vat, BigDecimal gross, BillType type,
			String breakdown) throws HttpException {
		setReference(reference);
		setAccount(account);
		if (issueDate == null) {
			throw new InternalException("The issue date may not be null.");
		}
		setIssueDate(issueDate);
		if (startDate.getDate().after(finishDate.getDate())) {
			throw new UserException("The bill start date " + startDate
					+ " can't be after the finish date " + finishDate + ".");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (kwh == null) {
			throw new InternalException("kwh can't be null.");
		}
		setKwh(kwh);
		setNet(net);
		setVat(vat);
		setGross(gross);
		if (type == null) {
			throw new InternalException("Type can't be null.");
		}
		setType(type);
		setBreakdown(breakdown);
	}
}