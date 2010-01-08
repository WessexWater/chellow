Chellow
=======

Web site: http://chellow.wikispaces.com/


License
-------
Chellow is released under the GPL.


Upgrade
-------
To upgrade from version 289:

1. Create a new report in the current version of Chellow. Paste in the script
that's included at the end of this README.

2. Run the report, which will generate a zip file of your data.

3. Install the new version of Chellow.

4. Go to General Imports and import the zip file.

from net.sf.chellow.monad import Hiber, UserException, MonadUtils
from net.sf.chellow.monad.types import UriPathElement
from java.util import GregorianCalendar, TimeZone, Locale, Calendar
from net.sf.chellow.physical import HhEndDate, Configuration
from java.text import DateFormat
from java.util.zip import ZipOutputStream, ZipEntry
from java.io import OutputStreamWriter, PrintWriter
from java.security import MessageDigest
from com.Ostermiller.util import Base64
from java.lang import String, System, Boolean

def mpan_fields(mpan):
    if mpan == None:
        return ['', '', '', '', '']
    else:
        pcnum = mpan.getPc().getCode()
        mpan_str = mpan.toString()
        ssc = mpan.getSsc()

        if pcnum == 0 and ssc is not None:
            raise Exception('error type 1 ' + mpan_str)
        if pcnum > 0 and ssc is None:
            raise Exception('error type 2 ' + mpan_str)



        if ssc is None:
            ssc_code = ''
        else:
            ssc_code = ssc.getCode()
        supply_capacity = str(mpan.getAgreedSupplyCapacity())
        supplier_account = mpan.getSupplierAccount()
        supplier_contract_name = supplier_account.getContract().getName()
        supplier_account_reference = supplier_account.getReference()
    return [mpan_str, ssc_code, supply_capacity, supplier_contract_name, supplier_account_reference]

def print_line(pw, values):
    pw.println('    <line>')
    for value in values:
        if value is None:
            value = ''
        else:
            value = str(value)
        pw.println('        <value><' + '![CDATA[' + value + ']]' + '></value>')
    pw.println('    </line>')
    pw.flush()


inv.getResponse().setContentType('application/zip')
inv.getResponse().setHeader('Content-Disposition', 'filename=output.zip;')
sout = inv.getResponse().getOutputStream()
zout = ZipOutputStream(sout)
pw = PrintWriter(OutputStreamWriter(zout, 'UTF-8'))
zout.putNextEntry(ZipEntry('out.xml'))

#inv.getResponse().setContentType('text/xml')
#inv.getResponse().setHeader('Content-Disposition', 'attachment; filename=output.xml;')
#pw = inv.getResponse().getWriter()

struct_only = inv.hasParameter('struct-only')

pw.println('<' + '?xml version="1.0"?>')
pw.flush()
pw.println('<csv>')

# Reports

reports = Hiber.session().createQuery("from Report report where report.name not like '0 %' order by report.id").scroll()
while reports.next():
    report = reports.get(0)
    print_line(pw, ['insert', 'report', str(report.getId()), report.getName(), report.getScript(), report.getTemplate()])


# Users

users = Hiber.session().createQuery("from User user order by user.id").scroll()
while users.next():
    user = users.get(0)
    email_address = user.getEmailAddress().toString()
    if email_address == 'administrator@localhost':
        print_line(pw, ['update', 'user', 'administrator@localhost', '{no change}', '', user.getPasswordDigest(), user.getRole().getCode(), '', ''])
    else:
        print_line(pw, ['insert', 'user', user.getEmailAddress(), '', user.getPasswordDigest(), user.getRole().getCode(), '', ''])
users.close()


# Configuration

print_line(pw, ['update', 'configuration', Configuration.getConfiguration().getProperties()])


# Sites

sites = Hiber.session().createQuery('from Site site order by site.id').scroll()
while sites.next():
    site = sites.get(0)
    print_line(pw, ['insert', 'site', site.getCode(), site.getName()])
sites.close()


# HHDC Contracts

contracts = Hiber.session().createQuery("from HhdcContract contract order by contract.id").scroll()
while contracts.next():
    contract = contracts.get(0)
    rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
    start_rate_script = rate_scripts[0]
    print_line(pw, ['insert', 'hhdc-contract', contract.getParty().getParticipant().getCode(), contract.getName(), start_rate_script.getStartDate(), start_rate_script.getFinishDate(), contract.getChargeScript(), start_rate_script.getScript(), contract.getProperties(), contract.getState()])
    if len(rate_scripts) > 1:
        for rate_script in rate_scripts[1:]:
            print_line(pw, ['insert', 'hhdc-contract-rate-script', contract.getName(), rate_script.getStartDate(), rate_script.getFinishDate(), rate_script.getScript()])
