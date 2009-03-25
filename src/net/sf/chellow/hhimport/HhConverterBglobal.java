/*
 
 Copyright 2009 Meniscus Systems Ltd
 
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

package net.sf.chellow.hhimport;

import java.io.IOException;
import java.io.Reader;
import java.math.BigDecimal;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.physical.HhDatum;
import net.sf.chellow.physical.HhEndDate;

import com.Ostermiller.util.CSVParser;

public class HhConverterBglobal implements HhConverter {

	private CSVParser shredder;

	private HhDatumRaw datum = null;

	private HhDatumRaw datumNext = null;

	private int hhIndex = 48;

	private String[] values = null;

	private SimpleDateFormat dateFormat = new SimpleDateFormat("dd/MM/yyyy",
			Locale.UK);

	private Calendar cal = MonadDate.getCalendar();

	public HhConverterBglobal(Reader reader) throws HttpException {
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

	public HhDatumRaw next() {
		HhDatumRaw datum = null;
		this.datum = datumNext;
		try {
			if (hhIndex > 47) {
				values = shredder.getLine();
				if (values != null && values.length < 51) {
					throw new UserException(
							"There must be fields for MPAN Core, Meter Serial Number, Date and the 48 HH values.");
				}
				hhIndex = 0;
			}
			while (values != null && datum == null) {
				try {
					Date date = dateFormat.parse(values[2]);
					cal.setTime(date);
					cal.add(Calendar.MINUTE, 30 * (hhIndex + 1));
					String hhValue = values[hhIndex + 3].trim();
					if (hhValue.length() > 0) {
						datum = new HhDatumRaw(values[0], true, true,
								new HhEndDate(cal.getTime()), new BigDecimal(
										hhValue), HhDatum.ACTUAL);
					}
				} catch (NumberFormatException e) {
					throw new UserException("Problem formatting value. "
							+ e.getMessage());
				} catch (ParseException e) {
					throw new UserException("Problem parsing date. "
							+ e.getMessage());
				}
				hhIndex++;
			}
			datumNext = datum;
			// Debug.print("returning " + this.datum);
			return this.datum;
		} catch (IOException e) {
			throw new RuntimeException(e);
		} catch (InternalException e) {
			throw new RuntimeException(e);
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
