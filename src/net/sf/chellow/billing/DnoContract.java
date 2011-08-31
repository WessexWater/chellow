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

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URI;
import java.util.List;

import javax.servlet.ServletContext;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadMessage;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class DnoContract extends Contract {
	public static DnoContract getDnoContract(Long id) throws HttpException {
		DnoContract contract = findDnoContract(id);
		if (contract == null) {
			throw new UserException("There isn't a DNO contract with that id.");
		}
		return contract;
	}

	public static DnoContract findDnoContract(Long id) throws HttpException {
		return (DnoContract) Hiber.session().get(DnoContract.class, id);
	}

	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (action.equals("insert")) {

			String dnoCode = GeneralImport.addField(csvElement, "DNO Code",
					values, 0);
			Dno dno = Dno.getDno(dnoCode);
			String idStr = GeneralImport.addField(csvElement, "Id", values, 1);
			
			Long id = null;
			if (idStr.length() > 0) {
				id = new Long(idStr);
			}
			
			String name = GeneralImport.addField(csvElement, "Name", values, 2);

			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 3);
			HhStartDate startDate = new HhStartDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 4);
			HhStartDate finishDate = null;
			if (finishDateStr.length() > 0) {
				finishDate = new HhStartDate(finishDateStr);
			}
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 5);

			String rateScriptIdStr = GeneralImport.addField(csvElement,
					"Rate Script Id", values, 6);
			Long rateScriptId = rateScriptIdStr.length() > 0 ? new Long(
					rateScriptIdStr) : null;

			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 7);
			dno.insertContract(id, name, startDate, finishDate, chargeScript,
					rateScriptId, rateScript);
		}
	}

	public static void loadFromCsv(ServletContext context) throws HttpException {
		try {
			GeneralImport process = new GeneralImport(null, context
					.getResource("/WEB-INF/dno-contracts.xml").openStream(),
					"xml");
			process.run();
			List<MonadMessage> errors = process.getErrors();
			if (!errors.isEmpty()) {
				throw new InternalException(errors.get(0).getDescription());
			}
		} catch (UnsupportedEncodingException e) {
			throw new InternalException(e);
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}

	private Dno dno;

	public DnoContract() {
	}

	public DnoContract(Dno dno, Long id, String name, HhStartDate startDate,
			HhStartDate finishDate, String chargeScript)
			throws HttpException {
		super(id, Boolean.TRUE, name, startDate, finishDate, chargeScript);
		setParty(dno);
		internalUpdate(name, chargeScript);
	}

	@Override
	public Dno getParty() {
		return dno;
	}

	void setParty(Dno dno) {
		this.dno = dno;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof DnoContract) {
			DnoContract contract = (DnoContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getEditUri() throws HttpException {
		return dno.contractsInstance().getEditUri().resolve(getUriId()).append("/");
	}

	public void delete() throws HttpException {
		super.delete();
		Hiber.session().delete(this);
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendFound(dno.contractsInstance().getEditUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
			chargeScript = chargeScript.replace("\r", "").replace("\t", "    ");
			try {
				update(name, chargeScript);
			} catch (HttpException e) {
				e.setDocument(document());
				throw e;
			}
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc, new XmlTree("party")));
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		source.appendChild(new MonadDate().toXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RateScripts.URI_ID.equals(uriId)) {
			return new RateScripts(this);
		} else {
			throw new NotFoundException();
		}
	}

	public String toString() {
		return super.toString() + " " + getParty();
	}

	public Element toXml(Document doc) throws HttpException {
		return super.toXml(doc, "dno-contract");
	}

	@Override
	public String missingBillSnagDescription() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	void onUpdate(HhStartDate from, HhStartDate to) throws HttpException {
		// TODO Auto-generated method stub
		
	}

	@Override
	public URI getViewUri() throws HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}
