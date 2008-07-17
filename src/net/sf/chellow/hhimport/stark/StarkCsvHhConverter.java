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

package net.sf.chellow.hhimport.stark;

import java.io.IOException;
import java.io.LineNumberReader;
import java.io.Reader;
import java.text.DateFormat;
import java.text.ParseException;
import java.util.Locale;
import java.util.TimeZone;

import net.sf.chellow.data08.HhDatumRaw;
import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.hhimport.HhConverter;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhDatumStatus;
import net.sf.chellow.physical.HhEndDate;

import com.Ostermiller.util.CSVParser;

public class StarkCsvHhConverter implements HhConverter {
	private LineNumberReader reader;

	private CSVParser shredder;

	private HhDatumRaw datum = null;

	private HhDatumRaw datumNext = null;

	private DateFormat dateFormat = DateFormat.getDateTimeInstance(
			DateFormat.SHORT, DateFormat.SHORT, Locale.UK);

	public StarkCsvHhConverter(Reader reader) throws HttpException,
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
				throw new UserException("The first line of the CSV must contain the titles "
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
			if (values != null) {
				if (values.length < 5) {
					throw new UserException("There must be fields for 'MPAN core', 'Imp / Exp', 'Units', 'Time' and 'Value'.");
				}
				MpanCoreRaw core = new MpanCoreRaw(values[0]);
				boolean isImport = values[1].equals("0");
				boolean isKwh;
				if (values[2].trim().equals("kWh")) {
					isKwh = true;
				} else if (values[2].trim().equals("kVArh")) {
					isKwh = false;
				} else {
					throw new UserException("The 'Units' field must be 'kWh' or 'kVArh'");
				}
				HhEndDate endDate = new HhEndDate(dateFormat.parse(values[3]));
				float value = Float.parseFloat(values[4]);
				HhDatumStatus status = null;
				if (values.length > 5) {
					char statusChar = 'E';
					if (values[5].equals("65")) {
						statusChar = 'A';
					}
					status = new HhDatumStatus(statusChar);
				}
				datum = new HhDatumRaw(core, isImport, isKwh, endDate, value,
						status);
			}
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
				throw new RuntimeException(new UserException("Problem at line number: "
								+ shredder.getLastLineNumber() + ". Problem: "
								+ e.getMessage()));
			} catch (InternalException e1) {
				throw new RuntimeException(e1);
			}
		} catch (ParseException e) {
			RuntimeException rte = new RuntimeException();
			rte.initCause(e);
			throw rte;
		}
	}

	public int lastLineNumber() {
		return shredder == null ? 0 : shredder.getLastLineNumber();
	}

	public void close() throws InternalException {
		if (reader != null) {
			try {
				reader.close();
			} catch (IOException e) {
				throw new InternalException(e);
			}
		}
	}
}
