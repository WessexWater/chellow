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
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.physical.HhEndDate;
import net.sf.chellow.physical.Meter;
import net.sf.chellow.physical.MpanCore;
import net.sf.chellow.physical.ReadType;
import net.sf.chellow.physical.RegisterReadRaw;
import net.sf.chellow.physical.Units;

public class BillConverterBgbEdi implements BillConverter {
	private static final Map<Integer, Character> readTypeMap = Collections
			.synchronizedMap(new HashMap<Integer, Character>());

	private static final Map<String, String> billTypeMap = Collections
			.synchronizedMap(new HashMap<String, String>());

	static {
		readTypeMap.put(0, ReadType.TYPE_ROUTINE);
		readTypeMap.put(1, ReadType.TYPE_ESTIMATE);
		readTypeMap.put(2, ReadType.TYPE_ESTIMATE);
		readTypeMap.put(3, ReadType.TYPE_ROUTINE);
		readTypeMap.put(4, ReadType.TYPE_CUSTOMER);
		readTypeMap.put(5, ReadType.TYPE_ROUTINE);
		readTypeMap.put(6, ReadType.TYPE_ROUTINE);
		readTypeMap.put(7, ReadType.TYPE_INITIAL);

		billTypeMap.put("A", "AMENDED");
		billTypeMap.put("F", "FINAL");
		billTypeMap.put("N", "NORMAL");
		billTypeMap.put("I", "INTEREST");
		billTypeMap.put("R", "RECONCILIATION");
		billTypeMap.put("P", "PREPAID");
		billTypeMap.put("O", "INFORMATION");
		billTypeMap.put("W", "WITHDRAWAL");
	}

	private LineNumberReader lreader;

	private List<RawBill> rawBills = new ArrayList<RawBill>();

	public BillConverterBgbEdi(Reader reader) throws HttpException,
			InternalException {
		lreader = new LineNumberReader(reader);
	}

