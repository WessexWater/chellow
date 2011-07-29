Chellow
=======

Web site: http://chellow.wikispaces.com/
Change Log: http://chellow.svn.sourceforge.net/viewvc/chellow/trunk/?view=log

License
-------
Chellow is released under the GPL.


Requirements
------------
PostgreSQL 8.4.8 with JDBC Driver PostgreSQL 8.4 JDBC4 (build 702)
OpenJDK 6b20 in server mode
Apache Tomcat 6.0.24 (with default configuration)


Installation
------------
1. Create a PostgreSQL database called chellow.

2. In postgresql.conf set the default_transaction_isolation parameter to 'serializable'. 

3. In your Tomcat, configure a JNDI JDBC datasource called jdbc/chellow.
    a) Copy context.xml from the same directory as this file, and update with your own settings.
    b) Put the JDBC driver from
          http://jdbc.postgresql.org/download/postgresql-8.4-702.jdbc4.jar
          in the Tomcat /lib/ directory.
         
4. Deploy the file chellow.war on your servlet container.


Upgrade From Version 482
------------------------
1. Upgrade your system so that it meets the requirements above.
2. Copy the report at the bottom of this file, and run it with the following parameters to export the user data:

/reports/<report number>/output/

3. Install Chellow afresh with a blank database.
4. Import the user data by going to General Imports section.


from java.math import BigDecimal
from net.sf.chellow.monad import Hiber, UserException, MonadUtils
from net.sf.chellow.monad.types import UriPathElement, MonadDate
from java.util import GregorianCalendar, TimeZone, Locale, Calendar
from net.sf.chellow.physical import HhStartDate, Configuration
from java.text import DateFormat
from java.util.zip import ZipOutputStream, ZipEntry
from java.io import OutputStreamWriter, PrintWriter
from java.security import MessageDigest
from com.Ostermiller.util import Base64
from java.lang import String, System, Boolean

def mpan_fields(mpan):
    if mpan is None:
        return ['', '', '', '', '']
    else:
        return [mpan.getCore(), mpan.getLlfc(), mpan.getAgreedSupplyCapacity(), mpan.getSupplierContract().getName(), mpan.getSupplierAccount()]

#inv.getResponse().setContentType('application/zip')
#inv.getResponse().setHeader('Content-Disposition', 'filename=output.zip;')
#sout = inv.getResponse().getOutputStream()
#zout = ZipOutputStream(sout)
#pw = PrintWriter(OutputStreamWriter(zout, 'UTF-8'))
#zout.putNextEntry(ZipEntry('out.xml'))

inv.getResponse().setContentType('text/xml')
inv.getResponse().setHeader('Content-Disposition', 'attachment; filename=output.xml;')
pw = inv.getResponse().getWriter()

def print_line(values):
    pw.println('    <line>')
    for value in values:
        if value is None:
            value = ''
        else:
            value = str(value)
        pw.println('        <value><' + '![CDATA[' + value + ']]' + '></value>')
    pw.println('    </line>')
    pw.flush()


def print_batches(contract, role_name):
    reads_query = Hiber.session().createQuery("select read.meterSerialNumber, read.mpanStr, read.coefficient, read.units, read.tpr.code, read.previousDate, read.previousValue, read.previousType.code, read.presentDate, read.presentValue, read.presentType.code from RegisterRead read where read.bill = :bill order by read.id")

    range_11 = range(11)

    bills_query = Hiber.session().createQuery("select bill from Bill bill where bill.batch = :batch order by bill.id")

    batches = Hiber.session().createQuery("from Batch batch where batch.contract.id = :contractId order by batch.id").setLong('contractId', contract.getId()).scroll()
    while batches.next():
        batch = batches.get(0)
        print_line(['insert', 'batch', role_name, contract.getName(), batch.getReference(), ''])
        bills = bills_query.setEntity('batch', batch).scroll()
        while bills.next():
            bill = bills.get(0)
            values = ['insert', 'bill', role_name, contract.getName(), batch.getReference(), bill.getSupply().getMpanCores().iterator().next(), MonadDate(bill.getIssueDate()), bill.getStartDate(), bill.getFinishDate(), bill.getNet(), bill.getVat(), BigDecimal(0), bill.getAccount(), bill.getReference(), bill.getType(), bill.getBreakdown(), bill.getKwh()]
            reads = reads_query.setEntity('bill', bill).scroll()
            while reads.next():
                values += [reads.get(i) for i in range_11]
            reads.close()
            print_line(values)
            Hiber.session().clear()
        bills.close()
        Hiber.session().clear()
    batches.close()


