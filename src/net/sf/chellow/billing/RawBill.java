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

import java.math.BigDecimal;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadObject;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.RawRegisterRead;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class RawBill extends MonadObject {
	private String type;

	private Date issueDate;

	private HhStartDate startDate;

	private HhStartDate finishDate;

	private BigDecimal kwh;

	private BigDecimal net;

	private BigDecimal vat;

	private String accountReference;

	private String reference;
	
	private String breakdown;

	private List<String> mpanStrings;

	private Set<RawRegisterRead> reads = new HashSet<RawRegisterRead>();

	public RawBill(String type, String accountReference,
			List<String> mpanStrings, String reference, Date issueDate,
			HhStartDate startDate, HhStartDate finishDate, BigDecimal kwh, BigDecimal net,
			BigDecimal vat, String breakdown, List<RawRegisterRead> registerReads)
			throws HttpException {
		if (type == null) {
			throw new InternalException("The type can't be null.");
		}
		this.type = type;
		if (issueDate == null) {
			throw new InternalException("The issue date can't be null.");
		}
		this.issueDate = issueDate;
		if (startDate == null) {
			throw new InternalException("The start date can't be null.");
		}
		this.startDate = startDate;
		if (finishDate == null) {
			throw new InternalException("The finish date can't be null.");
		}
		this.finishDate = finishDate;
		this.kwh = kwh;
		this.net = net;
		this.vat = vat;
		if (reference == null) {
			throw new InternalException(
					"The bill reference parameter is required.");
		}
		this.reference = reference;
		if (accountReference == null) {
			throw new UserException(
					"The accountReference parameter is required.");
		}
		this.accountReference = accountReference;
		if (mpanStrings == null) {
			throw new InternalException(
					"The mpanStrings parameter must not be null.");
		}
		this.breakdown = breakdown;
		this.mpanStrings = mpanStrings;
		if (registerReads != null) {
			for (RawRegisterRead read : registerReads) {
				this.reads.add(read);
			}
		}
	}

	public String getType() {
		return type;
	}

	public List<String> getMpanStrings() {
		return mpanStrings;
	}

	public Date getIssueDate() {
		return issueDate;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}
	
	public BigDecimal getKwh() {
		return kwh;
	}
	
	public BigDecimal getNet() {
		return net;
	}

	public BigDecimal getVat() {
		return vat;
	}

	public String getReference() {
		return reference;
	}

	public String getAccount() {
		return accountReference;
	}
	
	public String getBreakdown() {
		return breakdown;
	}
	
	public Set<RawRegisterRead> getRegisterReads() {
		return reads;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = doc.createElement("raw-bill");
		element.setAttribute("reference", reference);
		element.appendChild(new MonadDate("issue", issueDate).toXml(doc));
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXml(doc));
		element.setAttribute("net", kwh.toString());
		element.setAttribute("net", net.toString());
		element.setAttribute("vat", vat.toString());
		element.setAttribute("type", type);
		element.setAttribute("account-reference", accountReference);
		StringBuilder mpans = new StringBuilder();
		for (String mpan : mpanStrings) {
			mpans.append(mpan + ", ");
		}
		if (mpans.length() > 0) {
			element.setAttribute("mpans", mpans
					.substring(0, mpans.length() - 2));
		} else {
			element.setAttribute("mpans", mpans.toString());
		}
		return element;
	}
}