	public List<RawBill> getRawBills() throws HttpException,
			InternalException {
		Hiber.flush();
		String line;
		try {
			line = lreader.readLine();
			Set<String> mpanStrings = null;
			DayStartDate issueDate = null;
			DayStartDate startDate = null;
			DayFinishDate finishDate = null;
			String accountReference = null;
			String invoiceNumber = null;
			BigDecimal net = null;
			BigDecimal vat = null;
			String messageType = null;
			Set<LocalRegisterReadRaw> reads = null;
			String billTypeCode = null;

			while (line != null) {
				EdiSegment segment = null;
				if (line.endsWith("'")) {
					segment = new EdiSegment(line.substring(0,
							line.length() - 1), readTypeMap);
				} else {
					throw new UserException(
							"This parser expects one segment per line.");
				}
				String code = segment.getCode();
				if (code.equals("CLO")) {
					EdiElement cloc = segment.getElements().get(0);
					accountReference = cloc.getComponents().get(1);
				}
				if (code.equals("BCD")) {
					EdiElement ivdt = segment.getElements().get(0);
					EdiElement invn = segment.getElements().get(2);
					EdiElement btcd = segment.getElements().get(5);

					invoiceNumber = invn.getComponents().get(0);
					billTypeCode = btcd.getComponents().get(0);
					issueDate = new DayStartDate(ivdt.getDate(0).getNext()
							.getDate());
				}
				if (code.equals("MHD")) {
					EdiElement type = segment.getElements().get(1);
					messageType = type.getComponents().get(0);
					// Debug.print("message type" + messageType);
					if (messageType.equals("UTLBIL")) {
						issueDate = null;
						startDate = null;
						finishDate = null;
						accountReference = null;
						invoiceNumber = null;
						net = new BigDecimal(0);
						vat = new BigDecimal(0);
						reads = new HashSet<LocalRegisterReadRaw>();
						billTypeCode = null;
						mpanStrings = new HashSet<String>();
					}
				}
				if (code.equals("CCD")) {
					EdiElement ccde = segment.getElements().get(1);
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
							EdiElement tmod = segment.getElements().get(3);
							EdiElement mtnr = segment.getElements().get(4);
							EdiElement mloc = segment.getElements().get(5);
							EdiElement prrd = segment.getElements().get(9);
							EdiElement adjf = segment.getElements().get(12);
							ReadType presentReadType = prrd.getReadType(1);
							ReadType previousReadType = prrd.getReadType(3);
							BigDecimal coefficient = new BigDecimal(adjf
									.getInt(1)).divide(new BigDecimal(100000));
							BigDecimal presentReadingValue = new BigDecimal(
									prrd.getInt(0))
									.divide(new BigDecimal(1000));
							BigDecimal previousReadingValue = new BigDecimal(
									prrd.getInt(2))
									.divide(new BigDecimal(1000));
							String meterSerialNumber = mtnr.getString(0);
							Meter meter = MpanCore.getMpanCore(
									mloc.getString(0)).getSupply().findMeter(
									meterSerialNumber);
							int tpr = tmod.getInt(0);
							reads.add(new LocalRegisterReadRaw(meter,
									coefficient, Units.KWH, tpr,
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
							registerReads.add(new RegisterReadRaw(read
									.getMeter(), read.getCoefficient(), read
									.getUnits(), read.getTpr(), read
									.getPreviousDate(),
									read.getPreviousValue(), read
											.getPreviousType(), read
											.getCurrentDate(), read
											.getCurrentValue(), read
											.getCurrentType()));
						}
						String billType = billTypeMap
								.get(billTypeCode);
						RawBill billRaw = new RawBill(billType,
								accountReference, mpanStrings, invoiceNumber,
								issueDate, startDate, finishDate, net, vat,
								registerReads);
						rawBills.add(billRaw);
					}
				}
				if (code.equals("MAN")) {
					EdiElement madn = segment.getElements().get(2);
					String pcCode = "0" + madn.getString(3);
					String mtcCode = madn.getComponents().get(4);
					String llfcCode = madn.getString(5);

					mpanStrings.add(pcCode + " " + mtcCode + " " + llfcCode
							+ " " + madn.getComponents().get(0) + " "
							+ madn.getComponents().get(1)
							+ madn.getComponents().get(2));
				}
				if (code.equals("VAT")) {
					EdiElement uvla = segment.getElements().get(5);
					net = uvla.getBigDecimal();
					EdiElement uvtt = segment.getElements().get(6);
					vat = uvtt.getBigDecimal();
				}
				line = lreader.readLine();
			}
			lreader.close();
			Hiber.flush();
		} catch (IOException e) {
			throw new UserException("Can't read EDF Energy mm file.");
		} catch (HttpException e) {
			throw new UserException("Problem at line "
					+ lreader.getLineNumber() + " of the EDI file. "
					+ e.getMessage());
		}
		return rawBills;
	}

	public String getProgress() {
		return "Reached line " + lreader.getLineNumber() + " of first passs.";
	}

	private class LocalRegisterReadRaw {
		private BigDecimal coefficient;

		private Meter meter;

		private Units units;

		private int tpr;

		private DayFinishDate previousDate;

		private BigDecimal previousValue;

		private ReadType previousType;

		private DayFinishDate currentDate;

		private BigDecimal currentValue;

		private ReadType currentType;

		public LocalRegisterReadRaw(Meter meter, BigDecimal coefficient,
				Units units, int tpr, DayFinishDate previousDate,
				BigDecimal previousValue, ReadType previousType,
				DayFinishDate currentDate, BigDecimal currentValue,
				ReadType currentType) throws InternalException {
			this.meter = meter;
			this.coefficient = coefficient;
			this.units = units;
			this.tpr = tpr;
			this.previousDate = previousDate;
			this.previousValue = previousValue;
			this.previousType = previousType;
			this.currentDate = currentDate;
			this.currentValue = currentValue;
			this.currentType = currentType;
		}

		public Meter getMeter() {
			return meter;
		}

		public BigDecimal getCoefficient() {
			return coefficient;
		}

		public Units getUnits() {
			return units;
		}

		public int getTpr() {
			return tpr;
		}

		public DayFinishDate getPreviousDate() {
			return previousDate;
		}

		public BigDecimal getPreviousValue() {
			return previousValue;
		}

		public ReadType getPreviousType() {
			return previousType;
		}

		public DayFinishDate getCurrentDate() {
			return currentDate;
		}

		public BigDecimal getCurrentValue() {
			return currentValue;
		}

		public ReadType getCurrentType() {
			return currentType;
		}

	}
}