if inv.hasParameter('download'):
    has_non_core_contracts = inv.getBoolean('has-non-core-contracts')
    has_reports = inv.getBoolean('has-reports')
    has_supplier_contracts = inv.getBoolean('has-supplier-contracts')
    has_supplier_bills = inv.getBoolean('has-supplier-bills')
    has_hhdc_contracts = inv.getBoolean('has-hhdc-contracts')
    has_mop_contracts = inv.getBoolean('has-mop-contracts')
    has_sites = inv.getBoolean('has-sites')    
    has_supplies = inv.getBoolean('has-supplies')
    has_hh_data = inv.getBoolean('has-hh-data')
    has_users = inv.getBoolean('has-users')
    has_configuration = inv.getBoolean('has-configuration')
    has_channel_snag_ignores = inv.getBoolean('has-channel-snag-ignores')
    has_site_snag_ignores = inv.getBoolean('has-site-snag-ignores')
    
    if not inv.isValid():
        raise UserException()
else:
    has_non_core_contracts = has_reports = has_supplier_contracts = has_supplier_bills = has_hhdc_contracts = has_mop_contracts = has_sites = has_supplies = has_hh_data = has_users = has_configuration = has_channel_snag_ignores = has_site_snag_ignores = True


if has_supplies:
    mpan_core_str = inv.getString('mpan-core')

pw.println('<' + '?xml version="1.0"?>')
pw.flush()
pw.println('<csv>')

if has_reports:
    reports = Hiber.session().createQuery("from Report report where mod(report.id, 2) = 0 order by report.id").scroll()
    while reports.next():
        report = reports.get(0)
        template = report.getTemplate()
        if template is not None:
            template = template.replace("<!" + "[CDATA[", "&" + "lt;![CDATA[").replace("]]" + ">", "]]" + "&" + "gt;")
        print_line(['insert', 'report', str(report.getId()), False, report.getName(), report.getScript().replace("<!" + "[CDATA[", "&" + "lt;![CDATA[").replace("]]" + ">", "]]" + "&" + "gt;"), template])
    Hiber.session().clear()
    reports.close()

if has_non_core_contracts:
    contracts = Hiber.session().createQuery("from NonCoreContract contract where mod(contract.id, 2) = 0 order by contract.name").scroll()
    while contracts.next():
        contract = contracts.get(0)
        contract_name = contract.getName()
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract = :contract order by script.startDate.date").setEntity('contract', contract).list()
        start_rate_script = rate_scripts[0]
        print_line(['insert', 'non-core-contract', contract.getId(), None, contract.getParty().getParticipant().getCode(), contract_name, contract.getChargeScript(), start_rate_script.getId(), start_rate_script.getStartDate(), rate_scripts[len(rate_scripts) -1].getFinishDate(), start_rate_script.getScript()])
        for i in range(1, len(rate_scripts)):
            rate_script = rate_scripts[i]
            print_line(['insert', 'non-core-contract-rate-script', contract_name, rate_script.getId(), rate_script.getStartDate(), rate_script.getScript()])
    Hiber.session().clear()
    contracts.close()


if has_users:
    users = Hiber.session().createQuery("from User user order by user.id").scroll()
    while users.next():
        user = users.get(0)
        print_line(['insert', 'user', user.getEmailAddress(), '', user.getPasswordDigest(), user.getRole().getCode(), '', ''])
    users.close()


if has_configuration:
    print_line(['update', 'configuration', Configuration.getConfiguration().getProperties()])


if has_sites:
    sites = Hiber.session().createQuery("select site.code, site.name from Site site order by site.id").scroll()
    while sites.next():
        print_line(['insert', 'site', sites.get(0), sites.get(1)])
    sites.close()


if has_hhdc_contracts:
    contracts = Hiber.session().createQuery("from HhdcContract contract order by contract.id").scroll()
    while contracts.next():
        contract = contracts.get(0)
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
        start_rate_script = contract.getStartRateScript()
        finish_rate_script = contract.getFinishRateScript()
        print_line(['insert', 'hhdc-contract', contract.getId(), contract.getParty().getParticipant().getCode(), contract.getName(), start_rate_script.getStartDate(), finish_rate_script.getFinishDate(), contract.getChargeScript(), contract.getProperties(), contract.getState(), start_rate_script.getId(), start_rate_script.getScript()])
        if len(rate_scripts) > 1:
            for rate_script in rate_scripts[1:]:
                print_line(['insert', 'hhdc-contract-rate-script', contract.getName(), rate_script.getId(), rate_script.getStartDate(), rate_script.getScript()])
        Hiber.session().clear()
    contracts.close()


