package net.sf.chellow.physical;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.sf.chellow.billing.HhdcContract;
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
	public Map<String, List<Float>> hhData() throws HttpException {
		Map<String, List<Float>> map = new HashMap<String, List<Float>>();
		List<Float> importFromNet = new ArrayList<Float>();
		map.put("import-from-net", importFromNet);
		List<Float> exportToNet = new ArrayList<Float>();
		map.put("export-to-net", exportToNet);
		List<Float> importFromGen = new ArrayList<Float>();
		map.put("import-from-gen", importFromGen);
		List<Float> exportToGen = new ArrayList<Float>();
		map.put("export-to-gen", exportToGen);

		Calendar cal = HhEndDate.getCalendar();
		for (long end = getFrom().getDate().getTime(); end <= getTo().getDate()
				.getTime(); end = HhEndDate.getNext(cal, end)) {
			importFromNet.add(0f);
			exportToNet.add(0f);
			importFromGen.add(0f);
			exportToGen.add(0f);
		}
		Query query = Hiber
				.session()
				.createQuery(
						"select datum.endDate.date , datum.value from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = true and datum.endDate.date >= :from and datum.endDate.date <= :to order by datum.endDate.date")
				.setTimestamp("from", from.getDate()).setTimestamp("to",
						to.getDate());
		for (Supply supply : getSupplies()) {
			query.setEntity("supply", supply);
			for (boolean isImport : new boolean[] { true, false }) {
				List<Float> hhStream = null;
				if (supply.getSource().getCode().equals(Source.NETWORK_CODE)) {
					if (isImport) {
						hhStream = importFromNet;
					} else {
						hhStream = exportToNet;
					}
				} else {
					if (isImport) {
						hhStream = importFromGen;
					} else {
						hhStream = exportToGen;
					}
				}
				query.setBoolean("isImport", isImport);
				ScrollableResults hhData = query.scroll();
				if (!hhData.next()) {
					continue;
				}
				int i = 0;
				// int missing = 0;
				long datumEndDate = hhData.getDate(0).getTime();
				float datumValue = hhData.getFloat(1);
				for (long end = getFrom().getDate().getTime(); end <= getTo()
						.getDate().getTime(); end = HhEndDate.getNext(cal, end)) {
					if (datumEndDate == end) {
						hhStream.set(i, hhStream.get(i) + datumValue);
						if (hhData.next()) {
							datumEndDate = hhData.getDate(0).getTime();
							datumValue = hhData.getFloat(1);
						}
					}
					/*
					 * HhDatum datum = null; if (i - missing < hhData.size()) {
					 * datum = hhData.get(i - missing); if (end !=
					 * datum.getEndDate().getDate().getTime()) { missing++; }
					 * else { hhStream.set(i, hhStream.get(i) +
					 * datum.getValue()); } }
					 */
					i++;
				}
			}
		}
		return map;
	}

	public void addHhdcSnag(String description, HhEndDate startDate,
			HhEndDate finishDate, boolean isResolved) throws HttpException {
		// which sevice?
		Site site = sites.get(0);
		HhdcContract contract = getHhdcContract(startDate);
		HhEndDate contractEndDate = contract.getFinishRateScript()
				.getFinishDate();
		SnagDateBounded.addSiteSnag(contract, site, description, startDate,
				contractEndDate == null
						|| contractEndDate.getDate()
								.after(finishDate.getDate()) ? finishDate
						: contractEndDate, isResolved);
		while (!(contractEndDate == null || !contractEndDate.getDate().before(
				finishDate.getDate()))) {
			contract = getHhdcContract(contractEndDate.getNext());
			contractEndDate = contract.getFinishRateScript().getFinishDate();
			SnagDateBounded.addSiteSnag(contract, site, description, contract
					.getStartRateScript().getStartDate(),
					contractEndDate == null
							|| contractEndDate.getDate().after(
									finishDate.getDate()) ? finishDate
							: contractEndDate, isResolved);
		}
	}

	@SuppressWarnings("unchecked")
	private HhdcContract getHhdcContract(HhEndDate date) throws HttpException {
		List<Long> contractIds = (List<Long>) Hiber
				.session()
				.createQuery(
						"select distinct mpan.hhdcAccount.contract.id from Mpan mpan where mpan.supplyGeneration.supply in (:supplies) and mpan.supplyGeneration.startDate.date <= :date and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate >= :date) order by mpan.hhdcAccount.contract.id")
				.setParameterList("supplies", supplies).setTimestamp("date",
						date.getDate()).list();
		return contractIds.size() > 0 ? HhdcContract
				.getHhdcContract(contractIds.get(0)) : null;
	}

	@SuppressWarnings("unchecked")
	public void resolveHhdcSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws HttpException {
		if (!startDate.getDate().after(finishDate.getDate())) {
			for (SiteSnag snag : (List<SiteSnag>) Hiber
					.session()
					.createQuery(
							"from SiteSnag snag where snag.site = :site and snag.description = :description and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.dateResolved is null")
					.setEntity("site", sites.get(0)).setString("description",
							description.toString()).setTimestamp("startDate",
							startDate.getDate()).setTimestamp("finishDate",
							finishDate.getDate()).list()) {
				addHhdcSnag(description, snag.getStartDate().getDate().before(
						startDate.getDate()) ? startDate : snag.getStartDate(),
						snag.getFinishDate().getDate().after(
								finishDate.getDate()) ? finishDate : snag
								.getFinishDate(), true);
			}
		}
	}
}
