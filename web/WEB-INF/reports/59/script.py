from net.sf.chellow.monad import Hiber, UserException
from java.lang import System
from net.sf.chellow.monad.types import MonadDate
import math
from java.sql import Timestamp, ResultSet
from java.util import GregorianCalendar, Calendar, TimeZone, Locale, Date
from net.sf.chellow.physical import HhStartDate

year = inv.getInteger("year")
month = inv.getInteger("month")
months = inv.getInteger("months")

cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.clear()
cal.set(Calendar.YEAR, year)
cal.set(Calendar.MONTH, month - 1)
cal.add(Calendar.MONTH, 1)
finish_date = HhStartDate(cal.getTime())
cal.add(Calendar.MONTH, -1 * months)
cal.add(Calendar.MINUTE, 30)
start_date = HhStartDate(cal.getTime())

inv.getResponse().setContentType("text/csv")
inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="output.csv"')
pw = inv.getResponse().getWriter()
pw.println("Site Id, Site Name, Associated Site Ids, Sources, Generator Types, From, To, Imported kWh, Displaced kWh, Exported kWh, Used kWh, Parasitic kWh, Generated kWh,Meter Type")
pw.flush()
sites = Hiber.session().createQuery("from Site site order by site.code").scroll()
while sites.next():
    query = Hiber.session().createQuery("select sum(datum.value) from HhDatum datum where datum.channel.era = :era and datum.channel.isImport is :isImport and datum.channel.isKwh is true and datum.channel.era.supply.source.code in (:sources) and datum.startDate.date >= :startDate and datum.startDate <= :finishDate")
    site = sites.get(0)
    site_code = site.getCode()
    associates = []
    sources = []
    generator_types = []
    has_physical = False
    site_supply_eras = Hiber.session().createQuery("from SiteEra siteEra where siteEra.site = :site and siteEra.isPhysical is true and siteEra.era.supply.source.code != 'sub' and siteEra.era.startDate.date <= :finishDate and (siteEra.era.finishDate is null or siteEra.era.finishDate.date >= :startDate)").setEntity('site', site).setTimestamp('startDate', start_date.getDate()).setTimestamp('finishDate', finish_date.getDate()).scroll()
    import_from_net = 0
    export_to_net = 0
    import_from_gen = 0
    export_to_gen = 0
    metering_type = 'nhh'
    while site_supply_eras.next():
        has_physical = True
        site_supply_era = site_supply_eras.get(0)
        supply_era = site_supply_era.getEra()
        if metering_type == 'nhh' and supply_era.getChannels().size() > 0:
            metering_type = 'amr'
        if supply_era.getPc().getCode() == 0:
            metering_type = 'hh'
        for ss_gen in supply_era.getSiteEras():
            ss_gen_site_code = ss_gen.getSite().getCode()
            if ss_gen.getId() != site_supply_era.getId() and ss_gen_site_code != site_code and ss_gen_site_code not in associates:
                associates.append(ss_gen_site_code)
            sup = ss_gen.getEra().getSupply()
            ss_gen_source = sup.getSource().getCode()
            if ss_gen_source not in sources:
                sources.append(ss_gen_source)
            if sup.getGeneratorType() is not None:
                ss_gen_gtype = sup.getGeneratorType().getCode()
                if sup.getGeneratorType() not in generator_types:
                    generator_types.append(ss_gen_gtype)
        result = query.setEntity('era', supply_era).setTimestamp('startDate', start_date.getDate()).setTimestamp('finishDate', finish_date.getDate()).setBoolean('isImport', True).setParameterList('sources', ['net', 'gen-net']).uniqueResult()
        if result is not None:
            import_from_net = import_from_net + result.doubleValue()
        result = query.setBoolean('isImport', False).uniqueResult()
        if result is not None:
            export_to_net = export_to_net + result.doubleValue()
        result = query.setParameterList('sources', ['gen']).uniqueResult()
        if result is not None:
            export_to_gen = export_to_gen + result.doubleValue()
        result = query.setParameterList('sources', ['gen-net']).uniqueResult()
        if result is not None:
            import_from_gen = import_from_gen + result.doubleValue()
        result = query.setBoolean('isImport', True).uniqueResult()
        if result is not None:
            export_to_gen = export_to_gen + result.doubleValue()
        result = query.setParameterList('sources', ['gen']).uniqueResult()
        if result is not None:
            import_from_gen = import_from_gen + result.doubleValue()
    if has_physical:
        associate_str = ''
        for associate in associates:
            associate_str = associate_str + associate + ', '
        sources.sort()
        sources_str = ''
        for source in sources:
            sources_str = sources_str + source + ', '
        generator_types.sort()
        generator_types_str = ''
        for generator_type in generator_types:
            generator_types_str = generator_types_str + generator_type + ', '
        displaced = import_from_gen - export_to_net - export_to_gen
        used = displaced + import_from_net
        pw.print('"' + site_code + '","')
        pw.print(site.getName() + '","')     
        pw.print(associate_str[:-2] + '","')
        pw.print(sources_str[:-2] + '","')
        pw.print(generator_types_str[:-2] + '",')
        pw.print(start_date.toString() + ',')
        pw.print(finish_date.toString() + ',')
        pw.print(str(round(import_from_net)))
        pw.print(',' + str(round(displaced)) + ',')
        pw.print(str(round(export_to_net)) + ',')
        pw.print(str(round(used)) + ',')
        pw.print(str(round(export_to_gen)) + ',')
        pw.print(str(round(import_from_gen)) + ',' + metering_type + '\n')
    pw.flush()
    Hiber.session().clear()
sites.close()
pw.close()