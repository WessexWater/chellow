/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2010 Wessex Water Services Limited
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

import java.io.IOException;
import java.io.Reader;
import java.math.BigDecimal;
import java.text.DateFormat;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhStartDate;

import com.Ostermiller.util.CSVParser;

public class HhConverterCsvSimple implements HhConverter {

	private CSVParser shredder;

	private HhDatumRaw datumNext = null;

	String line;

	DateFormat dateFormat = DateFormat.getDateTimeInstance(DateFormat.SHORT,
			DateFormat.SHORT, Locale.UK);

	public HhConverterCsvSimple(Reader reader) throws HttpException {
		dateFormat.setTimeZone(TimeZone.getTimeZone("GMT"));
		shredder = new CSVParser(reader);
		shredder.setCommentStart("#;!");
		shredder.setEscapes("nrtf", "\n\r\t\f");

		try {
			next();
		} catch (RuntimeException e) {
			if (e.getCause() != null) {
				Throwable t = e.getCause();
				if (t instanceof HttpException) {
					throw (HttpException) t;
				} else {
					throw new InternalException(t);
				}
			} else {
				throw e;
			}
		}
	}

	public boolean hasNext() {
		return datumNext != null;
	}

	public void remove() {
		throw new UnsupportedOperationException();
	}

	private String getField(String[] values, int index, String name)
			throws UserException, InternalException {
		if (values.length > index) {
			return values[index].trim();
		} else {
			throw new UserException("Can't find field " + index + ", " + name
					+ ".");
		}
	}

	public HhDatumRaw next() {
		HhDatumRaw datum = null;
		try {
			String[] values = shredder.getLine();
			if (values != null) {
				String mpanCore = getField(values, 0, "Mpan Core");

				String isImportStr = getField(values, 1, "Is Import?");
				boolean isImport = Boolean.parseBoolean(isImportStr);

				String isKwhStr = getField(values, 2, "Is kWh?");
				boolean isKwh = Boolean.parseBoolean(isKwhStr);

				String startDateStr = getField(values, 3, "Start Date");
				HhStartDate startDate = new HhStartDate(startDateStr);

				String valueStr = getField(values, 4, "Value");
				BigDecimal value = new BigDecimal(valueStr);

				String statusStr = getField(values, 5, "Status");
				if (statusStr.length() != 1) {
					throw new UserException(
							"The status character must be one character in length.");
				}
				char status = statusStr.charAt(0);

				datum = new HhDatumRaw(mpanCore, isImport, isKwh, startDate,
						value, status);
			}
			HhDatumRaw toReturn = datumNext;
			datumNext = datum;
			return toReturn;
		} catch (IOException e) {
			RuntimeException rte = new RuntimeException();
			rte.initCause(e);
			throw rte;
		} catch (InternalException e) {
			RuntimeException rte = new RuntimeException();
			rte.initCause(e);
			throw rte;
		} catch (HttpException e) {
			try {
				throw new RuntimeException(new UserException(
						"Problem at line number: "
								+ shredder.getLastLineNumber() + ". Problem: "
								+ e.getMessage()));
			} catch (InternalException e1) {
				throw new RuntimeException(e1);
			}
		}
	}

	public int lastLineNumber() {
		return shredder.getLastLineNumber();
	}

	public void close() throws InternalException {
		try {
			shredder.close();
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}
}
