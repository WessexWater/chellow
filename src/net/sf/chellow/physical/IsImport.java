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

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

import net.sf.chellow.monad.types.MonadBoolean;

public class IsImport extends MonadBoolean {
	static public final IsImport TRUE = new IsImport(true);
	static public final IsImport FALSE = new IsImport(false);

	public IsImport() {
	}

	public IsImport(boolean isImport) {
		update(isImport);
	}

	public IsImport(String isImport) {
		update(isImport);
	}

	public IsImport(String label, boolean isImport) {
		setLabel(label);
		update(isImport);
	}

	public Attr toXml(Document doc) {
		setLabel("is-import");
		return super.toXml(doc);
	}
}