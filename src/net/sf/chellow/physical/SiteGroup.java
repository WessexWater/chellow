package net.sf.chellow.physical;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import net.sf.chellow.billing.HhdcContract;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.HttpException;

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

	public Map<String, List<Float>> hhData() throws InternalException,
			HttpException {
		Map<String, List<Float>> map = new HashMap<String, List<Float>>();
		List<Float> importFromNet = new ArrayList<Float>();
		map.put("import-from-net", importFromNet);
		List<Float> exportToNet = new ArrayList<Float>();
		map.put("export-to-net", exportToNet);
		List<Float> importFromGen = new ArrayList<Float>();
		map.put("import-from-gen", importFromGen);
		List<Float> exportToGen = new ArrayList<Float>();
		map.put("export-to-gen", exportToGen);

		HhEndDate hhEndDate = getFrom();
		while (!hhEndDate.getDate().after(getTo().getDate())) {
			importFromNet.add(0f);
			exportToNet.add(0f);
			importFromGen.add(0f);
			exportToGen.add(0f);
			hhEndDate = hhEndDate.getNext();
		}
		for (Supply supply : getSupplies()) {
			for (Channel channel : supply.getChannels()) {
				if (!channel.getIsKwh()) {
					continue;
				}
				List<Float> hhStream = null;
				if (supply.getSource().getCode().equals(SourceCode.NETWORK)) {
					if (channel.getIsImport()) {
						hhStream = importFromNet;
					} else {
						hhStream = exportToNet;
					}
				} else {
					if (channel.getIsImport()) {
						hhStream = importFromGen;
					} else {
						hhStream = exportToGen;
					}
				}
				List<HhDatum> hhData = channel.getHhData(getFrom(), getTo());
				if (hhData.isEmpty()) {
					continue;
				}
				int i = 0;
				int missing = 0;
				hhEndDate = getFrom();
				while (!hhEndDate.getDate().after(getTo().getDate())) {
					HhDatum datum = null;
					if (i - missing < hhData.size()) {
						datum = hhData.get(i - missing);
						if (!hhEndDate.equals(datum.getEndDate())) {
							missing++;
						} else {
							hhStream.set(i, hhStream.get(i) + datum.getValue());
						}
					}
					i++;
					hhEndDate = hhEndDate.getNext();
				}
			}
		}
		return map;
	}

	public void addDceSnag(String description, HhEndDate startDate,
			HhEndDate finishDate, boolean isResolved)
			throws InternalException, HttpException {
		// which sevice?
		Site site = sites.get(0);
		HhdcContract service = getDceService(startDate);
		HhEndDate serviceEndDate = service.getFinishRateScript()
				.getFinishDate();
		SnagDateBounded
				.addSiteSnag(service, site, description, startDate,
						serviceEndDate == null
								|| serviceEndDate.getDate().after(
										finishDate.getDate()) ? finishDate
								: serviceEndDate, isResolved);
		while (!(serviceEndDate == null || !serviceEndDate.getDate().before(
				finishDate.getDate()))) {
			service = getDceService(serviceEndDate.getNext());
			serviceEndDate = service.getFinishRateScript().getFinishDate();
			SnagDateBounded.addSiteSnag(service, site, description, service
					.getStartRateScript().getStartDate(),
					serviceEndDate == null
							|| serviceEndDate.getDate().after(
									finishDate.getDate()) ? finishDate
							: serviceEndDate, isResolved);
		}
	}

	@SuppressWarnings("unchecked")
	private HhdcContract getDceService(HhEndDate date) throws HttpException,
			InternalException {
		List<Long> serviceIds = (List<Long>) Hiber
				.session()
				.createQuery(
						"select distinct mpan.dceService.id from Mpan mpan where mpan.supplyGeneration.supply in (:supplies) and mpan.supplyGeneration.startDate.date <= :date and (mpan.supplyGeneration.finishDate.date is null or mpan.supplyGeneration.finishDate >= :date) order by mpan.dceService.id")
				.setParameterList("supplies", supplies).setTimestamp("date",
						date.getDate()).list();
		return serviceIds.size() > 0 ? HhdcContract.getDceService(serviceIds
				.get(0)) : null;
	}

	@SuppressWarnings("unchecked")
	public void resolveDceSnag(String description, HhEndDate startDate,
			HhEndDate finishDate) throws InternalException, HttpException {
		if (!startDate.getDate().after(finishDate.getDate())) {
			for (SiteSnag snag : (List<SiteSnag>) Hiber
					.session()
					.createQuery(
							"from SiteSnag snag where snag.site = :site and snag.description = :description and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and snag.dateResolved is null")
					.setEntity("site", sites.get(0)).setString("description",
							description.toString()).setTimestamp("startDate",
							startDate.getDate()).setTimestamp("finishDate",
							finishDate.getDate()).list()) {
				addDceSnag(description, snag.getStartDate().getDate().before(
						startDate.getDate()) ? startDate : snag.getStartDate(),
						snag.getFinishDate().getDate().after(
								finishDate.getDate()) ? finishDate : snag
								.getFinishDate(), true);
			}
		}
	}
}
