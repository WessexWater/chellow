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

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Mpan;
import net.sf.chellow.physical.SnagDateBounded;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class MpanSnag extends SnagDateBounded {
	public static final String MISSING_BILL = "Missing bill.";

	public static MpanSnag getAccountSnag(Long id) throws HttpException {
		MpanSnag snag = (MpanSnag) Hiber.session().get(MpanSnag.class,
				id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	public static void insertSnagAccount(MpanSnag snag) {
		Hiber.session().save(snag);
	}

	public static void deleteAccountSnag(MpanSnag snag) {
		Hiber.session().delete(snag);
	}

	private Mpan mpan;

	public MpanSnag() {
	}

	public MpanSnag(String description, Mpan mpan,
			HhEndDate startDate, HhEndDate finishDate) throws HttpException {
		super(description, startDate, finishDate);
		this.mpan = mpan;
	}

	public Mpan getMpan() {
		return mpan;
	}

	void setMpan(Mpan mpan) {
		this.mpan = mpan;
	}

	public void update() {
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "account-snag");
		return element;
	}

	public MpanSnag copy() throws InternalException {
		MpanSnag cloned;
		try {
			cloned = (MpanSnag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return super.toString();
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(toXml(doc, new XmlTree("account",
				new XmlTree("contract", new XmlTree("party")))));
		return doc;
	}

	public MonadUri getUri() throws HttpException {
		return new MpanSnags(mpan).getUri()
				.resolve(getUriId()).append("/");
	}
}
