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



import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadString;

public class MpanUniquePart extends MonadString {
	public MpanUniquePart() {
		setTypeName("MPANUniquePart");
		setMaximumLength(10);
		setMinimumLength(10);
		onlyDigits = true;
	}

	public MpanUniquePart(String name) throws HttpException, InternalException {
		this(null, name);
	}

	public MpanUniquePart(String label, String name) throws HttpException, InternalException
			{
		this();
		setLabel(label);
			update(name);
	}

	public void update(String mpanCore) throws InternalException, UserException {
		// remove spaces
		mpanCore = mpanCore.replace(" ", "");
		super.update(mpanCore);
	}
}