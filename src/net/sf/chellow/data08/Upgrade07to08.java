package net.sf.chellow.data08;

import java.sql.Connection;

import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.UserException;

public class Upgrade07to08 {
	static final int PAGE_SIZE = 1000;

	//static private Organization organization = null;

	@SuppressWarnings("unchecked")
	static public void upgrade(Connection con) throws UserException, DesignerException {
/*
		try {
			Statement stmt = con.createStatement();
			stmt.execute("ALTER SCHEMA main RENAME TO old_main");
			SchemaUpdate suOld = new SchemaUpdate(
					net.sf.chellow.persistant07.Hiber.getConfiguration());
			suOld.execute(false, true);
			stmt.execute("create schema main");
			stmt.close();
			ContextListener.initializeDatabase();
			organization = Organizations.insertOrganization(new MonadString(
					"An Organization"));
			for (net.sf.chellow.persistant07.Supplier supplierOld : (List<net.sf.chellow.persistant07.Supplier>) net.sf.chellow.persistant07.Hiber
					.session().createQuery("from Supplier").list()) {
				Supplier supplier = organization.insertSupplier(supplierOld
						.getName());
				Debug.print("Added supplier");
				for (net.sf.chellow.persistant07.Contract contractOld : supplierOld
						.getContracts()) {
					supplier.insertContract(new ContractName(contractOld
							.getName().getString()), new ContractFrequency(
							contractOld.getFrequency().getInteger()),
							contractOld.getLag());
					Debug.print("added contract.");
				}
			}
			Hiber.close();
			Chellow.USERS_INSTANCE.insertUser(new EmailAddress(
					"admin@localhost"), new Password("administrator"));
			Chellow.USERS_INSTANCE.insertUser(new EmailAddress(
					"basic@localhost"), new Password("basic-user"));
			Hiber.close();
			for (net.sf.chellow.persistant07.Site siteOld : (List<net.sf.chellow.persistant07.Site>) net.sf.chellow.persistant07.Hiber
					.session().createQuery("from Site").list()) {
				organization.insertSite(new SiteCode(siteOld.getCode()
						.getString()), siteOld.getId());
			}
			Hiber.close();
			net.sf.chellow.persistant07.Hiber.close();
			Debug.print("Added sites.");
			List<net.sf.chellow.persistant07.Supply> suppliesOld = (List<net.sf.chellow.persistant07.Supply>) net.sf.chellow.persistant07.Hiber
					.session().createQuery("from Supply").list();
			for (net.sf.chellow.persistant07.Supply supplyOld1 : suppliesOld) {
				net.sf.chellow.persistant07.Supply supplyOld = net.sf.chellow.persistant07.Supply
						.getSupply(supplyOld1.getId());
				net.sf.chellow.persistant07.SiteSupply[] siteSuppliesOld = supplyOld
						.getSiteSupplies()
						.toArray(
								new net.sf.chellow.persistant07.SiteSupply[supplyOld
										.getSiteSupplies().size()]);
				net.sf.chellow.persistant07.SupplyGeneration[] supplyGenerationsOld = supplyOld
						.getGenerations()
						.toArray(
								new net.sf.chellow.persistant07.SupplyGeneration[supplyOld
										.getGenerations().size()]);
				net.sf.chellow.persistant07.SupplyGeneration latestSupplyGenerationOld = supplyGenerationsOld[0];
				net.sf.chellow.persistant07.Mpan latestImportMpanOld = latestSupplyGenerationOld
						.getImportMpan();
				net.sf.chellow.persistant07.Mpan latestExportMpanOld = latestSupplyGenerationOld
						.getExportMpan();
				Site site = organization.findSite(new SiteCode(
						siteSuppliesOld[0].getSite().getCode().getString()));
				SupplyName supplyName = new SupplyName(supplyOld.getName()
						.getString());
				MpanRaw latestImportMpanRaw = latestImportMpanOld == null ? null : getMpanRaw(latestImportMpanOld);
				HhdceChannels latestImportHhdceChannels = getNewHhdceChannels(latestImportMpanOld);
				MonadInteger latestImportAgreedSupplyCapacity = latestImportMpanOld == null ? null
						: latestImportMpanOld.getAgreedSupplyCapacity();
				MpanRaw latestExportMpanRaw = latestExportMpanOld == null ? null
						: getMpanRaw(latestExportMpanOld);
				HhdceChannels latestExportHhdceChannels = getNewHhdceChannels(latestExportMpanOld);
				MonadInteger latestExportAgreedSupplyCapacity = latestExportMpanOld == null ? null
						: latestExportMpanOld.getAgreedSupplyCapacity();
				Supply supply = site
						.insertSupply(
								supplyName,
								latestImportMpanRaw,
								latestImportHhdceChannels,
								latestImportAgreedSupplyCapacity,
								latestExportMpanRaw,
								latestExportHhdceChannels,
								latestExportAgreedSupplyCapacity,
								new HhEndDate(
										supplyGenerationsOld[supplyGenerationsOld.length - 1]
												.getStartDate().getDate()),
								new SourceCode(supplyOld.getSource()
										.getCode().getString()), supplyOld
										.getId());
				for (int i = 1; i < siteSuppliesOld.length; i++) {
					supply.addSiteSupply(organization
							.findSite(new SiteCode(siteSuppliesOld[i].getSite()
									.getCode().getString())));
				}
				// add in supply generations
				for (int i = 1; i < supplyGenerationsOld.length; i++) {
					net.sf.chellow.persistant07.SupplyGeneration supplyGenerationOld = supplyGenerationsOld[i];
					SupplyGeneration supplyGeneration = supply
							.addGeneration(new HhEndDate(supplyGenerationOld
									.getStartDate().getDate()));
					supplyGeneration.update(new HhEndDate(supplyGenerationOld
							.getStartDate().getDate()), new HhEndDate(
							supplyGenerationOld.getFinishDate().getDate()));
					// add in MPAN generations
					net.sf.chellow.persistant07.Mpan importMpanOld = supplyGenerationOld
							.getImportMpan();
					net.sf.chellow.persistant07.Mpan exportMpanOld = supplyGenerationOld
							.getExportMpan();
					MpanRaw importMpanRaw = importMpanOld == null ? null
							: getMpanRaw(importMpanOld);
					MpanRaw exportMpanRaw = exportMpanOld == null ? null
							: getMpanRaw(exportMpanOld);
					supplyGeneration.addOrUpdateMpans(
							importMpanRaw == null ? null : importMpanRaw
									.getMeterTimeswitch(),
							importMpanRaw == null ? null : importMpanRaw
									.getLineLossFactor(),
							importMpanRaw == null ? null : importMpanRaw
									.getMpanCore(organization),
							getNewHhdceChannels(importMpanOld),
							importMpanOld == null ? null : importMpanOld
									.getAgreedSupplyCapacity(),
							exportMpanRaw == null ? null : exportMpanRaw
									.getMeterTimeswitch(),
							exportMpanRaw == null ? null : exportMpanRaw
									.getLineLossFactor(),
							exportMpanRaw == null ? null : exportMpanRaw
									.getMpanCore(organization),
							getNewHhdceChannels(exportMpanOld),
							exportMpanOld == null ? null : exportMpanOld
									.getAgreedSupplyCapacity());
				}
				Hiber.close();
				Debug.print("Added a supply.");
			}
			List<net.sf.chellow.persistant07.Channel> channels = (List<net.sf.chellow.persistant07.Channel>) net.sf.chellow.persistant07.Hiber
					.session().createQuery("from Channel channel").list();
			for (int i = 0; i < channels.size(); i++) {
				List<net.sf.chellow.persistant07.HhDatum> hhDatumList;
				for (int j = 0; !(hhDatumList = (List<net.sf.chellow.persistant07.HhDatum>) net.sf.chellow.persistant07.Hiber
						.session()
						.createQuery(
								"from HhDatum datum where datum.channel.id = :channelId order by datum.endDate.date")
						.setLong("channelId", channels.get(i).getId())
						.setFirstResult(j * PAGE_SIZE).setMaxResults(PAGE_SIZE)
						.list()).isEmpty(); j++) {
					List<HhDatumRaw> data = new ArrayList<HhDatumRaw>();
					for (net.sf.chellow.persistant07.HhDatum hhDatumOld : hhDatumList) {
						data
								.add(new HhDatumRaw(new MpanCoreRaw(hhDatumOld
										.getChannel().getSupply()
										.getMpanCores().iterator().next()
										.getCore().toString()), new IsImport(
										hhDatumOld.getChannel().getIsImport()
												.getBoolean()), new IsKwh(
										hhDatumOld.getChannel().getIsKwh()
												.getBoolean()), new HhEndDate(
										hhDatumOld.getEndDate().getDate()),
										new HhValue(hhDatumOld.getValue()
												.getFloat().floatValue()),
										new HhDatumStatus(hhDatumOld
												.getStatus().getCharacter())));
					}
					try {
						Channel.addHhData(null, data);
					} catch (UserException e) {
						Debug.print("User Exception thrown "
								+ e.getVFMessage().getDescription());
						// If there's no channel
					}
					Debug.print("Added page of hh data.");
					Hiber.close();
					net.sf.chellow.persistant07.Hiber.close();
				}
			}
			Hiber.close();
			stmt = con.createStatement();
			stmt.execute("DROP SCHEMA old_main CASCADE");
			Debug.print("Database conversion completed successfully.");
		} catch (ProgrammerException e) {
			e.printStackTrace();
		} catch (MonadInstantiationException e) {
			e.printStackTrace();
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}

	private static HhdceChannels getNewHhdceChannels(
			net.sf.chellow.persistant07.Mpan mpanOld) throws UserException,
			ProgrammerException {
		if (mpanOld == null) {
			return null;
		}
		net.sf.chellow.persistant07.HhdceChannels hhdceChannelsOld = mpanOld
				.getHhdceChannels();
		if (hhdceChannelsOld == null) {
			return null;
		}
		Supplier supplier = organization.getSupplier(hhdceChannelsOld
				.getContract().getSupplier().getName());
		Contract contract = null;
		try {
			contract = supplier.getContract(new ContractName(hhdceChannelsOld
					.getContract().getName().getString()));
		} catch (MonadInstantiationException e) {
			throw new ProgrammerException(e);
		}
		return HhdceChannels.getHhdceChannels(contract, hhdceChannelsOld
				.getIsImportKwh(), hhdceChannelsOld.getIsImportKvarh(),
				hhdceChannelsOld.getIsExportKwh(), hhdceChannelsOld
						.getIsExportKvarh());
	}

	private static MpanRaw getMpanRaw(net.sf.chellow.persistant07.Mpan mpanOld)
			throws ProgrammerException, UserException {
		try {
			ProfileClassCode profileClassCode = new ProfileClassCode(mpanOld
					.getProfileClass().getCode().getString());
			MeterTimeswitchCode meterTimeswitchCode = new MeterTimeswitchCode(
					mpanOld.getMeterTimeswitch().getCode().getString());
			LineLossFactorCode lineLossFactorCode = new LineLossFactorCode(
					mpanOld.getLineLossFactor().getCode().getString());
			MpanCoreRaw mpanCoreRaw = new MpanCoreRaw(mpanOld.getMpanCore()
					.toString());
			return new MpanRaw(profileClassCode, meterTimeswitchCode,
					lineLossFactorCode, mpanCoreRaw);
		} catch (InvalidArgumentException e) {
			throw new ProgrammerException(e);
		} catch (MonadInstantiationException e) {
			throw new ProgrammerException(e);
		}
		*/
	}
}
