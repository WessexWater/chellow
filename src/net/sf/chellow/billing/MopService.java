/*
 
 Copyright 2005 Meniscus Systems Ltd
 
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

import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhEndDate;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

@SuppressWarnings("serial")
public class MopService extends Service {
	public static MopService getMopService(Long id) throws HttpException,
			InternalException {
		MopService contract = (MopService) Hiber.session().get(
				MopService.class, id);
		if (contract == null) {
			throw new UserException
					("There isn't a meter operator contract with that id.");
		}
		return contract;
	}

	private Mop provider;

	public MopService() {
		setTypeName("mop-service");
	}

	public MopService(int type, String name, HhEndDate startDate,
			String chargeScript, Mop mop) throws HttpException,
			InternalException, DesignerException {
		super(type, name, startDate, chargeScript);
		setProvider(mop);
	}

	public Mop getProvider() {
		return provider;
	}

	void setProvider(Mop provider) {
		this.provider = provider;
	}

	public boolean equals(Object obj) {
		boolean isEqual = false;
		if (obj instanceof MopService) {
			MopService contract = (MopService) obj;
			isEqual = contract.getId().equals(getId());
		}
		return isEqual;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return provider.contractsInstance().getUri().resolve(getUriId())
				.append("/");
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException, DesignerException, DeployerException {
		int type = inv.getInteger("type");
		String name = inv.getString("name");
		String chargeScript = inv.getString("charge-script");
		if (!inv.isValid()) {
			throw new UserException(document());
		}
		update(type, name, chargeScript);
		Hiber.commit();
		inv.sendOk(document());
	}

	private Document document() throws InternalException, HttpException,
			DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc,
				new XmlTree("supplier").put("organization")));
		return doc;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			InternalException, HttpException, DeployerException {
		inv.sendOk(document());
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public String toString() {
		return "Contract id " + getId() + " " + getProvider() + " name "
				+ getName();
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub
		return null;
	}
}