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
import java.io.LineNumberReader;
import java.io.Reader;
import java.math.BigDecimal;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;

public class InvoiceConverterMm implements InvoiceConverter {
	private LineNumberReader lreader;

	private DateFormat dateFormat = new SimpleDateFormat("yyyyMMdd", Locale.UK);

	private List<InvoiceRaw> rawBills = new ArrayList<InvoiceRaw>();

	public InvoiceConverterMm(Reader reader) throws HttpException,
			InternalException {
		lreader = new LineNumberReader(reader);
	}

	public List<InvoiceRaw> getRawInvoices() throws HttpException,
			InternalException {
		Hiber.flush();
		if (rawBills.isEmpty()) {
			String line;
			dateFormat.setTimeZone(TimeZone.getTimeZone("GMT"));
			try {
				line = lreader.readLine();
				DayStartDate startDate = null;
				DayFinishDate finishDate = null;
				String accountReference = null;
				String invoiceNumber = null;
				BigDecimal net = new BigDecimal(0);
				BigDecimal vat = new BigDecimal(0);
				Set<String> mpanStrings = null;
				while (line != null) {
					String recordType = getRecordType(line);
					if (recordType.equals("0100")) {
						accountReference = getAccountReference(line);
						invoiceNumber = getInvoiceNumber(line);
						startDate = null;
						finishDate = null;
						net = new BigDecimal(0);
						vat = new BigDecimal(0);
						mpanStrings = new HashSet<String>();
					}
					if (recordType.equals("1460")) {
						net = net.add(new BigDecimal(line.substring(67, 79))
								.divide(new BigDecimal(100)));
						vat = vat.add(new BigDecimal(line.substring(85, 97))
								.divide(new BigDecimal(100)));
					}
					if (recordType.equals("0461")) {
						mpanStrings.add(line.substring(148, 156)
								+ line.substring(135, 148));
					}
					if (recordType.equals("0101")) {
						try {
							startDate = new DayStartDate(new HhEndDate(
									dateFormat.parse(line.substring(66, 74)))
									.getNext().getDate()).getNext();
						} catch (ParseException e) {
							throw new UserException(
									"Can't parse the start date: '"
											+ e.getMessage() + "'.");
						}
						try {
							finishDate = new DayFinishDate(dateFormat
									.parse(line.substring(74, 82)));
						} catch (ParseException e) {
							throw new UserException(
									"Can't parse the finish date: '"
											+ e.getMessage() + "'.");
						}
					}
					if (recordType.equals("1500")) {
						rawBills.add(new InvoiceRaw(InvoiceType.NORMAL,
								accountReference, mpanStrings, invoiceNumber,
								startDate, startDate, finishDate, net, vat,
								null));
					}
					line = lreader.readLine();
				}
				lreader.close();
				Hiber.flush();
			} catch (IOException e) {
				throw new UserException("Can't read EDF Energy mm file.");
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
