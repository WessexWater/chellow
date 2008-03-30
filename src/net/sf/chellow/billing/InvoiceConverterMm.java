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

package net.sf.chellow.billing;

import java.io.IOException;
import java.io.LineNumberReader;
import java.io.Reader;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;

import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;

public class InvoiceConverterMm implements InvoiceConverter {
	private LineNumberReader lreader;

	private DateFormat dateFormat = new SimpleDateFormat("yyyyMMdd", Locale.UK);

	private List<InvoiceRaw> rawBills = new ArrayList<InvoiceRaw>();

	public InvoiceConverterMm(Reader reader) throws UserException,
			ProgrammerException {
		lreader = new LineNumberReader(reader);
	}

	public List<InvoiceRaw> getRawInvoices() throws UserException,
			ProgrammerException {
		Hiber.flush();
		if (rawBills.isEmpty()) {
			String line;
			List<List<Object>> billFields = new ArrayList<List<Object>>();
			Map<String, String> mpanLookup = new HashMap<String, String>();
			dateFormat.setTimeZone(TimeZone.getTimeZone("GMT"));
			try {
				line = lreader.readLine();
				DayStartDate startDate = null;
				DayFinishDate finishDate = null;
				String accountReference = null;
				String invoiceNumber = null;
				String recordType = null;
				double net = 0;
				double vat = 0;
				String mpanText = null;
				while (line != null) {
					recordType = getRecordType(line);
					if (!recordType.equals("0000")
							&& !recordType.equals("0050")
							&& !recordType.equals("0051")) {
						accountReference = getAccountReference(line);
						invoiceNumber = getInvoiceNumber(line);
					}
					if (recordType.equals("1460")) {
						net += Double.parseDouble(line.substring(67, 79)) / 100;
						vat += Double.parseDouble(line.substring(85, 97)) / 100;
					}
					if (recordType.equals("0461")) {
						String mpanStr;
						mpanStr = new MpanRaw(line.substring(148, 156)
								+ line.substring(135, 148)).toString();
						if (mpanText == null) {
							mpanText = mpanStr;
						} else if (mpanText.indexOf(mpanStr) == -1) {
							mpanText = mpanText + ", " + mpanStr;
						}
					}
					if (recordType.equals("0101")) {
						try {
							startDate = new DayStartDate(new HhEndDate(
									dateFormat.parse(line.substring(66, 74)))
									.getNext().getDate()).getNext();
						} catch (ParseException e) {
							throw UserException
									.newInvalidParameter("Can't parse the start date: '"
											+ e.getMessage() + "'.");
						}
						try {
							finishDate = new DayFinishDate(dateFormat
									.parse(line.substring(74, 82)));
						} catch (ParseException e) {
							throw UserException
									.newInvalidParameter("Can't parse the finish date: '"
											+ e.getMessage() + "'.");
						}
					}
					line = lreader.readLine();
					if (!recordType.equals("0000")
							&& !recordType.equals("0050")
							&& !recordType.equals("0051")) {
						String accountReferenceNext = line == null ? null
								: getAccountReference(line);
						String invoiceNumberNext = line == null ? null
								: getInvoiceNumber(line);
						if (!accountReference.equals(accountReferenceNext)
								|| !invoiceNumber.equals(invoiceNumberNext)) {
							List<Object> fields = new ArrayList<Object>();
							fields.add(accountReference);
							fields.add(mpanText);
							fields.add(invoiceNumber);
							fields.add(startDate);
							fields.add(finishDate);
							fields.add(net);
							fields.add(vat);
							billFields.add(fields);
							if (mpanLookup.get(accountReference) == null) {
								mpanLookup.put(accountReference, mpanText);
							}
							accountReference = null;
							mpanText = null;
							invoiceNumber = null;
							startDate = null;
							finishDate = null;
							recordType = null;
							net = 0;
							vat = 0;
						}
					}
				}
				lreader.close();
				Hiber.flush();
			} catch (IOException e) {
				throw UserException.newOk("Can't read EDF Energy mm file.");
			}
			for (List<Object> fields : billFields) {
				try {
					rawBills.add(new InvoiceRaw(InvoiceType.NORMAL, (String) fields.get(0), fields
							.get(1) == null ? mpanLookup.get((String) fields
							.get(0)) : (String) fields.get(1), (String) fields
							.get(2), (DayStartDate) fields.get(3), (DayStartDate) fields.get(3),
							(DayFinishDate) fields.get(4), (Double) fields
									.get(5), (Double) fields.get(6), null));
				} catch (UserException e) {
					throw UserException
							.newInvalidParameter("I'm having trouble parsing the file. The problem seems to be with the bill with account number '"
									+ (String) fields.get(0)
									+ "' and invoice number '"
									+ (String) fields.get(2)
									+ "'. "
									+ e.getMessage());
				}
			}
		}
		return rawBills;

	}

	private String getRecordType(String line) {
		return line.substring(62, 66);
	}

	private String getAccountReference(String line) {
		return line.substring(33, 41);
	}

	private String getInvoiceNumber(String line) {
		return line.substring(41, 46);
	}

	public String getProgress() {
		return "Reached line " + lreader.getLineNumber() + " of first passs.";
	}
}