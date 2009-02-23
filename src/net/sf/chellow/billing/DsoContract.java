/*
 
 Copyright 2005-2009 Meniscus Systems Ltd
 
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

import java.io.IOException;
import java.io.UnsupportedEncodingException;
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
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.ui.GeneralImport;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class DsoContract extends Contract {
	public static DsoContract getDsoContract(Long id) throws HttpException {
		DsoContract contract = findDsoContract(id);
		if (contract == null) {
			throw new UserException("There isn't a DSO contract with that id.");
		}
		return contract;
	}

	public static DsoContract findDsoContract(Long id) throws HttpException {
		return (DsoContract) Hiber.session().get(DsoContract.class, id);
	}

	static public void generalImport(String action, String[] values,
			Element csvElement) throws HttpException {
		if (values.length < 6) {
			throw new UserException("There aren't enough fields in this row");
		}
		String dsoCode = GeneralImport.addField(csvElement,
				"DSO Code", values, 0);
		Dso dso = Dso.getDso(dsoCode);
		String name = GeneralImport.addField(csvElement, "Name", values, 1);

		if (action.equals("insert")) {
			String startDateStr = GeneralImport.addField(csvElement,
					"Start Date", values, 2);
			HhEndDate startDate = new HhEndDate(startDateStr);
			String finishDateStr = GeneralImport.addField(csvElement,
					"Finish Date", values, 3);
			HhEndDate finishDate = null;
			if (finishDateStr.length() > 0) {
				finishDate = new HhEndDate(finishDateStr);
			}
			String chargeScript = GeneralImport.addField(csvElement,
					"Charge Script", values, 4);
			String rateScript = GeneralImport.addField(csvElement,
					"Rate Script", values, 5);
			dso.insertContract(name, startDate, finishDate, chargeScript,
					rateScript);
		}
	}
	
	public static void loadFromCsv(ServletContext context) throws HttpException {
		try {
			GeneralImport process = new GeneralImport(null, context
					.getResource("/WEB-INF/mdd/dso-contracts.xml").openStream(), "xml");
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

	private Dso dso;

	public DsoContract() {
	}

	public DsoContract(Dso dso, String name, HhEndDate startDate,
			HhEndDate finishDate, String chargeScript, String rateScript)
			throws HttpException {
		super(name, startDate, finishDate, chargeScript, rateScript);
		setParty(dso);
		internalUpdate(name, chargeScript);
	}

	@Override
	public Dso getParty() {
		return dso;
	}

	void setParty(Dso dso) {
		this.dso = dso;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof DsoContract) {
			DsoContract contract = (DsoContract) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws HttpException {
		return dso.contractsInstance().getUri().resolve(getUriId()).append("/");
	}

	public void delete() throws HttpException {
		super.delete();
		Hiber.session().delete(this);
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendFound(dso.contractsInstance().getUri());
		} else {
			String name = inv.getString("name");
			String chargeScript = inv.getString("charge-script");
			if (!inv.isValid()) {
				throw new UserException(document());
			}
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
		return super.toXml(doc, "dso-contract");
	}
}