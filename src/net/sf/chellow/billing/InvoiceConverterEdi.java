/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.data08.MpanCoreRaw;
import net.sf.chellow.data08.MpanRaw;
import net.sf.chellow.monad.Debug;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.ProgrammerException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.MeterTimeswitchCode;
import net.sf.chellow.physical.ProfileClassCode;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.RegisterReadRaw;
import net.sf.chellow.physical.Units;

public class InvoiceConverterEdi implements InvoiceConverter {
	private static final Map<Integer, ReadType> readTypeMap = Collections
			.synchronizedMap(new HashMap<Integer, ReadType>());

	private static final Map<String, InvoiceType> invoiceTypeMap = Collections
			.synchronizedMap(new HashMap<String, InvoiceType>());

	static {
		readTypeMap.put(0, ReadType.NORMAL);
		readTypeMap.put(1, ReadType.MANUAL_ESTIMATE);
		readTypeMap.put(2, ReadType.COMPUTER_ESTIMATE);
		readTypeMap.put(3, ReadType.REMOVED);
		readTypeMap.put(4, ReadType.CUSTOMER);
		readTypeMap.put(5, ReadType.COMPUTER);
		readTypeMap.put(6, ReadType.EXCHANGE);

		invoiceTypeMap.put("A", InvoiceType.AMENDED);
		invoiceTypeMap.put("F", InvoiceType.FINAL);
		invoiceTypeMap.put("N", InvoiceType.NORMAL);
		invoiceTypeMap.put("I", InvoiceType.INTEREST);
		invoiceTypeMap.put("R", InvoiceType.RECONCILIATION);
		invoiceTypeMap.put("P", InvoiceType.PREPAID);
		invoiceTypeMap.put("O", InvoiceType.INFORMATION);
		invoiceTypeMap.put("W", InvoiceType.WITHDRAWAL);
	}

	private LineNumberReader lreader;

	private List<InvoiceRaw> rawInvoices = new ArrayList<InvoiceRaw>();

	public InvoiceConverterEdi(Reader reader) throws UserException,
			ProgrammerException {
		lreader = new LineNumberReader(reader);
	}

