Chellow
=======

Web site: http://chellow.wikispaces.com/
Change Log: http://chellow.svn.sourceforge.net/viewvc/chellow/trunk/?view=log

License
-------
Chellow is released under the GPL.


Requirements
------------
PostgreSQL 8.4.2 with JDBC Driver PostgreSQL 8.4 JDBC4 (build 701)
OpenJDK 6b16
Apache Tomcat 6


Installation
------------
1. Create a PostgreSQL database called chellow.

2. In your Tomcat, configure a JNDI JDBC datasource called jdbc/chellow.
    a) Copy context.xml from the same directory as this file, and update with your own settings.
    b) Install the JDBC driver from
          http://jdbc.postgresql.org/download/postgresql-8.4-701.jdbc4.jar
          in the /lib/ directory.
         
3. Deploy the file chellow.war on your servlet container.


Upgrade From Version 357
------------------------
1. Copy the report at the bottom of this file, and run it with the following parameters to export the user data:

/reports/<report number>/output/?is_core=false&has-reports=true&has-supplier-contracts=true&has-hhdc-contracts=true&has-sites=true&has-supplies=true&has-hh-data=true&has-users=true&has-configuration=true&has-channel-snag-ignorals=true&mpan-core=

2. Install Chellow afresh with a blank database.
3. Import the user data by going to General Imports section.


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
        pcnum = mpan.getSupplyGeneration().getPc().getCode()
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
        supplier_contract = mpan.getSupplierContract()
        supplier_contract_name = supplier_contract.getName()
        supplier_account = mpan.getSupplierAccount()
    return [mpan_str, ssc_code, supply_capacity, supplier_contract_name, supplier_account]

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


#inv.getResponse().setContentType('application/zip')
#inv.getResponse().setHeader('Content-Disposition', 'filename=output.zip;')
#sout = inv.getResponse().getOutputStream()
#zout = ZipOutputStream(sout)
#pw = PrintWriter(OutputStreamWriter(zout, 'UTF-8'))
#zout.putNextEntry(ZipEntry('out.xml'))

inv.getResponse().setContentType('text/xml')
inv.getResponse().setHeader('Content-Disposition', 'attachment; filename=output.xml;')
pw = inv.getResponse().getWriter()

is_core = inv.getBoolean('is-core')
has_dso_contracts = inv.getBoolean('has-dso-contracts')    
has_non_core_contracts = inv.getBoolean('has-non-core-contracts')
has_reports = inv.getBoolean('has-reports')
has_supplier_contracts = inv.getBoolean('has-supplier-contracts')
has_hhdc_contracts = inv.getBoolean('has-hhdc-contracts')
has_sites = inv.getBoolean('has-sites')    
has_supplies = inv.getBoolean('has-supplies')
has_hh_data = inv.getBoolean('has-hh-data')
has_users = inv.getBoolean('has-users')
has_configuration = inv.getBoolean('has-configuration')
has_channel_snag_ignorals = inv.getBoolean('has-channel-snag-ignorals')

if not inv.isValid():
    raise UserException()

if has_supplies:
    mpan_core_str = inv.getString('mpan-core')

pw.println('<' + '?xml version="1.0"?>')
pw.flush()
pw.println('<csv>')

if has_reports:
    if is_core:
        qstring = "from Report report where report.name like '0 %'"
    else:
        qstring = "from Report report where report.name not like '0 %'"
    reports = Hiber.session().createQuery(qstring + " order by report.id").scroll()
    while reports.next():
        report = reports.get(0)
        template = report.getTemplate()
        if template is not None:
            template = template.replace("<!" + "[CDATA[", "&" + "lt;![CDATA[").replace("]]" + ">", "]]" + "&" + "gt;")
        print_line(pw, ['insert', 'report', str(report.getId()), report.getName(), report.getScript().replace("<!" + "[CDATA[", "&" + "lt;![CDATA[").replace("]]" + ">", "]]" + "&" + "gt;"), template])
    reports.close()

if has_dso_contracts and is_core:
    contracts = Hiber.session().createQuery("from DsoContract contract order by contract.party.code, contract.name").scroll()
    while contracts.next():
        contract = contracts.get(0)
        contract_name = contract.getName()
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
        start_rate_script = rate_scripts[0]
        finish_date = rate_scripts[len(rate_scripts) - 1].getFinishDate()
        if finish_date != None:
            finish_date = finish_date.getPrevious()
        print_line(pw, ['insert', 'dso-contract', contract.getParty().getCode(), contract_name, start_rate_script.getStartDate().getPrevious(), finish_date, contract.getChargeScript(), start_rate_script.getScript()])
        for i in range(1, len(rate_scripts)):
            rate_script = rate_scripts[i]
            print_line(pw, ['insert', 'dso-contract-rate-script', contract.getParty().getCode(), contract.getName(), rate_script.getStartDate().getPrevious(), rate_script.getScript()])
    Hiber.session().clear()
    contracts.close()