if has_mop_contracts:
    contracts = Hiber.session().createQuery("from MopContract contract order by contract.id").scroll()
    while contracts.next():
        contract = contracts.get(0)
        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()
        start_rate_script = rate_scripts[0]
        finish_rate_script = rate_scripts[len(rate_scripts) - 1]
        print_line(['insert', 'mop-contract', contract.getId(), contract.getParty().getParticipant().getCode(), contract.getName(), start_rate_script.getStartDate(),  finish_rate_script.getFinishDate(), contract.getChargeScript(), start_rate_script.getId(), start_rate_script.getScript()])
        if len(rate_scripts) > 1:
            for rate_script in rate_scripts[1:]:
                print_line(['insert', 'mop-contract-rate-script', contract.getName(), rate_script.getId(), rate_script.getStartDate(), rate_script.getScript()])
        Hiber.session().clear()
    contracts.close()


if has_supplier_contracts:
    contracts = Hiber.session().createQuery("from SupplierContract contract order by contract.id").scroll()
    while contracts.next():
        contract = contracts.get(0)
        contract_name = contract.getName()

        rate_scripts = Hiber.session().createQuery("from RateScript script where script.contract.id = :contractId order by script.startDate.date").setLong('contractId', contract.getId()).list()

        start_rate_script = rate_scripts.get(0)
        finish_rate_script = rate_scripts.get(len(rate_scripts) - 1)
        print_line(['insert', 'supplier-contract', contract.getId(), contract.getParty().getParticipant().getCode(), contract_name, start_rate_script.getStartDate(), finish_rate_script.getFinishDate(), contract.getChargeScript(), start_rate_script.getId(), start_rate_script.getScript()])

        for i in range(1, len(rate_scripts)):
            rate_script = rate_scripts[i]
            print_line(['insert', 'supplier-contract-rate-script', rate_script.getContract().getName(), rate_script.getId(), rate_script.getStartDate(), rate_script.getScript()])
            Hiber.session().clear()
        Hiber.session().clear()
    contracts.close()