	public List<InvoiceRaw> getRawInvoices() throws UserException,
			ProgrammerException {
		Hiber.flush();
		String line;
		try {
			line = lreader.readLine();
			MpanRaw mpanRaw = null;
			DayStartDate issueDate = null;
			DayStartDate startDate = null;
			DayFinishDate finishDate = null;
			String accountReference = null;
			String invoiceNumber = null;
			Float net = null;
			Float vat = null;
			String messageType = null;
			Set<LocalRegisterReadRaw> reads = null;
			String invoiceTypeCode = null;

			while (line != null) {
				Segment segment = null;
				if (line.endsWith("'")) {
					segment = new Segment(line.substring(0, line.length() - 1));
				} else {
					throw UserException
							.newInvalidParameter("This parser expects one segment per line.");
				}
				String code = segment.getCode();
				if (code.equals("CLO")) {
					Element cloc = segment.getElements().get(0);
					accountReference = cloc.getComponents().get(1);
				}
				if (code.equals("BCD")) {
					Element ivdt = segment.getElements().get(0);
					Element invn = segment.getElements().get(2);
					Element btcd = segment.getElements().get(5);

					invoiceNumber = invn.getComponents().get(0);
					invoiceTypeCode = btcd.toString();
					issueDate = new DayStartDate(ivdt.getDate(0).getNext()
							.getDate());
				}
				if (code.equals("MHD")) {
					Element type = segment.getElements().get(1);
					messageType = type.getComponents().get(0);
					// Debug.print("message type" + messageType);
					if (messageType.equals("UTLBIL")) {
						mpanRaw = null;
						issueDate = null;
						startDate = null;
						finishDate = null;
						accountReference = null;
						invoiceNumber = null;
						net = 0f;
						vat = 0f;
						reads = new HashSet<LocalRegisterReadRaw>();
						invoiceTypeCode = null;
					}
				}
				if (code.equals("CCD")) {
					Element ccde = segment.getElements().get(1);
					String consumptionChargeIndicator = ccde.getString(0);
					String chargeType = ccde.getString(2);
					if (!consumptionChargeIndicator.equals("5")
							&& (chargeType.equals("7")
									|| chargeType.equals("8") || chargeType
									.equals("9"))) {
						HhEndDate previousHhReadDate = segment.getElements()
								.get(7).getDate(0);
						DayStartDate registerStartDate = new DayStartDate(
								previousHhReadDate.getNext().getDate())
								.getNext();
						DayFinishDate previousReadDate = new DayFinishDate(
								previousHhReadDate).getNext();
						if (startDate == null
								|| startDate.getDate().after(
										registerStartDate.getDate())) {
							startDate = registerStartDate;
						}
						DayFinishDate registerFinishDate = new DayFinishDate(
								segment.getElements().get(6).getDate(0))
								.getNext();
						if (finishDate == null
								|| finishDate.getDate().before(
										registerFinishDate.getDate())) {
							finishDate = registerFinishDate;
						}
						if (chargeType.equals("7")) {
							Element tmod = segment.getElements().get(3);
							Element mtnr = segment.getElements().get(4);
							Element prrd = segment.getElements().get(9);
							Element adjf = segment.getElements().get(12);
							ReadType presentReadType = prrd.getReadType(1);
							ReadType previousReadType = prrd.getReadType(3);
							float coefficient = adjf.getInt(1) / 100000;
							float presentReadingValue = prrd.getInt(0) / 1000;
							float previousReadingValue = prrd.getInt(2) / 1000;
							String meterSerialNumber = mtnr.getString(0);
							int tpr = tmod.getInt(0);
							reads.add(new LocalRegisterReadRaw(coefficient,
									meterSerialNumber, Units.KWH, tpr, true,
									previousReadDate, previousReadingValue,
									previousReadType, registerFinishDate,
									presentReadingValue, presentReadType));
						}
					}
				}
				if (code.equals("MTR")) {
					if (messageType.equals("UTLBIL")) {
						Set<RegisterReadRaw> registerReads = new HashSet<RegisterReadRaw>();
						for (LocalRegisterReadRaw read : reads) {
							registerReads.add(new RegisterReadRaw(mpanRaw, read
									.getCoefficient(), read
									.getMeterSerialNumber(), read.getUnits(),
									read.getTpr(), read.getIsImport(), read
											.getPreviousDate(), read
											.getPreviousValue(), read
											.getPreviousType(), read
											.getCurrentDate(), read
											.getCurrentValue(), read
											.getCurrentType()));
						}
						InvoiceType invoiceType = invoiceTypeMap
								.get(invoiceTypeCode);
						InvoiceRaw invoiceRaw = new InvoiceRaw(invoiceType,
								accountReference, mpanRaw.toString(),
								invoiceNumber, issueDate, startDate,
								finishDate, net, vat, registerReads);
						rawInvoices.add(invoiceRaw);
						Debug.print("at mtr: " + invoiceNumber + " "
								+ startDate + " " + finishDate);
					}
				}
				if (code.equals("MAN")) {
					Element madn = segment.getElements().get(2);
					ProfileClassCode profileClassCode = new ProfileClassCode(
							madn.getInt(3));
					MeterTimeswitchCode meterTimeswitchCode = new MeterTimeswitchCode(
							madn.getComponents().get(4));
					int lineLossFactorCode = madn.getInt(5);
					MpanCoreRaw mpanCoreRaw = new MpanCoreRaw(madn
							.getComponents().get(0)
							+ madn.getComponents().get(1)
							+ madn.getComponents().get(2));
					mpanRaw = new MpanRaw(profileClassCode,
							meterTimeswitchCode, lineLossFactorCode,
							mpanCoreRaw);
				}
				if (code.equals("VAT")) {
					Debug.print("started vat");
					Element uvla = segment.getElements().get(5);
					net = uvla.getFloat();
					Element uvtt = segment.getElements().get(6);
					vat = uvtt.getFloat();
				}
				/*
				 * recordType = getRecordType(line); if
				 * (!recordType.equals("0000") && !recordType.equals("0050") &&
				 * !recordType.equals("0051")) { accountReference =
				 * getAccountReference(line); invoiceNumber =
				 * getInvoiceNumber(line); } if (recordType.equals("1460")) {
				 * net += Double.parseDouble(line.substring(67, 79)) / 100; vat +=
				 * Double.parseDouble(line.substring(85, 97)) / 100; } if
				 * (recordType.equals("0461")) { String mpanStr; mpanStr = new
				 * MpanRaw(line.substring(148, 156) + line.substring(135,
				 * 148)).toString(); if (mpanText == null) { mpanText = mpanStr; }
				 * else if (mpanText.indexOf(mpanStr) == -1) { mpanText =
				 * mpanText + ", " + mpanStr; } } if (recordType.equals("0101")) {
				 * try { startDate = new HhEndDate(dateFormat.parse(line
				 * .substring(66, 74))).getNext(); } catch (ParseException e) {
				 * throw UserException .newInvalidParameter("Can't parse the
				 * start date: '" + e.getMessage() + "'."); } try { finishDate =
				 * new HhEndDate(dateFormat.parse(line .substring(74, 82))); }
				 * catch (ParseException e) { throw UserException
				 * .newInvalidParameter("Can't parse the finish date: '" +
				 * e.getMessage() + "'."); } }
				 */
				line = lreader.readLine();
				/*
				 * if (!recordType.equals("0000") && !recordType.equals("0050") &&
				 * !recordType.equals("0051")) { String accountReferenceNext =
				 * line == null ? null : getAccountReference(line); String
				 * invoiceNumberNext = line == null ? null :
				 * getInvoiceNumber(line); if
				 * (!accountReference.equals(accountReferenceNext) ||
				 * !invoiceNumber.equals(invoiceNumberNext)) { List<Object>
				 * fields = new ArrayList<Object>();
				 * fields.add(accountReference); fields.add(mpanText);
				 * fields.add(invoiceNumber); fields.add(startDate);
				 * fields.add(finishDate); fields.add(net); fields.add(vat);
				 * billFields.add(fields); if (mpanLookup.get(accountReference) ==
				 * null) { mpanLookup.put(accountReference, mpanText); }
				 * accountReference = null; mpanText = null; invoiceNumber =
				 * null; startDate = null; finishDate = null; recordType = null;
				 * net = 0; vat = 0; } }
				 */
			}
			lreader.close();
			Hiber.flush();
		} catch (IOException e) {
			throw UserException.newOk("Can't read EDF Energy mm file.");
		} catch (UserException e) {
			throw UserException.newInvalidParameter("Problem at line "
					+ lreader.getLineNumber() + " of the EDI file. "
					+ e.getMessage());
		}
		/*
		 * for (List<Object> fields : billFields) { try {
		 * 
		 * rawBills.add(new InvoiceRaw((String) fields.get(0), fields .get(1) ==
		 * null ? mpanLookup .get((String) fields.get(0)) : (String)
		 * fields.get(1), (String) fields.get(2), (HhEndDate) fields.get(3),
		 * false, (HhEndDate) fields.get(4), false, (Double) fields.get(5),
		 * (Double) fields.get(6))); } catch (UserException e) { throw
		 * UserException .newInvalidParameter("I'm having trouble parsing the
		 * file. The problem seems to be with the bill with account number '" +
		 * (String) fields.get(0) + "' and invoice number '" + (String)
		 * fields.get(2) + "'. " + e.getMessage()); } }
		 */
		return rawInvoices;
	}

