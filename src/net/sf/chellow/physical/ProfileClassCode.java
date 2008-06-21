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

import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.Locale;

import org.w3c.dom.Attr;
import org.w3c.dom.Document;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadInteger;

public class ProfileClassCode extends MonadInteger {
	public ProfileClassCode() {
		init();
	}

	public ProfileClassCode(int code) throws HttpException,
			InternalException {
		this(null, code);
	}

	public ProfileClassCode(String label, int code) throws HttpException,
			InternalException {
		init();
		setLabel(label);
		update(code);
	}

	private void init() {
		setTypeName("ProfileClassCode");
		setMaximum(8);
		setMinimum(0);
	}

	public void update(String code) throws InternalException, UserException {
		NumberFormat profileClassCodeFormat = NumberFormat
				.getIntegerInstance(Locale.UK);
		profileClassCodeFormat.setMinimumIntegerDigits(2);
		super.update(profileClassCodeFormat.format(Integer.parseInt(code.trim())));
	}
	
	public Attr toXml(Document doc) {
		Attr attr = doc.createAttribute("code");
		attr.setValue(toString());
		return attr;
	}
	
	public String toString() {
		DecimalFormat pcFormat = new DecimalFormat("00");
		return pcFormat.format(getInteger());
	}
}