Hiber.session().clear()
contracts.close()


# Supplier Contracts

contracts = Hiber.session().createQuery("from SupplierContract contract order by contract.id").scroll()
while contracts.next():
    contract = contracts.get(0)
    contract_name = contract.getName()
    rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
    start_rate_script = rate_scripts[0]
    finish_rate_script = rate_scripts[len(rate_scripts) - 1]
    print_line(pw, ['insert', 'supplier-contract', contract.getParty().getParticipant().getCode(), contract_name, start_rate_script.getStartDate(), finish_rate_script.getFinishDate(), contract.getChargeScript(), start_rate_script.getScript()])
    if len(rate_scripts) > 1:
        for i in range(1, len(rate_scripts)):
            rate_script = rate_scripts[i]
            print_line(pw, ['insert', 'supplier-contract-rate-script', contract.getName(), rate_script.getStartDate(), rate_script.getScript()])
Hiber.session().clear()
contracts.close()


# Supplies

supplies = Hiber.session().createQuery("from Supply supply order by supply.id").scroll()
#supplies.last()
#supplies.previous()
while supplies.next():
    supply = supplies.get(0) 
    supplyGenerations = Hiber.session().createQuery('from SupplyGeneration generation where generation.supply = :supply order by generation.startDate.date').setEntity('supply', supply).list()
    first_generation = supplyGenerations[0]
    last_generation = supplyGenerations[len(supplyGenerations) - 1]
    physical_site = Hiber.session().createQuery("select siteSupplyGeneration.site from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.isPhysical is true").setEntity('supplyGeneration', last_generation).uniqueResult()
    site_code = physical_site.getCode()
    supply_name = supply.getName()
    start_date = first_generation.getStartDate().toString()
    finish_date = last_generation.getFinishDate()
    if finish_date is None:
        finish_date = ''
    else:
        finish_date = finish_date.toString()
    meter = last_generation.getMeter()
    if meter is None:
        meter_serial_number = ''
    else:
        meter_serial_number = meter.getSerialNumber()
    source = supply.getSource().getCode()
    generator_type = supply.getGeneratorType()
    if generator_type is None:
        generator_type = ''
    else:
        generator_type = generator_type.getCode()
    hhdc_account = first_generation.getMpans()[0].getHhdcAccount()
    if hhdc_account is None:
        hhdc_contract_name = ''
        hhdc_account_reference = ''
    else:
        hhdc_contract_name = hhdc_account.getContract().getName()
        hhdc_account_reference = hhdc_account.getReference()
    has_import_kwh = 'False'
    has_import_kvarh = 'False'
    has_export_kwh = 'False'
    has_export_kvarh = 'False'
    for mpan in first_generation.getMpans():
        if mpan.getHasImportKwh():
            has_import_kwh = 'True'
        if mpan.getHasImportKvarh():
            has_import_kvarh = 'True'
        if mpan.getHasExportKwh():
            has_export_kwh = 'True'
        if mpan.getHasExportKvarh():
            has_export_kvarh = 'True'
    values = ['insert', 'supply', site_code, source, generator_type, supply_name, first_generation.mpans[0].getGspGroup().getCode(), start_date, finish_date, hhdc_contract_name, hhdc_account_reference, has_import_kwh, has_import_kvarh, has_export_kwh, has_export_kvarh, meter_serial_number]
    values = values + mpan_fields(first_generation.getImportMpan())
    values = values + mpan_fields(first_generation.getExportMpan())
    print_line(pw, values)
    generations = Hiber.session().createQuery("from SupplyGeneration generation where generation.supply = :supply order by generation.startDate.date").setEntity('supply', supply).scroll()
    generations.next()
    while generations.next():
        generation = generations.get(0)
        physical_site = Hiber.session().createQuery("select siteSupplyGeneration.site from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.isPhysical is true").setEntity('supplyGeneration', last_generation).uniqueResult()
        site_code = physical_site.getCode()
        start_date = generation.getStartDate()
        hhdc_account = generation.getMpans()[0].getHhdcAccount()
        if hhdc_account is None:
            hhdc_contract_name = ''
            hhdc_account_reference = ''
        else:
            hhdc_contract_name = hhdc_account.getContract().getName()
            hhdc_account_reference = hhdc_account.getReference()
        has_import_kwh = 'False'
        has_import_kvarh = 'False'
        has_export_kwh = 'False'
        has_export_kvarh = 'False'
        for mpan in generation.getMpans():
            if mpan.getHasImportKwh():
                has_import_kwh = 'True'
            if mpan.getHasImportKvarh():
                has_import_kvarh = 'True'
            if mpan.getHasExportKwh():
                has_export_kwh = 'True'
            if mpan.getHasExportKvarh():
                has_export_kvarh = 'True'
        meter = generation.getMeter()
        if meter is None:
            meter_serial_number = ''
        else:
            meter_serial_number = meter.getSerialNumber()
        values = ['insert', 'supply-generation', site_code, start_date, hhdc_contract_name, hhdc_account_reference, has_import_kwh, has_import_kvarh, has_export_kwh, has_export_kvarh, meter_serial_number]
        values = values + mpan_fields(generation.getImportMpan())
        values = values + mpan_fields(generation.getExportMpan())
        print_line(pw, values)
    generations.beforeFirst()
    while generations.next():
        generation = generations.get(0)
        start_date = generation.getStartDate()
        finish_date = generation.getFinishDate()
        site_supply_generations = Hiber.session().createQuery("from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.isPhysical is false").setEntity('supplyGeneration', generation).scroll()
        while site_supply_generations.next():
            site_supply_generation = site_supply_generations.get(0)
            print_line(pw, ['insert', 'site-supply-generation', site_supply_generation.getSite().getCode(), generation.getMpans()[0].getCore(), start_date, 'false'])
        site_supply_generations.close()
        query = "select datum.endDate, datum.value, datum.status from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.endDate.date >= :startDate"
        if finish_date is None:
            hh_data_q = Hiber.session().createQuery(query + " order by datum.endDate.date").setTimestamp('startDate', start_date.getDate())
        else:
            hh_data_q = Hiber.session().createQuery(query + " and datum.endDate.date <= :finishDate  order by datum.endDate.date").setTimestamp('finishDate', finish_date.getDate())
        hh_data_q.setTimestamp('startDate', start_date.getDate()).setEntity('supply', supply)
        mpan_core_str = generation.getMpans()[0].getCore().toString()
        channels = Hiber.session().createQuery("from Channel channel where channel.supplyGeneration = :supplyGeneration").setEntity('supplyGeneration', generation).scroll()
        while channels.next():
            channel = channels.get(0)
            if channel.getIsImport():
                is_import = 'true'
            else:
                is_import = 'false'
            if channel.getIsKwh():
                is_kwh = 'true'
            else:
                is_kwh = 'false'
            if not struct_only:
                hh_data_q.setBoolean('isImport', channel.getIsImport()).setBoolean('isKwh', channel.getIsKwh()),
                hh_data = hh_data_q.scroll()
                hh_str = ''
                prev_end_date = None
                count = 0
                while hh_data.next():
                    end_date = hh_data.get(0)
                    if prev_end_date is None or not prev_end_date.getNext().getDate().equals(end_date.getDate()) or count > 1000:
                        if prev_end_date is not None:
                            pw.println('</value>')
                            pw.println('    </line>')
                        pw.println('    <line>')
                        for value in ['insert', 'hh-datum', mpan_core_str, str(end_date), is_import, is_kwh]:
                            pw.println('        <value>' + value + '</value>')
                        pw.print('        <value>')
                        count = 0
                    else:
                        pw.print(',')
                    status = hh_data.get(2)
                    if status is None:
                        status = ''
                    pw.print(str(hh_data.get(1)) + ',' + status)
                    prev_end_date = end_date
                    count = count + 1
                if prev_end_date is not None:
                    pw.println('</value>')
                    pw.println('    </line>')
                hh_data.close()
        channels.close()
    generations.close()
    Hiber.session().clear()
supplies.close()

# Channel Snag Ignorals
timing = System.currentTimeMillis()
#pw.println('about to start ' + str(System.currentTimeMillis() - timing))
snags = Hiber.session().createQuery("from ChannelSnag snag where snag.isIgnored is true").scroll()
#pw.println('finished ' + str(System.currentTimeMillis() - timing))
while snags.next():
    snag = snags.get(0)
    channel = snag.getChannel()
    print_line(pw, ['insert', 'channel-snag-ignore', channel.getSupplyGeneration().getMpans()[0].getCore().toString(), Boolean.toString(channel.getIsImport()), Boolean.toString(channel.getIsKwh()), snag.getStartDate(), snag.getFinishDate()])
    Hiber.session().clear()
snags.close()

pw.println('</csv>')
pw.flush()
pw.close()