if has_non_core_contracts:
    q = "from NonCoreContract contract where contract.name"
    if is_core:
        q += " not"
    q += " in ('EnergyChanges', 'TRIAD Estimates') order by contract.name"

    contracts = Hiber.session().createQuery(q).scroll()
    while contracts.next():
        contract = contracts.get(0)
        contract_name = contract.getName()
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract = :contract order by script.startDate.date").setEntity('contract', contract).list()
        start_rate_script = rate_scripts[0]
        finish_date = rate_scripts[len(rate_scripts) - 1].getFinishDate()
        if finish_date is None:
            finish_date = finish_date.getPrevious()
        print_line(pw, ['insert', 'non-core-contract', contract.getParty().getParticipant().getCode(), contract_name, start_rate_script.getStartDate().getPrevious(), finish_date, contract.getChargeScript(), start_rate_script.getScript()])
        for i in range(1, len(rate_scripts)):
            rate_script = rate_scripts[i]
            print_line(pw, ['insert', 'non-core-contract-rate-script', contract_name, rate_script.getStartDate().getPrevious(), rate_script.getScript()])
    Hiber.session().clear()
    contracts.close()


if has_users and not is_core:
    users = Hiber.session().createQuery("from User user order by user.id").scroll()
    while users.next():
        user = users.get(0)
        email_address = user.getEmailAddress().toString()
        if email_address == 'administrator@localhost':
            print_line(pw, ['update', 'user', 'administrator@localhost', '{no change}', '', user.getPasswordDigest(), user.getRole().getCode(), '', ''])
        else:
            print_line(pw, ['insert', 'user', user.getEmailAddress(), '', user.getPasswordDigest(), user.getRole().getCode(), '', ''])
    users.close()


if has_configuration and not is_core:
    print_line(pw, ['update', 'configuration', Configuration.getConfiguration().getProperties()])


if has_sites and not is_core:
    sites = Hiber.session().createQuery("from Site site order by site.id").scroll()
    while sites.next():
        site = sites.get(0)
        print_line(pw, ['insert', 'site', site.getCode(), site.getName()])
    sites.close()


if has_hhdc_contracts and not is_core:
    contracts = Hiber.session().createQuery("from HhdcContract contract order by contract.id").scroll()
    while contracts.next():
        contract = contracts.get(0)
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
        start_rate_script = rate_scripts[0]
        finish_date = rate_scripts[len(rate_scripts) - 1].getFinishDate()
        if finish_date is not None:
            finish_date = finish_date.getPrevious()
        print_line(pw, ['insert', 'hhdc-contract', contract.getParty().getParticipant().getCode(), contract.getName(), start_rate_script.getStartDate().getPrevious(), finish_date, contract.getChargeScript(), contract.getProperties(), contract.getState(), start_rate_script.getScript()])
        if len(rate_scripts) > 1:
            for rate_script in rate_scripts[1:]:
                print_line(pw, ['insert', 'hhdc-contract-rate-script', contract.getName(), rate_script.getStartDate().getPrevious(), rate_script.getScript()])
    Hiber.session().clear()
    contracts.close()


if has_supplier_contracts and not is_core:
    contracts = Hiber.session().createQuery("from SupplierContract contract order by contract.id").scroll()
    while contracts.next():
        contract = contracts.get(0)
        contract_name = contract.getName()
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
        start_rate_script = rate_scripts[0]
        finish_date = rate_scripts[len(rate_scripts) - 1].getFinishDate()
        if finish_date is not None:
            finish_date.getPrevious()
        print_line(pw, ['insert', 'supplier-contract', contract.getParty().getParticipant().getCode(), contract_name, start_rate_script.getStartDate().getPrevious(), finish_date, contract.getChargeScript(), start_rate_script.getScript()])
        if len(rate_scripts) > 1:
            for i in range(1, len(rate_scripts)):
                rate_script = rate_scripts[i]
                print_line(pw, ['insert', 'supplier-contract-rate-script', contract.getName(), rate_script.getStartDate().getPrevious(), rate_script.getScript()])
    Hiber.session().clear()
    contracts.close()


