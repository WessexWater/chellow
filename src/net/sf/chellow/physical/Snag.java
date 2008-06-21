/*
 
 Copyright 2005-2007 Meniscus Systems Ltd
 
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

import java.util.Date;

import net.sf.chellow.billing.Service;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.types.MonadBoolean;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadString;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public abstract class Snag extends PersistentEntity implements Cloneable,
		Urlable {

	static public Snag getSnag(Long id) throws InternalException, NotFoundException {
		Snag snag = (Snag) Hiber.session().get(Snag.class, id);
		if (snag == null) {
			throw new NotFoundException();
		}
		return snag;
	}

	static public Snag getSnag(String id) throws InternalException, NotFoundException {
		return getSnag(Long.parseLong(id));
	}

	private Date dateCreated;

	private Date dateResolved;

	private boolean isIgnored;

	private String description;

	private String progress;

	public Snag() {
	}

	public Snag(String description) throws InternalException {
		setDateCreated(new Date());
		this.description = description;
		this.isIgnored = false;
		this.progress = "";
	}

	public Date getDateCreated() {
		return dateCreated;
	}

	void setDateCreated(Date dateCreated) {
		this.dateCreated = dateCreated;
	}

	public Date getDateResolved() {
		return dateResolved;
	}

	public void setDateResolved(Date dateResolved) {
		this.dateResolved = dateResolved;
	}

	public boolean getIsIgnored() {
		return isIgnored;
	}

	public void setIsIgnored(boolean isIgnored) {
		this.isIgnored = isIgnored;
		
	}

	public String getDescription() {
		return description;
	}

	void setDescription(String description) {
		this.description = description;
	}

	public String getProgress() {
		return progress;
	}

	void setProgress(String progress) {
		this.progress = progress;
	}

	public void resolve(boolean isIgnored) throws InternalException {
		setDateResolved(new Date());
		setIsIgnored(isIgnored);
	}

	public void deResolve() {
		setDateResolved(null);
		setIsIgnored(false);
	}

	public void update() {
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = (Element) super.toXml(doc);
		element.appendChild(MonadDate.toXML(dateCreated, "created", doc));
		if (dateResolved != null) {
			element.appendChild(MonadDate.toXML(dateResolved, "resolved", doc));
		}
		element.setAttributeNode(MonadBoolean.toXml(doc, "is-ignored", isIgnored));
		element.setAttributeNode(MonadString.toXml(doc, "progress", progress));
		element.setAttributeNode(MonadString.toXml(doc, "description", description));
		return element;
	}

	public Snag copy() throws InternalException {
		Snag cloned;
		try {
			cloned = (Snag) super.clone();
		} catch (CloneNotSupportedException e) {
			throw new InternalException(e);
		}
		cloned.setId(null);
		return cloned;
	}

	public Urlable getChild(UriPathElement uriId) throws InternalException, NotFoundException {
		throw new NotFoundException();
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("ignore")) {
			boolean ignore = inv.getBoolean("ignore");
			boolean ignored = getIsIgnored();
			if (ignored != ignore) {
				if (ignore && this.getDateResolved() == null) {
					resolve(true);
				}
				if (!ignore) {
					deResolve();
				}
			}
			Hiber.commit();
			inv.sendSeeOther(getUri());
		}
	}

	public abstract Service getService();

	public abstract void setService(Service service);
}