	/*
	 * private String getRecordType(String line) { return line.substring(62,
	 * 66); }
	 * 
	 * private String getAccountReference(String line) { return
	 * line.substring(33, 41); }
	 * 
	 * private String getInvoiceNumber(String line) { return line.substring(41,
	 * 46); }
	 */
	public String getProgress() {
		return "Reached line " + lreader.getLineNumber() + " of first passs.";
	}

	private class Segment {
		private List<Element> elements = new ArrayList<Element>();

		private String code;

		public Segment(String segment) {
			code = segment.substring(0, 3);
			for (String element : segment.substring(4).split("\\+")) {
				elements.add(new Element(segment, elements.size(), element));
			}
		}

		public List<Element> getElements() {
			return elements;
		}

		public String getCode() {
			return code;
		}
	}

	private class Element {
		private List<String> components = new ArrayList<String>();

		private String segment;

		private int index;

		public Element(String segment, int index, String element) {
			this.segment = segment;
			this.index = index;
			for (String component : element.split(":")) {
				components.add(component);
			}
		}

		public List<String> getComponents() {
			return components;
		}

		public HhEndDate getDate(int index) throws ProgrammerException,
				UserException {
			DateFormat dateFormat = new SimpleDateFormat("yyMMdd", Locale.UK);
			dateFormat.setCalendar(MonadDate.getCalendar());
			try {
				return new HhEndDate(dateFormat.parse(components.get(index)));
			} catch (ParseException e) {
				throw UserException.newInvalidParameter("Expected component "
						+ index + " of element " + this.index + " of segment '"
						+ segment + "' to be a date. " + e.getMessage());
			}
		}

