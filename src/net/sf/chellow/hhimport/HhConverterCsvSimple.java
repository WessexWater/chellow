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

import java.io.IOException;
import java.io.LineNumberReader;
import java.io.Reader;
import java.math.BigDecimal;
import java.text.DateFormat;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;

import com.Ostermiller.util.CSVParser;

public class HhConverterCsvSimple implements HhConverter {
	private LineNumberReader reader;

	private CSVParser shredder;

	private HhDatumRaw datum = null;

	private HhDatumRaw datumNext = null;

	String line;

	DateFormat dateFormat = DateFormat.getDateTimeInstance(DateFormat.SHORT,
			DateFormat.SHORT, Locale.UK);

	public HhConverterCsvSimple(Reader reader) throws HttpException,
			InternalException {
		dateFormat.setTimeZone(TimeZone.getTimeZone("GMT"));
		try {
			shredder = new CSVParser(reader);
			shredder.setCommentStart("#;!");
			shredder.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = shredder.getLine();

			if (titles.length < 6 || !titles[0].equals("MPAN core")
					|| !titles[1].equals("Imp / Exp")
					|| !titles[2].equals("Units") || !titles[3].equals("Time")
					|| !titles[4].equals("Value")
					|| !titles[5].equals("Status")) {
				throw new UserException(
						"The first line of the CSV must contain the titles "
								+ "MPAN core, Imp / Exp, Units, Time, Value, Status.");
			}
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
		} catch (IOException e) {
			throw new UserException("Can't read CSV Simple file.");
		}
	}

	public boolean hasNext() {
		return datumNext != null;
	}

	public void remove() {
		throw new UnsupportedOperationException();
	}

	public HhDatumRaw next() {
		HhDatumRaw datum = null;
		this.datum = datumNext;
		try {
			String[] values = shredder.getLine();
			if (values.length < 5) {
				throw new UserException(
						"There must be fields for 'MPAN core', 'Imp / Exp', 'Units', 'Time' and 'Value'.");
			}
			Character status = null;
			if (values.length > 5) {
				status = values[5].trim().charAt(0);
			}
			datum = new HhDatumRaw(values[0], Boolean.parseBoolean(values[1]), Boolean.parseBoolean(values[2]), new HhEndDate(values[3]),
					new BigDecimal(values[4]), status);
			datumNext = datum;
			return this.datum;
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
		return reader.getLineNumber();
	}

	public void close() throws InternalException {
		try {
			reader.close();
		} catch (IOException e) {
			throw new InternalException(e);
		}
	}
}
