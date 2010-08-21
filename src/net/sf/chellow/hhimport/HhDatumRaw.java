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
package net.sf.chellow.hhimport;

import java.math.BigDecimal;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.physical.HhStartDate;

public class HhDatumRaw {
	private String core;

	private boolean isImport;

	private boolean isKwh;

	private HhStartDate startDate;

	private BigDecimal value;

	private char status;

	public HhDatumRaw(String core, boolean isImport, boolean isKwh,
			HhStartDate startDate, BigDecimal value, char status)
			throws HttpException {
		this.core = core;
		this.isImport = isImport;
		this.isKwh = isKwh;
		this.startDate = startDate;
		this.value = value;
		this.status = status;
	}

	public String getMpanCore() {
		return core;
	}

	public boolean getIsImport() {
		return isImport;
	}

	public boolean getIsKwh() {
		return isKwh;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	public BigDecimal getValue() {
		return value;
	}

	public char getStatus() {
		return status;
	}

	public String toString() {
		return "MPAN core: " + core + ", Is import? " + isImport + ", Is Kwh? "
				+ isKwh + ", End date " + startDate + ", Value " + value
				+ ", Status " + status;
	}
}
