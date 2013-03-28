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

package net.sf.chellow.physical;

import java.util.Set;

import net.sf.chellow.billing.Contract;

public class Era extends PersistentEntity {

	private Supply supply;

	private Set<SiteEra> siteEras;

	private Set<Channel> channels;

	private HhStartDate startDate;

	private HhStartDate finishDate;
	private Contract mopContract;
	private String mopAccount;

	private Contract hhdcContract;
	private String hhdcAccount;
	private String msn;
	private Pc pc;
	private Mtc mtc;
	private Cop cop;
	private Ssc ssc;
	private Contract dnoContract;
	private Llfc impLlfc;
	private int impSc;
	private Contract impSupplierContract;
	private String impSupplierAccount;
	private String impMpanCore;
	private String expMpanCore;
	private Llfc expLlfc;
	private int expSc;
	private Contract expSupplierContract;
	private String expSupplierAccount;

	Era() {
	}

	void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Supply getSupply() {
		return supply;
	}

	public Set<SiteEra> getSiteEras() {
		return siteEras;
	}

	protected void setSiteEras(Set<SiteEra> siteEras) {
		this.siteEras = siteEras;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public Contract getMopContract() {
		return mopContract;
	}

	void setMopContract(Contract mopContract) {
		this.mopContract = mopContract;
	}

	public String getMopAccount() {
		return mopAccount;
	}

	void setMopAccount(String mopAccount) {
		this.mopAccount = mopAccount;
	}

	public Contract getHhdcContract() {
		return hhdcContract;
	}

	void setHhdcContract(Contract hhdcContract) {
		this.hhdcContract = hhdcContract;
	}

	public String getHhdcAccount() {
		return hhdcAccount;
	}

	void setHhdcAccount(String hhdcAccount) {
		this.hhdcAccount = hhdcAccount;
	}

	public Pc getPc() {
		return pc;
	}

	public String getMsn() {
		return msn;
	}

	void setMsn(String msn) {
		this.msn = msn;
	}

	void setPc(Pc pc) {
		this.pc = pc;
	}

	public Mtc getMtc() {
		return mtc;
	}

	void setMtc(Mtc mtc) {
		this.mtc = mtc;
	}

	public Cop getCop() {
		return cop;
	}

	void setCop(Cop cop) {
		this.cop = cop;
	}

	public Ssc getSsc() {
		return ssc;
	}

	void setSsc(Ssc ssc) {
		this.ssc = ssc;
	}

	public Set<Channel> getChannels() {
		return channels;
	}

	void setChannels(Set<Channel> channels) {
		this.channels = channels;
	}

	public Contract getDnoContract() {
		return dnoContract;
	}

	public void setDnoContract(Contract contract) {
		this.dnoContract = contract;
	}

	public String getImpMpanCore() {
		return impMpanCore;
	}

	public void setImpMpanCore(String impMpanCore) {
		this.impMpanCore = impMpanCore;
	}

	public String getExpMpanCore() {
		return expMpanCore;
	}

	public void setExpMpanCore(String expMpanCore) {
		this.expMpanCore = expMpanCore;
	}

	public Llfc getImpLlfc() {
		return impLlfc;
	}

	public void setImpLlfc(Llfc impLlfc) {
		this.impLlfc = impLlfc;
	}

	public int getImpSc() {
		return impSc;
	}

	public void setImpSc(int impSc) {
		this.impSc = impSc;
	}

	public Contract getImpSupplierContract() {
		return impSupplierContract;
	}

	public void setImpSupplierContract(Contract impSupplierContract) {
		this.impSupplierContract = impSupplierContract;
	}

	public String getImpSupplierAccount() {
		return impSupplierAccount;
	}

	public void setImpSupplierAccount(String impSupplierAccount) {
		this.impSupplierAccount = impSupplierAccount;
	}

	public Llfc getExpLlfc() {
		return expLlfc;
	}

	public void setExpLlfc(Llfc impLlfc) {
		this.impLlfc = impLlfc;
	}

	public int getExpSc() {
		return expSc;
	}

	public void setExpSc(int expSc) {
		this.expSc = expSc;
	}

	public Contract getExpSupplierContract() {
		return expSupplierContract;
	}

	public void setExpSupplierContract(Contract expSupplierContract) {
		this.expSupplierContract = expSupplierContract;
	}

	public String getExpSupplierAccount() {
		return expSupplierAccount;
	}

	public void setExpSupplierAccount(String expSupplierAccount) {
		this.expSupplierAccount = expSupplierAccount;
	}
}
