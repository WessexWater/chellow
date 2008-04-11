from net.sf.chellow.monad import Hiber, UserException
from java.util import GregorianCalendar, TimeZone, Locale, Calendar
from net.sf.chellow.physical import HhEndDate
from java.text import DateFormat

year = inv.getInteger("year")
month = inv.getInteger("month")
if not inv.isValid():
    raise UserException.newInvalidParameter()
cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal_ct = GregorianCalendar(TimeZone.getTimeZone("BST"), Locale.UK)
cal.clear()
cal.set(Calendar.YEAR, year)
cal.set(Calendar.MONTH, month - 1)
startDate = HhEndDate(cal.getTime()).getNext()
cal.add(Calendar.MONTH, 1)
finishDate = HhEndDate(cal.getTime())
inv.getResponse().setContentType("text/plain")
pw = inv.getResponse().getWriter()
pw.print("Site Code,Site Name,Associated Sites,TRIAD kW\n")
dateFormat = DateFormat.getDateInstance(DateFormat.LONG, Locale.UK)
dateFormat.applyLocalizedPattern("yyyy-MM-dd")
for site in Hiber.session().createQuery("select distinct site from Site site join site.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.supplyGeneration.supply.source.code.string in ('lm','chp','turb') and site.organization = :organization and siteSupplyGeneration.supplyGeneration.startDate.date <= :finishDate and (siteSupplyGeneration.supplyGeneration.finishDate.date = null or siteSupplyGeneration.supplyGeneration.finishDate.date >= :startDate) order by site.code.string").setEntity('organization', organization).setTimestamp('startDate', startDate.getDate()).setTimestamp('finishDate', finishDate.getDate()).list():
    pw.print('main site ' + site.getCode().toString())
    pw.flush()
    for group in organization.getSite(site.getId()).groups(startDate, finishDate):
        sites = group.getSites()
        pw.print(' sites ')
        for sitee in sites:
            pw.print(sitee.getCode().toString())
        pw.print(' endsites')
        pw.flush()
        '''
        site_code = sites[0].getCode().toString()
        site_name = sites[0].getName()
        has_triad_est = False
        associate_string = ''
        for i in range(1, len(sites) - 1):
            associate_string = associate_string + sites[i].getCode().toString() + ' '
        supplies = group.getSupplies()
        primary_supply = None
        for supply in supplies:
            source_code = supply.getSource().getCode().toString()
            if source_code == 'lm' or source_code == 'turb':
                has_triad_est = True
            pw.print('site ' + site_code + ' source_code ' + source_code + ' supply id ' + str(supply.getId()))
            pw.print('supply name ' + supply.getName().toString())
            if primary_supply == None and source_code == 'net':
                primary_supply = supply
        pw.print(' primary supply ' + str(primary_supply.getId()) + ' date ' + startDate.toString())
        primary_supply_generation = primary_supply.getGeneration(startDate)
        #pw.print('primary supp generation ' + str(primary_supply_generation.getId()))
        for mpan in primary_supply_generation.getMpans():
            if int(mpan.getMpanCore().getDso().getCode().toString()) < 24:
                #pw.print('found primary mpan')
                primary_mpan = mpan
                break
        is_substation = primary_mpan.getLineLossFactor().getIsSubstation().getBoolean()
        dso = primary_mpan.getMpanCore().getDso()
        dso_service = dso.getService('main')
        voltage_level = primary_mpan.getLineLossFactor().getVoltageLevel().getCode().toString()
        llf_calculator = dso_service.callFunction('llf_calculator', [voltage_level, is_substation])
        hh_date = group.getFrom()
        num_triad_kwh = 0
        triad_kwh = 0
        stream_map = group.hhData()
        i = 0
        import_from_net = stream_map['import-from-net']
        export_to_net = stream_map['export-to-net']
        import_from_gen = stream_map['import-from-gen']
        export_to_gen = stream_map['export-to-gen']
        while not hh_date.getDate().after(group.getTo().getDate()):
            displaced_hh = import_from_gen[i] - export_to_gen[i] - export_to_net[i]
            used_hh = displaced_hh + import_from_net[i]
            cal.setTime(hh_date.getDate())
            year = cal.get(Calendar.YEAR)
            month = cal.get(Calendar.MONTH)
            day = cal.get(Calendar.DAY_OF_MONTH)
            day_of_week = cal.get(Calendar.DAY_OF_WEEK)
            hour = cal.get(Calendar.HOUR_OF_DAY)
            minute = cal.get(Calendar.MINUTE)
            decimal_hour = hour + minute / 60
            cal_ct.setTime(hh_date.getDate())
            year_ct = cal_ct.get(Calendar.YEAR)
            month_ct = cal_ct.get(Calendar.MONTH)
            day_ct = cal_ct.get(Calendar.DAY_OF_MONTH)
            day_of_week_ct = cal_ct.get(Calendar.DAY_OF_WEEK)
            hour_ct = cal_ct.get(Calendar.HOUR_OF_DAY)
            minute_ct = cal_ct.get(Calendar.MINUTE)
            decimal_hour_ct = hour_ct + minute_ct / 60            
            if decimal_hour >= 16 and decimal_hour <= 19 and (month > 9 or month < 2) and day_of_week > 1 and day_of_week < 7:
                num_triad_kwh = num_triad_kwh + 1
                triad_kwh = triad_kwh + used_hh * llf_calculator.llf(hh_date, year, month, day, day_of_week, hour, minute, decimal_hour, year_ct, month_ct, day_ct, day_of_week_ct, hour_ct, minute_ct, decimal_hour_ct)
                i = i + 1
            hh_date = hh_date.getNext()
        if has_triad_est:
            est_triad_kw = triad_kwh / 4 / num_triad_kwh * 2
        else:
            est_triad_kw = 0
        pw.print('"' + site_code + '","' + site_name + '","' + associate_string + '",' + str(round(est_triad_kw, 1)) + '\n')
        pw.flush()
        '''
    Hiber.session().clear()
pw.close()