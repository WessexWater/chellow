/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
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
import java.io.Reader;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TimeZone;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.RegisterReadRaw;
import net.sf.chellow.physical.Units;

import com.Ostermiller.util.CSVParser;

public class InvoiceConverterCsv implements InvoiceConverter {
	private static final Map<String, InvoiceType> invoiceTypeMap = Collections
			.synchronizedMap(new HashMap<String, InvoiceType>());

	static {
		invoiceTypeMap.put("A", InvoiceType.AMENDED);
		invoiceTypeMap.put("F", InvoiceType.FINAL);
		invoiceTypeMap.put("N", InvoiceType.NORMAL);
		invoiceTypeMap.put("I", InvoiceType.INTEREST);
		invoiceTypeMap.put("R", InvoiceType.RECONCILIATION);
		invoiceTypeMap.put("P", InvoiceType.PREPAID);
		invoiceTypeMap.put("O", InvoiceType.INFORMATION);
		invoiceTypeMap.put("W", InvoiceType.WITHDRAWAL);
	}

	private CSVParser shredder;

	private DateFormat dateFormat = new SimpleDateFormat("yyyy'-'MM'-'dd",
			Locale.UK);

	private List<InvoiceRaw> rawBills = new ArrayList<InvoiceRaw>();

	public InvoiceConverterCsv(Reader reader) throws HttpException,
			InternalException {
		try {
			shredder = new CSVParser(reader);
			shredder.setCommentStart("#;!");
			shredder.setEscapes("nrtf", "\n\r\t\f");
			String[] titles = shredder.getLine();

			if (titles.length < 7) {
				throw new UserException(
						"The first line of the CSV must contain the 7 titles "
								+ "'Account Text, MPAN Text, Invoice Text, Start Date, Finish Date, Net, VAT'.");
			}
			if (!titles[0].trim().toLowerCase().equals("account text")) {
				throw new UserException(
						"The title of the first column should be 'Account Text'.");
			}
			if (!titles[1].trim().toLowerCase().equals("mpan text")) {
				throw new UserException(
						"The title of the second column should be 'MPAN Text'.");
			}
			if (!titles[2].trim().toLowerCase().equals("invoice text")) {
				throw new UserException(
						"The title of the third column should be 'Invoice Text'.");
			}
			if (!titles[3].trim().toLowerCase().equals("start date")) {
				throw new UserException(
						"The title of the fouth column should be 'Start Date'.");
			}
			if (!titles[4].trim().toLowerCase().equals("finish date")) {
				throw new UserException(
						"The title of the fifth column should be 'Finish Date'.");
			}
			if (!titles[5].trim().toLowerCase().equals("net")) {
				throw new UserException(
						"The title of the sixth column should be 'Net'.");
			}
			if (!titles[6].trim().toLowerCase().equals("vat")) {
				throw new UserException(
						"The title of the seventh column should be 'VAT'.");
			}
		} catch (IOException e) {
			throw new InternalException(e);
		}
		dateFormat.setTimeZone(TimeZone.getTimeZone("GMT"));
	}

	public List<InvoiceRaw> getRawInvoices() throws HttpException,
			InternalException {
		if (rawBills.isEmpty()) {
			try {
				for (String[] values = shredder.getLine(); values != null; values = shredder
						.getLine()) {
					if (values.length < 7) {
						throw new UserException(
								"Problem at line number "
										+ shredder.getLastLineNumber()
										+ "; there aren't enough fields, there should be 7");
					}
					Set<RegisterReadRaw> reads = new HashSet<RegisterReadRaw>();
					for (int i = 9; i < values.length; i += 11) {
						reads.add(new RegisterReadRaw(MpanCore
								.getMpanCore(values[i]), Float
								.parseFloat(values[i + 1]), values[i + 2],
								Units.getUnits(values[i + 3]), Integer
										.parseInt(values[i + 4]),
								new DayFinishDate(values[i + 5]), Float
										.parseFloat(values[i + 6]), ReadType
										.getReadType(values[i + 7]),
								new DayFinishDate(values[i + 8]), Float
										.parseFloat(values[i + 9]), ReadType
										.getReadType(values[i + 10])));
					}
					Set<String> mpanStrings = new HashSet<String>();
					mpanStrings.add(values[2]);
					rawBills.add(new InvoiceRaw(invoiceTypeMap.get(values[0]),
							values[1], mpanStrings, values[3],
							new DayStartDate(values[4]), new DayStartDate(
									values[5]).getNext(), new DayFinishDate(
									values[6]), Double.parseDouble(values[7]),
							Double.parseDouble(values[8]), reads));
				}
				shredder.close();
			} catch (NumberFormatException e) {
				throw new UserException("Problem at line "
						+ shredder.getLastLineNumber()
						+ ". Can't parse number. " + e.getMessage());
			} catch (IOException e) {
				throw new UserException("Problem at line "
						+ shredder.getLastLineNumber()
						+ ". Input / output problem. " + e.getMessage());
			} catch (HttpException e) {
				throw new UserException("Problem at line "
						+ shredder.getLastLineNumber() + ". " + e.getMessage());
			}
		}
		Hiber.flush();
		return rawBills;

	}

	public String getProgress() {
		return "Reached line " + shredder.getLastLineNumber()
				+ " of first passs.";
	}
}