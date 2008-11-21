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

package net.sf.chellow.physical;

import java.util.ArrayList;
import java.util.List;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.hhimport.HhDatumRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhDatum extends PersistentEntity {
	public static final Character ACTUAL = 'A';
	public static final Character ESTIMATE = 'E';
	
	static private String getCsvField(String fieldName, String[] values, int index) throws HttpException {
		if (index > values.length - 1) {
			throw new UserException("Another field called " + fieldName
					+ " needs to be added on to " + values);
		}
		return values[index];
	}
	
	static public void generalImportInsert(List<HhDatumRaw> rawData) throws HttpException {
		HhDatumRaw datum = rawData.get(0);
		String mpanCoreStr = datum.getMpanCore();
		MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
		SupplyGeneration generation = mpanCore
				.getSupply().getGeneration(datum.getEndDate());
        HhdcContract contract = generation.getHhdcContract();
		if (generation == null) {
			throw new UserException("HH datum has been ignored: "
					+ datum.toString() + ".");
		}
		Channel channel = generation.getChannel(datum.getIsImport(), datum
				.getIsKwh());
		HhEndDate genFinishDate = generation.getFinishDate();
		List<HhDatumRaw> data = new ArrayList<HhDatumRaw>();
		data.add(datum);
		HhDatumRaw firstDatum = datum;
		if (rawData.size() == 1) {
			//batchSize = data.size();
			//try {
				channel.addHhData(contract, data);
			//} catch (UserException e) {
			//	messages.add(e.getMessage());
			//}
		}
		for (int i = 1; i < rawData.size(); i++) {
				datum = rawData.get(i);
			if (data.size() > 1000
					|| !(mpanCoreStr.equals(datum.getMpanCore())
							&& datum.getIsImport() == firstDatum
									.getIsImport()
							&& datum.getIsKwh() == firstDatum.getIsKwh() && datum
							.getEndDate().getDate().equals(
									data.get(data.size() - 1).getEndDate()
											.getNext().getDate()))
					|| (genFinishDate != null && genFinishDate.getDate()
							.before(datum.getEndDate().getDate()))) {
				//batchSize = data.size();
		//		try {
					channel.addHhData(contract, data);
			//	} catch (UserException e) {
				//	messages.add(e.getMessage());
			//	}
				Hiber.close();
				data.clear();
				mpanCoreStr = datum.getMpanCore();
				mpanCore = MpanCore.getMpanCore(mpanCoreStr);
				generation = mpanCore.getSupply()
						.getGeneration(datum.getEndDate());
				if (generation == null) {
					throw new UserException("HH datum has been ignored: "
							+ datum.toString() + ".");
				}
				contract = generation.getHhdcContract();
				channel = generation.getChannel(datum.getIsImport(), datum
						.getIsKwh());
				genFinishDate = generation.getFinishDate();
			}
			data.add(datum);
		}
		if (!data.isEmpty()) {
			channel.addHhData(contract, data);
		}
		//Hiber.close();
}
	static public HhDatumRaw generalImportRaw(String[] values) throws HttpException {
		String mpanCoreStr = getCsvField("MPAN Core", values, 2);
		//MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
		String dateStr = getCsvField("Date", values, 3);
        HhEndDate date = new HhEndDate(dateStr);
        String isImportStr = getCsvField("Is Import?", values, 4);
        boolean isImport = Boolean.parseBoolean(isImportStr);
        String isKwhStr = getCsvField("Is Kwh?", values, 5);
        boolean isKwh = Boolean.parseBoolean(isKwhStr);
			String valueStr = getCsvField("Value", values, 6);
			float value = Float.parseFloat(valueStr);
			String status = getCsvField("Status", values, 7);
			return new HhDatumRaw(mpanCoreStr, isImport, isKwh,
					date, value, status);
	}
	
	static public void generalImport(String action, String[] values) throws HttpException {
		String mpanCoreStr = getCsvField("MPAN Core", values, 2);
		MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
		String dateStr = getCsvField("Date", values, 3);
        HhEndDate date = new HhEndDate(dateStr);
        Supply supply = mpanCore.getSupply();
        SupplyGeneration supplyGeneration = supply.getGeneration(date);
        String isImportStr = getCsvField("Is Import?", values, 4);
        boolean isImport = Boolean.parseBoolean(isImportStr);
        String isKwhStr = getCsvField("Is Kwh?", values, 5);
        boolean isKwh = Boolean.parseBoolean(isKwhStr);
        Channel channel = supplyGeneration.getChannel(isImport, isKwh);
		if (action.equals("insert")) {
			String valueStr = getCsvField("Value", values, 6);
			float value = Float.parseFloat(valueStr);
			String status = getCsvField("Status", values, 7);
			HhDatumRaw datumRaw = new HhDatumRaw(mpanCoreStr, isImport, isKwh,
					date, value, status);
			List<HhDatumRaw> dataRaw = new ArrayList<HhDatumRaw>();
			dataRaw.add(datumRaw);
			channel.addHhData(supplyGeneration.getHhdcContract(), dataRaw);
		}
	}

	private Channel channel;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatum() {
	}

	public HhDatum(Channel channel, HhDatumRaw datumRaw) throws HttpException {
		setChannel(channel);
		setEndDate(datumRaw.getEndDate());
		update(datumRaw.getValue(), datumRaw.getStatus());
	}

	/*
	 * public HhDatum(Channel channel, HhEndDate endDate, float value, Character
	 * status) throws UserException, ProgrammerException { this.channel =
	 * channel; this.endDate = endDate; update(value, status); }
	 */
	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}

	public HhEndDate getEndDate() {
		return endDate;
	}

	void setEndDate(HhEndDate endDate) {
		this.endDate = endDate;
	}

	public float getValue() {
		return value;
	}

	void setValue(float value) {
		this.value = value;
	}

	public Character getStatus() {
		return status;
	}

	void setStatus(Character status) {
		this.status = status;
	}

	public void update(float value, Character status) throws HttpException {
		this.value = value;
		this.status = HhDatumRaw.checkStatus(status);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "hh-datum");

		element.appendChild(endDate.toXml(doc));
		element.setAttribute("value", Float.toString(value));
		if (status != null) {
			element.setAttribute("status", Character.toString(status));
		}
		return element;
	}

	public String toString() {
		return "End date " + endDate + ", Value " + value + ", Status "
				+ status;
	}

	public MonadUri getUri() throws HttpException {
		return channel.getHhDataInstance().getUri().resolve(getUriId());
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		throw new NotFoundException();
	}
}
