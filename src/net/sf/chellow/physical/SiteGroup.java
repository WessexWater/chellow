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

	private HhEndDate from;

	private HhEndDate to;

	private List<Site> sites;

	private List<Supply> supplies;

	public SiteGroup(HhEndDate from, HhEndDate to, List<Site> sites,
			List<Supply> supplies) {
		this.from = from;
		this.to = to;
		this.sites = sites;
		this.supplies = supplies;
	}

	public HhEndDate getFrom() {
		return from;
	}

	public HhEndDate getTo() {
		return to;
	}

	public List<Site> getSites() {
		return sites;
	}

	public List<Supply> getSupplies() {
		return supplies;
	}

	@SuppressWarnings("unchecked")
	public Map<String, List<Double>> hhData() throws HttpException {
		Map<String, List<Double>> map = new HashMap<String, List<Double>>();
		List<Double> importFromNet = new ArrayList<Double>();
		map.put("import-from-net", importFromNet);
		List<Double> exportToNet = new ArrayList<Double>();
		map.put("export-to-net", exportToNet);
		List<Double> importFromGen = new ArrayList<Double>();
		map.put("import-from-gen", importFromGen);
		List<Double> exportToGen = new ArrayList<Double>();
		map.put("export-to-gen", exportToGen);
		List<Double> importFrom3rdParty = new ArrayList<Double>();
		map.put("import-from-3rd-party", importFrom3rdParty);
		List<Double> exportTo3rdParty = new ArrayList<Double>();
		map.put("export-to-3rd-party", exportTo3rdParty);
		
		Calendar cal = HhEndDate.getCalendar();
		for (long end = getFrom().getDate().getTime(); end <= getTo().getDate()
				.getTime(); end = HhEndDate.getNext(cal, end)) {
			importFromNet.add(0d);
			exportToNet.add(0d);
			importFromGen.add(0d);
			exportToGen.add(0d);
			importFrom3rdParty.add(0d);
			exportTo3rdParty.add(0d);
		}
		Query query = Hiber
				.session()
				.createQuery(
						"select datum.endDate.date , datum.value from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = true and datum.endDate.date >= :from and datum.endDate.date <= :to order by datum.endDate.date")
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
						hhStreams.add(importFromNet);
					} else {
						hhStreams.add(exportToNet);
					}
				} else if (sourceCode.equals(Source.GENERATOR_CODE)) {
					if (isImport) {
						hhStreams.add(importFromGen);
					} else {
						hhStreams.add(exportToGen);
					}
				} else if (sourceCode.equals(Source.THIRD_PARTY_CODE)) {
					if (isImport) {
						hhStreams.add(importFrom3rdParty);
					} else {
						hhStreams.add(exportTo3rdParty);
					}
				} else if (sourceCode.equals(Source.THIRD_PARTY_REVERSE_CODE)) {
					if (isImport) {
						hhStreams.add(exportTo3rdParty);
					} else {
						hhStreams.add(importFrom3rdParty);
					}
				}
				if (sourceCode.equals(Source.GENERATOR_NETWORK_CODE)) {
					if (isImport) {
						hhStreams.add(exportToGen);
					} else {
						hhStreams.add(importFromGen);
					}
				}
				query.setBoolean("isImport", isImport);
				ScrollableResults hhData = query.scroll();
				if (!hhData.next()) {
					continue;
				}
				int i = 0;
				long datumEndDate = hhData.getDate(0).getTime();
				double datumValue = hhData.getBigDecimal(1).doubleValue();
				for (long end = getFrom().getDate().getTime(); end <= getTo()
						.getDate().getTime(); end = HhEndDate.getNext(cal, end)) {
					if (datumEndDate == end) {
						for (List<Double> hhStream : hhStreams) {
							hhStream.set(i, hhStream.get(i) + datumValue);
						}
						if (hhData.next()) {
							datumEndDate = hhData.getDate(0).getTime();
							datumValue = hhData.getBigDecimal(1).doubleValue();
						}
					}
					i++;
				}
			}
		}
		return map;
	}

	public void addSiteSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		SnagDateBounded.addSiteSnag(sites.get(0), description, startDate,
				finishDate);
	}

	@SuppressWarnings("unchecked")
	public void deleteHhdcSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		SnagDateBounded.deleteSiteSnag(sites.get(0), description, startDate,
				finishDate);
	}
}
