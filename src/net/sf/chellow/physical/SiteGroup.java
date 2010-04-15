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
package net.sf.chellow.physical;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;

import org.hibernate.Query;
import org.hibernate.ScrollableResults;

public class SiteGroup {
	public static final String EXPORT_NET_GT_IMPORT_GEN = "Export to net > import from generators.";

	public static final String EXPORT_GEN_GT_IMPORT = "Export to generators > import.";

	private HhStartDate from;

	private HhStartDate to;

	private List<Site> sites;

	private List<Supply> supplies;

	public SiteGroup(HhStartDate from, HhStartDate to, List<Site> sites,
			List<Supply> supplies) {
		this.from = from;
		this.to = to;
		this.sites = sites;
		this.supplies = supplies;
	}

	public HhStartDate getFrom() {
		return from;
	}

	public HhStartDate getTo() {
		return to;
	}

	public List<Site> getSites() {
		return sites;
	}

	public List<Supply> getSupplies() {
		return supplies;
	}

	public Map<String, List<Double>> hhData() throws HttpException {
		Map<String, List<Double>> map = new HashMap<String, List<Double>>();
		List<Double> importNet = new ArrayList<Double>();
		map.put("import-net", importNet);
		List<Double> exportNet = new ArrayList<Double>();
		map.put("export-net", exportNet);
		List<Double> importGen = new ArrayList<Double>();
		map.put("import-gen", importGen);
		List<Double> exportGen = new ArrayList<Double>();
		map.put("export-gen", exportGen);
		List<Double> import3rdParty = new ArrayList<Double>();
		map.put("import-3rd-party", import3rdParty);
		List<Double> export3rdParty = new ArrayList<Double>();
		map.put("export-3rd-party", export3rdParty);

		Calendar cal = HhStartDate.getCalendar();
		for (long end = getFrom().getDate().getTime(); end <= getTo().getDate()
				.getTime(); end = HhStartDate.getNext(cal, end)) {
			importNet.add(0d);
			exportNet.add(0d);
			importGen.add(0d);
			exportGen.add(0d);
			import3rdParty.add(0d);
			export3rdParty.add(0d);
		}
		Query query = Hiber
				.session()
				.createQuery(
						"select datum.startDate.date , datum.value from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = true and datum.startDate.date >= :from and datum.startDate.date <= :to order by datum.startDate.date")
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate());
		List<List<Double>> hhStreams = new ArrayList<List<Double>>();
		for (Supply supply : getSupplies()) {
			query.setEntity("supply", supply);
			String sourceCode = supply.getSource().getCode();
			for (boolean isImport : new boolean[] { true, false }) {
				hhStreams.clear();
				if (sourceCode.equals(Source.NETWORK_CODE)
						|| sourceCode.equals(Source.GENERATOR_NETWORK_CODE)) {
					if (isImport) {
						hhStreams.add(importNet);
					} else {
						hhStreams.add(exportNet);
					}
				} else if (sourceCode.equals(Source.GENERATOR_CODE)) {
					if (isImport) {
						hhStreams.add(importGen);
					} else {
						hhStreams.add(exportGen);
					}
				} else if (sourceCode.equals(Source.THIRD_PARTY_CODE)) {
					if (isImport) {
						hhStreams.add(import3rdParty);
					} else {
						hhStreams.add(export3rdParty);
					}
				} else if (sourceCode.equals(Source.THIRD_PARTY_REVERSE_CODE)) {
					if (isImport) {
						hhStreams.add(export3rdParty);
					} else {
						hhStreams.add(import3rdParty);
					}
				}
				if (sourceCode.equals(Source.GENERATOR_NETWORK_CODE)) {
					if (isImport) {
						hhStreams.add(exportGen);
					} else {
						hhStreams.add(importGen);
					}
				}
				query.setBoolean("isImport", isImport);
				ScrollableResults hhData = query.scroll();
				try {
					if (!hhData.next()) {
						continue;
					}
					int i = 0;
					long datumStartDate = hhData.getDate(0).getTime();
					double datumValue = hhData.getBigDecimal(1).doubleValue();
					for (long end = getFrom().getDate().getTime(); end <= getTo()
							.getDate().getTime(); end = HhStartDate.getNext(cal,
							end)) {
						if (datumStartDate == end) {
							for (List<Double> hhStream : hhStreams) {
								hhStream.set(i, hhStream.get(i) + datumValue);
							}
							if (hhData.next()) {
								datumStartDate = hhData.getDate(0).getTime();
								datumValue = hhData.getBigDecimal(1)
										.doubleValue();
							}
						}
						i++;
					}
				} finally {
					hhData.close();
				}
			}
		}
		return map;
	}

	public void addSiteSnag(String description, HhStartDate startDate,
			HhStartDate finishDate) throws HttpException {
		SnagDateBounded.addSiteSnag(sites.get(0), description, startDate,
				finishDate);
	}

	public void deleteHhdcSnag(String description, HhStartDate startDate,
			HhStartDate finishDate) throws HttpException {
		SnagDateBounded.deleteSiteSnag(sites.get(0), description, startDate,
				finishDate);
	}
}
