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

package net.sf.chellow.physical;

import net.sf.chellow.billing.DceService;
import net.sf.chellow.billing.Service;
import net.sf.chellow.monad.DeployerException;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadUri;

import org.w3c.dom.Document;
import org.w3c.dom.Element;


public class SnagChannel extends SnagDateBounded {
	public static final long SNAG_CHECK_LEAD_TIME = 1000 * 60 * 60 * 24 * 5;

	public static final String SNAG_NEGATIVE = "Negative values.";

	public static final String SNAG_NOT_ACTUAL = "Not actual reads.";

	public static final String SNAG_MISSING = "Missing.";
	
	public static final String SNAG_DATA_IGNORED = "Data ignored.";

	public static void insertSnagChannel(SnagChannel snag) {
		Hiber.session().save(snag);
	}

	public static void deleteSnagChannel(SnagChannel snag) {
		Hiber.session().delete(snag);
	}

	private Channel channel;
	
	private DceService dceService;

	public SnagChannel() {
		setTypeName("snag-channel");
	}

	public SnagChannel(String description, DceService dceService,
			Channel channel, HhEndDate startDate, HhEndDate finishDate)
			throws ProgrammerException, UserException {
		super(description, startDate, finishDate);
		this.channel = channel;
		this.dceService = dceService;
	}

	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}
/*
	public void resolve(boolean isIgnored) throws ProgrammerException,
			UserException {
		setDateResolved(new MonadDate());
		setIsIgnored(new MonadBoolean(isIgnored));
	}
*/
	public void update() {
	}

	public Element toXML(Document doc) throws ProgrammerException, UserException {
		Element element = (Element) super.toXML(doc);
		return element;
	}

	public SnagChannel copy() throws ProgrammerException {
		SnagChannel cloned;
		try {
			cloned = (SnagChannel) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new ProgrammerException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public String toString() {
		return super.toString() + " Contract: " + getService();
	}
	
	public DceService getService() {
		return dceService;
	}
	
	public void setService(DceService dceService) {
		this.dceService = dceService;
	}

	public void httpGet(Invocation inv) throws DesignerException,
			ProgrammerException, UserException, DeployerException {
		inv.sendOk(document());
	}

	private Document document() throws ProgrammerException, UserException, DesignerException {
		Document doc = MonadUtils.newSourceDocument();
		Element sourceElement = doc.getDocumentElement();
		sourceElement.appendChild(getXML(new XmlTree("service", new XmlTree(
				"provider", new XmlTree("organization"))).put("channel",
				new XmlTree("supply")), doc));
		return doc;
	}

	public void httpDelete(Invocation inv) throws ProgrammerException,
			DesignerException, UserException, DeployerException {
		// TODO Auto-generated method stub

	}

	public MonadUri getUri() throws ProgrammerException, UserException {
		return getService().getSnagsChannelInstance().getUri().resolve(
				getUriId()).append("/");
	}

	@Override
	public void setService(Service service) {
		setService((DceService) service);
	}
}
