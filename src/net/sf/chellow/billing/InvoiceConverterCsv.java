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

package net.sf.chellow.billing;

import java.io.IOException;
import java.io.Reader;
import java.math.BigDecimal;
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
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
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
			String[] desiredTitles = new String[] { "InvoiceType",
					"Account Reference", "Mpans", "Invoice Reference",
					"Issue Date", "Start Date", "Finish Date", "Net", "VAT" };
			if (titles.length < desiredTitles.length) {
				throw new UserException(
						"The first line of the CSV must contain at least "
								+ desiredTitles.length + " titles.");
			}
			for (int i = 0; i < desiredTitles.length; i++) {
				if (!titles[i].trim().toLowerCase().equals(
						desiredTitles[i].trim().toLowerCase())) {
					throw new UserException("The title of column " + i
							+ " should be '" + desiredTitles[i] + "'.");
				}
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
								.getMpanCore(values[i]), new BigDecimal(
								values[i + 1]), values[i + 2], Units
								.getUnits(values[i + 3]), Integer
								.parseInt(values[i + 4]), new DayFinishDate(
								values[i + 5]), new BigDecimal(values[i + 6]),
								ReadType.getReadType(values[i + 7]),
								new DayFinishDate(values[i + 8]),
								new BigDecimal(values[i + 9]), ReadType
										.getReadType(values[i + 10])));
					}
					Set<String> mpanStrings = new HashSet<String>();
					for (String mpanStr : values[2].split(",")) {
						mpanStrings.add(mpanStr);
					}
					rawBills.add(new InvoiceRaw(invoiceTypeMap.get(values[0]),
							values[1], mpanStrings, values[3],
							new DayStartDate(values[4]), new DayStartDate(
									values[5]).getNext(), new DayFinishDate(
									values[6]), new BigDecimal(values[7]),
							new BigDecimal(values[8]), reads));
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