if has_supplies and not is_core:
    if len(mpan_core_str) == 0:
        supplies = Hiber.session().createQuery("from Supply supply order by supply.id").scroll()
    else:
        supplies = Hiber.session().createQuery("from Supply supply where supply = :supply").setEntity('supply', MpanCore.getMpanCore(mpan_core_str)
.getSupply()).scroll()
    while supplies.next():
        supply = supplies.get(0) 
        supplyGenerations = Hiber.session().createQuery('from SupplyGeneration generation where generation.supply = :supply order by generation.startDate.date').setEntity('supply', supply).list()
        first_generation = supplyGenerations[0]
        last_generation = supplyGenerations[len(supplyGenerations) - 1]
        physical_site = Hiber.session().createQuery("select siteSupplyGeneration.site from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.isPhysical is true").setEntity('supplyGeneration', last_generation).uniqueResult()
        site_code = physical_site.getCode()
        supply_name = supply.getName()
        start_date = first_generation.getStartDate().getPrevious().toString()
        finish_date = last_generation.getFinishDate()
        if finish_date is None:
            finish_date = ''
        else:
            finish_date = finish_date.getPrevious().toString()
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
        hhdc_contract = first_generation.getHhdcContract()
        if hhdc_contract is None:
            hhdc_contract_name = ''
            hhdc_account = ''
        else:
            hhdc_contract_name = hhdc_contract.getName()
            hhdc_account = first_generation.getHhdcAccount()
        values = ['insert', 'supply', site_code, source, generator_type, supply_name, supply.getGspGroup().getCode(), start_date, finish_date, hhdc_contract_name, hhdc_account]
        for is_import in [True, False]:
            for is_kwh in [True, False]:
                values.append(Boolean(first_generation.getChannel(is_import, is_kwh) != None))
        values.append(meter_serial_number)
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
            hhdc_contract = generation.getHhdcContract()
            if hhdc_contract is None:
                hhdc_contract_name = ''
                hhdc_account = ''
            else:
                hhdc_contract_name = hhdc_contract.getName()
                hhdc_account = generation.getHhdcAccount()
            meter = generation.getMeter()
            if meter is None:
                meter_serial_number = ''
            else:
                meter_serial_number = meter.getSerialNumber()
            values = ['insert', 'supply-generation', site_code, start_date.getPrevious(), hhdc_contract_name, hhdc_account]
            for is_import in [True, False]:
                for is_kwh in [True, False]:
                    values.append(Boolean(generation.getChannel(is_import, is_kwh) != None))
            values.append(meter_serial_number)
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
                print_line(pw, ['insert', 'site-supply-generation', site_supply_generation.getSite().getCode(), generation.getMpans().iterator().next().getCore(), start_date.getPrevious(), 'false'])
            site_supply_generations.close()
            query = "select datum.endDate, datum.value, datum.status from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.endDate.date >= :startDate"
            if finish_date is None:
                hh_data_q = Hiber.session().createQuery(query + " order by datum.endDate.date").setTimestamp('startDate', start_date.getDate())
            else:
                hh_data_q = Hiber.session().createQuery(query + " and datum.endDate.date <= :finishDate  order by datum.endDate.date").setTimestamp('finishDate', finish_date.getDate())
            hh_data_q.setTimestamp('startDate', start_date.getDate()).setEntity('supply', supply)
            mpan_core_str = generation.getMpans().iterator().next().getCore().toString()
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
                if has_hh_data:
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
                            for value in ['insert', 'hh-datum', mpan_core_str, str(end_date.getPrevious()), is_import, is_kwh]:
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


if has_channel_snag_ignorals and not is_core:
    timing = System.currentTimeMillis()
    #pw.println('about to start ' + str(System.currentTimeMillis() - timing))
    snags = Hiber.session().createQuery("from ChannelSnag snag where snag.isIgnored is true").scroll()
    #pw.println('finished ' + str(System.currentTimeMillis() - timing))
    while snags.next():
        snag = snags.get(0)
        channel = snag.getChannel()
        finish_date = snag.getFinishDate()
        if finish_date is not None:
            finish_date = finish_date.getPrevious()
        print_line(pw, ['insert', 'channel-snag-ignore', channel.getSupplyGeneration().getMpans().iterator().next().getCore().toString(), Boolean(channel.getIsImport()), Boolean(channel.getIsKwh()), snag.getStartDate().getPrevious(), finish_date])
        Hiber.session().clear()
    snags.close()

pw.println('</csv>')
pw.flush()
pw.close()