if has_supplies:
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
        start_date = first_generation.getStartDate().toString()
        finish_date = last_generation.getFinishDate()
        if finish_date is None:
            finish_date = ''
        else:
            finish_date = finish_date.toString()
        source = supply.getSource().getCode()
        generator_type = supply.getGeneratorType()
        if generator_type is None:
            generator_type = ''
        else:
            generator_type = generator_type.getCode()

        mop_contract = first_generation.getMopContract()
        if mop_contract is None:
            mop_contract_name = ''
            mop_account = ''
        else:
            mop_contract_name = mop_contract.getName()
            mop_account = first_generation.getMopAccount()

        hhdc_contract = first_generation.getHhdcContract()
        if hhdc_contract is None:
            hhdc_contract_name = ''
            hhdc_account = ''
        else:
            hhdc_contract_name = hhdc_contract.getName()
            hhdc_account = first_generation.getHhdcAccount()
        values = ['insert', 'supply', site_code, source, generator_type, supply_name, supply.getGspGroup().getCode(), start_date, finish_date, mop_contract_name, mop_account, hhdc_contract_name, hhdc_account]
        for is_import in [True, False]:
            for is_kwh in [True, False]:
                values.append(Boolean(first_generation.getChannel(is_import, is_kwh) != None))

        values += [first_generation.getMeterSerialNumber(), first_generation.getPc(), first_generation.getMtc(), first_generation.getCop().getCode(), first_generation.getSsc()] + mpan_fields(first_generation.getImportMpan()) + mpan_fields(first_generation.getExportMpan())
        first_mpan_core_str = str(first_generation.getMpans().iterator().next().getCore())
        print_line(values)
        generations = Hiber.session().createQuery("from SupplyGeneration generation where generation.supply = :supply order by generation.startDate.date").setEntity('supply', supply).scroll()
        generations.next()
        while generations.next():
            generation = generations.get(0)
            physical_site = Hiber.session().createQuery("select siteSupplyGeneration.site from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.isPhysical is true").setEntity('supplyGeneration', last_generation).uniqueResult()
            site_code = physical_site.getCode()
            start_date = generation.getStartDate()

            mop_contract = generation.getMopContract()
            if mop_contract is None:
                mop_contract_name = ''
                mop_account = ''
            else:
                mop_contract_name = mop_contract.getName()
                mop_account = generation.getMopAccount()

            hhdc_contract = generation.getHhdcContract()
            if hhdc_contract is None:
                hhdc_contract_name = ''
                hhdc_account = ''
            else:
                hhdc_contract_name = hhdc_contract.getName()
                hhdc_account = generation.getHhdcAccount()
            values = ['insert', 'supply-generation', first_mpan_core_str, start_date, site_code, mop_contract_name, mop_account, hhdc_contract_name, hhdc_account]
            for is_import in [True, False]:
                for is_kwh in [True, False]:
                    values.append(Boolean(generation.getChannel(is_import, is_kwh) != None))

            values += [generation.getMeterSerialNumber(), generation.getPc(), generation.getMtc(), generation.getCop().getCode(), generation.getSsc()] + mpan_fields(generation.getImportMpan()) + mpan_fields(generation.getExportMpan())
            print_line(values)
        generations.beforeFirst()
        while generations.next():
            generation = generations.get(0)
            start_date = generation.getStartDate()
            finish_date = generation.getFinishDate()
            site_supply_generations = Hiber.session().createQuery("from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.supplyGeneration = :supplyGeneration and siteSupplyGeneration.isPhysical is false").setEntity('supplyGeneration', generation).scroll()
            while site_supply_generations.next():
                site_supply_generation = site_supply_generations.get(0)
                print_line(['insert', 'site-supply-generation', site_supply_generation.getSite().getCode(), first_mpan_core_str, start_date, 'false'])
            site_supply_generations.close()
            query = "select datum.startDate, datum.value, datum.status from HhDatum datum where datum.channel.supplyGeneration.supply = :supply and datum.channel.isImport = :isImport and datum.channel.isKwh = :isKwh and datum.startDate.date >= :startDate"
            if finish_date is None:
                hh_data_q = Hiber.session().createQuery(query + " order by datum.startDate.date").setTimestamp('startDate', start_date.getDate())
            else:
                hh_data_q = Hiber.session().createQuery(query + " and datum.startDate.date <= :finishDate  order by datum.startDate.date").setTimestamp('finishDate', finish_date.getDate())
            hh_data_q.setTimestamp('startDate', start_date.getDate()).setEntity('supply', supply)
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
                            for value in ['insert', 'hh-datum', first_mpan_core_str, str(end_date), is_import, is_kwh]:
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


if has_channel_snag_ignores:
    timing = System.currentTimeMillis()
    #pw.println('about to start ' + str(System.currentTimeMillis() - timing))
    snags = Hiber.session().createQuery("from ChannelSnag snag where snag.isIgnored is true").scroll()
    #pw.println('finished ' + str(System.currentTimeMillis() - timing))
    while snags.next():
        snag = snags.get(0)
        channel = snag.getChannel()
        print_line(['insert', 'channel-snag-ignore', channel.getSupplyGeneration().getMpans().iterator().next().getCore().toString(), Boolean(channel.getIsImport()), Boolean(channel.getIsKwh()), snag.getDescription(), snag.getStartDate(), snag.getFinishDate()])
        Hiber.session().clear()
    snags.close()


if has_site_snag_ignores:
    snags = Hiber.session().createQuery("from SiteSnag snag where snag.isIgnored is true").scroll()
    while snags.next():
        snag = snags.get(0)
        print_line(['insert', 'site-snag-ignore', snag.getSite().getCode(), snag.getDescription(), snag.getStartDate(), snag.getFinishDate()])
        Hiber.session().clear()
    snags.close()

if has_hhdc_contracts:
    contracts = Hiber.session().createQuery("from HhdcContract contract order by contract.id").scroll()
    while contracts.next():
        print_batches(contracts.get(0), 'hhdc')
        Hiber.session().clear()
    contracts.close()


if has_mop_contracts:
    contracts = Hiber.session().createQuery("from MopContract contract order by contract.id").scroll()
    while contracts.next():
        print_batches(contracts.get(0), 'mop')
        Hiber.session().clear()
    contracts.close()


if has_supplier_bills:
    contracts = Hiber.session().createQuery("from SupplierContract contract order by contract.id").scroll()
    while contracts.next():
        print_batches(contracts.get(0), 'supplier')
        Hiber.session().clear()
    contracts.close()


pw.println('</csv>')
pw.flush()
pw.close()