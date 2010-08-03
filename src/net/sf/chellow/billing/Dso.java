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

public class Dso extends Party {
	static public Dso getDso(Long id) throws HttpException {
		Dso dso = (Dso) Hiber.session().get(Dso.class, id);
		if (dso == null) {
			throw new UserException("There is no DSO with the id '" + id + "'.");
		}
		return dso;
	}

	static public Dso getDso(Participant participant) throws HttpException {
		Dso dso = (Dso) Hiber
				.session()
				.createQuery(
						"from Dso dso where dso.participant = :participant and dso.validTo is null")
				.setEntity("participant", participant).uniqueResult();
		if (dso == null) {
			throw new UserException("There is no DSO with the participant '"
					+ participant.getCode() + "'.");
		}
		return dso;
	}

	static public Dso getDso(String code) throws HttpException {
		Dso dso = findDso(code);
		if (dso == null) {
			throw new UserException("There is no DSO with the code '" + code
					+ "'.");
		}
		return dso;
	}

	static public Dso findDso(String code) throws HttpException {
		return (Dso) Hiber.session().createQuery(
				"from Dso dso where dso.code = :code").setString("code", code)
				.uniqueResult();
	}

	private String code;

	public Dso(String name, Participant participant, Date validFrom,
			Date validTo, String code) throws HttpException {
		super(name, participant, MarketRole.DISTRIBUTOR, validFrom, validTo);
		setCode(code);
	}

	public Dso() {
		super();
	}

	void setCode(String code) {
		this.code = code;
	}

	public String getCode() {
		return code;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "dso");
		element.setAttribute("code", code.toString());
		return element;
	}

	public Llfc getLlfc(String code, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dso", this).setInteger("code",
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
		Llfc llfc = (Llfc) Hiber.session().createQuery(
				"from Llfc llfc where llfc.dso = :dso and llfc.code = :code")
				.setEntity("dso", this).setInteger("code",
						Integer.parseInt(code)).uniqueResult();
		if (llfc == null) {
			throw new UserException("There is no LLFC with the code " + code
					+ " associated with the DSO " + getCode() + ".");
		}
		return llfc;
	}

	public DsoContracts contractsInstance() {
		return new DsoContracts(this);
	}

	public DsoContract insertContract(Long id, String name,
			HhStartDate startDate, HhStartDate finishDate, String chargeScript,
			Long rateScriptId, String rateScript) throws HttpException {
		DsoContract contract = findContract(name);
		if (contract == null) {
			contract = new DsoContract(this, id, name, startDate, finishDate,
					chargeScript);
		} else {
			throw new UserException(
					"There is already a DSO contract with this name.");
		}
		Hiber.session().save(contract);
		Hiber.flush();
		contract.insertFirstRateScript(rateScriptId, startDate, finishDate, rateScript);
		return contract;
	}

	public DsoContract findContract(String name) throws HttpException {
		return (DsoContract) Hiber
				.session()
				.createQuery(
						"from DsoContract contract where contract.party = :dso and contract.name = :contractName")
				.setEntity("dso", this).setString("contractName", name)
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
		} else if (DsoContracts.URI_ID.equals(uriId)) {
			return new DsoContracts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public DsoContract getContract(String name) throws HttpException {
		DsoContract contract = (DsoContract) Hiber
				.session()
				.createQuery(
						"from DsoContract contract where contract.party.id = :dsoId and contract.name = :name")
				.setLong("dsoId", getId()).setString("name", name)
				.uniqueResult();
		if (contract == null) {
			throw new NotFoundException("DSO contract not found.");
		}
		return contract;
	}

	@Override
	public MonadUri getUri() throws HttpException {
		return Chellow.DSOS_INSTANCE.getUri().resolve(getUriId()).append("/");
	}
}