		public Float getFloat() {
			Float result = new Float(components.get(0));
			if (components.size() > 1
					&& components.get(components.size() - 1).equals("R")) {
				result = result * -1;
			}
			return result;
		}

		public ReadType getReadType(int index) throws UserException,
				ProgrammerException {
			return readTypeMap.get(getInt(index));
		}

		public int getInt(int index) throws UserException, ProgrammerException {
			try {
				return Integer.parseInt(components.get(index));
			} catch (NumberFormatException e) {
				throw UserException.newInvalidParameter("Expected component "
						+ index + " of element " + this.index + " of segment '"
						+ segment + "' to be an integer. " + e.getMessage());
			}
		}

		public String getString(int index) {
			return components.get(index);
		}
	}

	private class LocalRegisterReadRaw {
		private float coefficient;

		private String meterSerialNumber;

		private Units units;

		private int tpr;

		private boolean isImport;

		private DayFinishDate previousDate;

		private float previousValue;

		private ReadType previousType;

		private DayFinishDate currentDate;

		private float currentValue;

		private ReadType currentType;

		public LocalRegisterReadRaw(float coefficient,
				String meterSerialNumber, Units units, int tpr,
				boolean isImport, DayFinishDate previousDate,
				float previousValue, ReadType previousType,
				DayFinishDate currentDate, float currentValue,
				ReadType currentType) throws ProgrammerException {
			this.coefficient = coefficient;
			this.meterSerialNumber = meterSerialNumber;
			this.units = units;
			this.tpr = tpr;
			this.isImport = isImport;
			this.previousDate = previousDate;
			this.previousValue = previousValue;
			this.previousType = previousType;
			this.currentDate = currentDate;
			this.currentValue = currentValue;
			this.currentType = currentType;
		}

		public float getCoefficient() {
			return coefficient;
		}

		public String getMeterSerialNumber() {
			return meterSerialNumber;
		}

		public Units getUnits() {
			return units;
		}

		public int getTpr() {
			return tpr;
		}

		public boolean getIsImport() {
			return isImport;
		}

		public DayFinishDate getPreviousDate() {
			return previousDate;
		}

		public float getPreviousValue() {
			return previousValue;
		}

		public ReadType getPreviousType() {
			return previousType;
		}

		public DayFinishDate getCurrentDate() {
			return currentDate;
		}

		public float getCurrentValue() {
			return currentValue;
		}

		public ReadType getCurrentType() {
			return currentType;
		}

	}
}