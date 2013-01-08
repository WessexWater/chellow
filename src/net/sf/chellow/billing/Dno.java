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

import java.net.URI;
import java.util.Date;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.Llfc;
import net.sf.chellow.physical.Llfcs;
import net.sf.chellow.physical.MarketRole;
import net.sf.chellow.physical.Participant;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dno extends Party {
	static public Dno getDno(Long id) throws HttpException {
		Dno dno = (Dno) Hiber.session().get(Dno.class, id);
		if (dno == null) {
			throw new UserException("There is no DNO with the id '" + id + "'.");
		}
		return dno;
	}

	static public Dno getDno(Participant participant) throws HttpException {
		Dno dno = (Dno) Hiber
				.session()
				.createQuery(
						"from Dno dno where dno.participant = :participant and dno.validTo is null")
				.setEntity("participant", participant).uniqueResult();
		if (dno == null) {
			throw new UserException("There is no DNO with the participant '"
					+ participant.getCode() + "'.");
		}
		return dno;
	}

	static public Dno getDno(String code) throws HttpException {
		Dno dno = findDno(code);
		if (dno == null) {
			throw new UserException("There is no DNO with the code '" + code
					+ "'.");
		}
		return dno;
	}

	static public Dno findDno(String code) throws HttpException {
		return (Dno) Hiber.session().createQuery(
				"from Dno dno where dno.code = :code").setString("code", code)
				.uniqueResult();
	}

	private String code;

	public Dno(String name, Participant participant, Date validFrom,
			Date validTo, String code) throws HttpException {
		super(name, participant, MarketRole.DISTRIBUTOR, validFrom, validTo);
		setCode(code);
	}

	public Dno() {
		super();
	}

	void setCode(String code) {
		this.code = code;
	}

	public String getCode() {
		return code;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "dno");
		element.setAttribute("code", code.toString());
		return element;
	}

	public Llfc getLlfc(String code, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dno = :dno and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dno", this).setInteger("code",
						Integer.parseInt(code)).setTimestamp("date", date)
				.uniqueResult();
		if (llfc == null) {
			throw new UserException(
					"There is no line loss factor with the code " + code
							+ " associated with the DNO '"
							+ getCode().toString() + "' for the date "
							+ date.toString() + ".");
		}
		return llfc;
	}

	public Llfc getLlfc(String code) throws HttpException {
		Integer llfcInt = null;
		try {
			llfcInt = Integer.parseInt(code);
		} catch (NumberFormatException e) {
			throw new UserException(
					"The LLFC must be an integer between 0 and 999.");
		}

		Llfc llfc = (Llfc) Hiber.session().createQuery(
				"from Llfc llfc where llfc.dno = :dno and llfc.code = :code")
				.setEntity("dno", this).setInteger("code", llfcInt)
				.uniqueResult();
		if (llfc == null) {
			throw new UserException("There is no LLFC with the code " + code
					+ " associated with the DNO " + getCode() + ".");
		}
		return llfc;
	}

	public DnoContracts contractsInstance() {
		return new DnoContracts(this);
	}

	public DnoContract insertContract(Long id, String name,
			HhStartDate startDate, HhStartDate finishDate, String chargeScript,
			Long rateScriptId, String rateScript) throws HttpException {
		DnoContract contract = findContract(name);
		if (contract == null) {
			contract = new DnoContract(this, id, name, startDate, finishDate,
					chargeScript);
		} else {
			throw new UserException(
					"There is already a DNO contract with this name.");
		}
		Hiber.session().save(contract);
		Hiber.flush();
		contract.insertFirstRateScript(rateScriptId, startDate, finishDate,
				rateScript);
		return contract;
	}

	public DnoContract findContract(String name) throws HttpException {
		return (DnoContract) Hiber
				.session()
				.createQuery(
						"from DnoContract contract where contract.party = :dno and contract.name = :contractName")
				.setEntity("dno", this).setString("contractName", name)
				.uniqueResult();
	}

	@Override
	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("participant").put("role")));
		inv.sendOk(doc);
	}

	@Override
	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (Llfcs.URI_ID.equals(uriId)) {
			return new Llfcs(this);
		} else if (DnoContracts.URI_ID.equals(uriId)) {
			return new DnoContracts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public DnoContract getContract(String name) throws HttpException {
		DnoContract contract = (DnoContract) Hiber
				.session()
				.createQuery(
						"from DnoContract contract where contract.party.id = :dnoId and contract.name = :name")
				.setLong("dnoId", getId()).setString("name", name)
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException("DNO contract not found.");
		}
		return contract;
	}

	@Override
	public MonadUri getEditUri() throws HttpException {
		return Chellow.DNOS_INSTANCE.getEditUri().resolve(getUriId()).append("/");
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
