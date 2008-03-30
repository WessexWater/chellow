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


import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadInteger;

public class ContractFrequency extends MonadInteger {
	private static final long serialVersionUID = 1L;
	static public final ContractFrequency DAILY;
	static public final ContractFrequency MONTHLY;

	static {
		try {
			DAILY = new ContractFrequency(0);
			MONTHLY = new ContractFrequency(1);
		} catch (UserException e) {
			throw new RuntimeException(e);
		} catch (ProgrammerException e) {
			throw new RuntimeException(e);
		}
	}

	public ContractFrequency() {
		setTypeName("frequency");
	}

	public ContractFrequency(String label, String integerString) throws UserException, ProgrammerException {
		this();
		setLabel(label);
		update(integerString);
	}
	
	public ContractFrequency(int intValue) throws UserException, ProgrammerException {
		this();
		update(intValue);
	}
}