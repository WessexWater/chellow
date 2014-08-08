from net.sf.chellow.monad import Monad
import datetime
import os
import sys
import traceback
import threading
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'utils', 'computer')

Site, Era, Bill = db.Site, db.Era, db.Bill
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
totalseconds = utils.totalseconds

caches = {}

year = inv.getInteger("finish_year")
month = inv.getInteger("finish_month")
months = inv.getInteger("months")

if inv.hasParameter('site_id'):
    st_id = inv.getLong('site_id')
else:
    st_id = None
    
finish_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc) + relativedelta(months=1) - HH
start_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc) - relativedelta(months=months-1)

def process_site(sess, site, month_start, month_finish, forecast_date, tmp_file):
    site_code = site.code
    associates = []
    sources = []
    generator_types = []
    metering_type = 'no-supply'
    problem = ''
    month_data = {}

    for stream_name in ['import-net', 'export-net', 'import-gen', 'export-gen', 'import-3rd-party', 'export-3rd-party', 'msp', 'used', 'used-3rd-party']:
        month_data[stream_name + '-kwh'] = 0
        month_data[stream_name + '-gbp'] = 0

    has_3rd_party = False
    third_party_contracts = {}
    
    billed_gbp = 0
    billed_kwh = 0

    for group in site.groups(sess, month_start, month_finish, False):
        for cand_site in group.sites:
            cand_site_code = cand_site.code
            if cand_site_code != site_code and cand_site_code not in associates:
                associates.append(cand_site_code)
        for cand_supply in group.supplies:
            for cand_era in cand_supply.find_eras(sess, month_start, month_finish):
                if cand_era.imp_mpan_core is not None and metering_type != 'hh':
                    if cand_era.pc.code == '00':
                        metering_type = 'hh'
                    elif metering_type != 'amr':
                        if len(cand_era.channels) > 0:
                            metering_type = 'amr'
                        elif metering_type != 'nhh':
                            if cand_era.mtc.meter_type.code not in ['UM', 'PH']:
                                metering_type = 'nhh'
                            else:
                                metering_type = 'unmetered'

    for group in site.groups(sess, month_start, month_finish, True):
        if group.start_date > start_date:
            chunk_start = group.start_date
        else:
            chunk_start = start_date

        if group.finish_date > finish_date:
            chunk_finish = finish_date
        else:
            chunk_finish = group.finish_date

        for supply in group.supplies:
            source_code = supply.source.code
            if source_code not in sources:
                sources.append(source_code)

            if supply.generator_type is not None:
                gen_type = supply.generator_type.code
                if gen_type not in generator_types:
                    generator_types.append(gen_type)

            for era in sess.query(Era).filter(Era.supply_id==supply.id, Era.start_date<=chunk_finish, or_(Era.finish_date==None, Era.finish_date>=chunk_start)):
                tmp_file.write(' ')

                imp_mpan_core = era.imp_mpan_core

                # GBP
                if imp_mpan_core is None:
                    continue

                if era.start_date > chunk_start:
                    bill_start = era.start_date
                else:
                    bill_start = chunk_start
                if hh_after(era.finish_date, chunk_finish):
                    bill_finish = chunk_finish
                else:
                    bill_finish = era.finish_date

                supplier_contract = era.imp_supplier_contract
                if source_code in ('net', 'gen-net', '3rd-party', '3rd-party-reverse'):
                    #tmp_file.write("starting vbill, " + str(System.currentTimeMillis()))
                    supply_source = computer.SupplySource(sess, bill_start, bill_finish, forecast_date, era, True, tmp_file, caches)
                    if supply_source.measurement_type not in ['hh', 'amr']:
                        kwh = sum(hh['msp-kwh'] for hh in supply_source.hh_data)
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-kwh'] += kwh
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-kwh'] += kwh

                    #tmp_file.write("finished init from mpan, " + str(System.currentTimeMillis()))
                    import_vb_function = computer.contract_func(caches, supplier_contract, 'virtual_bill', tmp_file)
                    if import_vb_function is None:
                        problem += "Can't find the virtual_bill function in the supplier contract. "
                    else:
                        import_vb_function(supply_source)
                        v_bill = supply_source.supplier_bill
                        #tmp_file.write("finishing vbill, " + str(System.currentTimeMillis()))
                        
                        if 'problem' in v_bill and len(v_bill['problem']) > 0:
                            problem += 'Supplier Problem: ' + v_bill['problem']

                        try:
                            gbp = v_bill['net-gbp']
                        except KeyError:
                            problem += 'For the supply ' + import_mpan.toString() + ' the virtual bill ' + str(v_bill) + ' from the contract ' + supplier_contract.getName() + ' does not contain the net-gbp key.'
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp

                    dc_contract = era.hhdc_contract
                    if dc_contract is not None:
                        dc_bill = supply_source.contract_func(dc_contract, 'virtual_bill')(supply_source)
                        gbp = dc_bill['net-gbp']
                        if 'problem' in dc_bill and len(dc_bill['problem']) > 0:
                            problem += 'DC Problem: ' + dc_bill['problem']
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp

                    mop_contract = era.mop_contract
                    if mop_contract is not None:
                        mop_bill_function = supply_source.contract_func(mop_contract, 'virtual_bill')
                        if mop_bill_function is not None:
                            mop_bill = mop_bill_function(supply_source)
                            gbp = mop_bill['net-gbp']
                            if 'problem' in mop_bill and len(mop_bill['problem']) > 0:
                                problem += 'MOP Problem: ' + mop_bill['problem']
                            if source_code in ('net', 'gen-net'):
                                month_data['import-net-gbp'] += gbp
                            elif source_code in ('3rd-party', '3rd-party-reverse'):
                                month_data['import-3rd-party-gbp'] += gbp

            for bill in sess.query(Bill).filter(Bill.supply_id==supply.id, Bill.start_date<=chunk_finish, Bill.finish_date>=chunk_start):
                bill_start = bill.start_date
                bill_finish = bill.finish_date
                bill_duration = totalseconds(bill_finish - bill_start) + (30 * 60)
                overlap_duration = totalseconds(min(bill_finish, chunk_finish)  - max(bill_start, chunk_start)) + (30 * 60)
                overlap_proportion = float(overlap_duration) / bill_duration
                billed_gbp += overlap_proportion * float(bill.net)
                billed_kwh += overlap_proportion * float(bill.kwh)

        #tmp_file.println("getting site ds, " + str(System.currentTimeMillis()))

        displaced_era = computer.displaced_era(sess, group, chunk_start, chunk_finish)
        site_ds = computer.SiteSource(sess, site, chunk_start, chunk_finish, forecast_date, tmp_file, caches, displaced_era)
        if displaced_era != None:
            #tmp_file.println("starting displaced, " + str(System.currentTimeMillis()))
            month_data['msp-gbp'] += computer.contract_func(caches, displaced_era.imp_supplier_contract, 'displaced_virtual_bill', tmp_file)(site_ds)['net-gbp']

            #tmp_file.println("finishing displaced, " + str(System.currentTimeMillis()))

        #tmp_file.println("finishing site ds " + str(System.currentTimeMillis()))

        for stream_name in ('import-3rd-party', 'export-3rd-party', 'import-net', 'export-net', 'import-gen', 'export-gen', 'msp'):
            name = stream_name + '-kwh'
            month_data[name] += sum(hh[name] for hh in site_ds.hh_data)

        month_data['used-3rd-party-kwh'] = month_data['import-3rd-party-kwh'] - month_data['export-3rd-party-kwh']
        month_data['used-3rd-party-gbp'] = month_data['import-3rd-party-gbp']
        month_data['used-gbp'] += month_data['import-net-gbp'] + month_data['msp-gbp'] + month_data['used-3rd-party-gbp']

        month_data['used-kwh'] += month_data['msp-kwh'] + month_data['used-3rd-party-kwh'] + month_data['import-net-kwh']

    sources.sort()
    generator_types.sort()

    result = [site.code, site.name, ','.join(associates), ','.join(sources), '.'.join(generator_types), hh_format(month_finish), month_data['import-net-kwh'], month_data['msp-kwh'], month_data['export-net-kwh'], month_data['used-kwh'], month_data['export-gen-kwh'], month_data['import-gen-kwh'], month_data['import-3rd-party-kwh'], month_data['export-3rd-party-kwh'], month_data['import-net-gbp'], month_data['msp-gbp'], 0, month_data['used-gbp'], month_data['used-3rd-party-gbp'], billed_kwh, billed_gbp, metering_type, problem]
    #tmp_file.println("Finished call method " + str(System.currentTimeMillis()))
    #count = Hiber.session().createQuery("select count(*) from hh_datum").uniqueResult()
    #tmp_file.println("Rows " + str(count))
    return result

