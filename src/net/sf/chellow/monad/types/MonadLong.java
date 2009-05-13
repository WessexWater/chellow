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

package net.sf.chellow.monad.types;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.MonadMessage;
import org.w3c.dom.Document;
import org.w3c.dom.Node;

public class MonadLong extends MonadObject {
	private Long longValue;

	private Long min = null;

	private Long max = null;

	public MonadLong(String name, String longValue) throws HttpException {
		super("Long", name);

		try {
			setLong(new Long(longValue));
		} catch (NumberFormatException e) {
			throw new UserException(
					"malformed_integer");
		}
	}

	protected MonadLong(String name, long longValue) throws HttpException,
			InternalException {
		super("Long", name);
		setLong(new Long(longValue));
	}

	protected void setMax(Long max) {
		this.max = max;
	}

	protected void setMin(Long min) {
		this.min = min;
	}

	public MonadLong(String stringValue) throws HttpException,
			InternalException {
		this(null, stringValue);
	}

	public MonadLong(long longValue) throws HttpException, InternalException {
		this(null, longValue);
	}

	public Long getLong() {
		return longValue;
	}

	public void setLong(Long longValue) throws HttpException,
			InternalException {

		if ((min != null) && (longValue.longValue() < min.longValue())) {
			throw new UserException(
					MonadMessage.NUMBER_TOO_SMALL);
		}
		if ((max != null) && (longValue.longValue() < max.longValue())) {
			throw new UserException(
					MonadMessage.NUMBER_TOO_BIG);
		}
		this.longValue = longValue;
	}

	public Node toXml(Document doc) {
		Node node = doc.createAttribute(getLabel());

		node.setNodeValue(longValue.toString());
		return node;
	}

	public String toString() {
		return longValue.toString();
	}
}