def long_process():
    now = datetime.datetime.now(pytz.utc)
    
    sess = None
    try:
        sess = db.session()
        if st_id is None:
            st = None
            base_name = "site_monthly_duration_for_all_site_for_" + str(months) + "_to_" + str(year) + "_" + str(month) + ".csv"
        else:
            st = Site.get_by_id(sess, st_id)
            base_name = "site_monthly_duration_for_" + st.code + "_" + str(months) + "_to_" + str(year) + "_" + str(month) + ".csv"
        running_name = "RUNNING_" + base_name
        finished_name = "FINISHED_" + base_name

        download_path = Monad.getContext().getRealPath("/downloads")
        os.chdir(download_path)
        tmp_file = open(running_name, "w")

        forecast_date = computer.forecast_date()

        tmp_file.write("Site Id,Site Name,Associated Site Ids,Sources,Generator Types,Month,Metered Imported kWh,Metered Displaced kWh,Metered Exported kWh,Metered Used kWh,Metered Parasitic kWh,Metered Generated kWh,Metered 3rd Party Import kWh,Metered 3rd Party Export kWh,Metered Imported GBP,Metered Displaced GBP,Metered Exported GBP,Metered Used GBP,Metered 3rd Party Import GBP,Billed Imported kWh,Billed Imported GBP,Metering Type,Problem")

        for i in range(months):
            sites = sess.query(Site).order_by(Site.code)
            if st is not None:
                sites = sites.filter(Site.id==st.id)
            for site in sites:
                #tmp_file.write("starting site, " + str(System.currentTimeMillis()))
                #tmp_file.write("starting site, " + str(System.currentTimeMillis()))

                month_start = start_date + relativedelta(months=i)
                month_finish = month_start + relativedelta(months=1) - HH
                #tq = process_site(sess, site, month_start, month_finish, forecast_date,  tmp_file)
                #tmp_file.write('printing, ' + str(System.currentTimeMillis()) + ',' + ','.join('"' + str(value) + '"' for value in tq))
                tmp_file.write('\r\n' + ','.join('"' + str(value) + '"' for value in process_site(sess, site, month_start, month_finish, forecast_date, tmp_file)))
                #tmp_file.write("finishing site, " + str(System.currentTimeMillis()))
                tmp_file.flush()

    except:
        tmp_file.write("Problem " + traceback.format_exc())
    finally:
        try:
            if sess is not None:
                sess.close()
        except:
            tmp_file.write("\nProblem closing session.")
        finally:
            tmp_file.close()
            os.rename(running_name, finished_name)

        
threading.Thread(target=long_process).start()
inv.sendSeeOther("/reports/251/output/")