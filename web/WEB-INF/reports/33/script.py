import traceback
from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.sql import func
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

Era, Supply, Bill, Batch = db.Era, db.Supply, db.Bill, db.Batch
Channel, HhDatum, RegisterRead = db.Channel, db.HhDatum, db.RegisterRead
ReadType = db.ReadType
MeasurementRequirement = db.MeasurementRequirement
HH, hh_format, form_int = utils.HH, utils.hh_format, utils.form_int
inv = globals()['inv']

year = form_int(inv, 'year')
month = form_int(inv, 'month')
if inv.hasParameter('supply_id'):
    supply_id = form_int(inv, 'supply_id')
else:
    supply_id = None


def content():
    sess = None
    try:
        sess = db.session()

        date = datetime.datetime(year, month, 1) + relativedelta(months=1) - HH

        yield """Date,Physical Site Id, Physical Site Name, Other Site Ids,
            Other Site Names, Supply Id, Source, Generator Type, DNO Name,
            Voltage Level, Metering Type, Mandatory HH, PC, MTC, CoP, SSC,
            Number Of Registers, MOP Contract, Mop Account, HHDC Contract,
            HHDC Account, Meter Serial Number, Meter Installation Date,
            Latest Normal Meter Read Date,Latest Normal Meter Read Type,
            Latest DC Bill Date, Latest MOP Bill Date,Import ACTIVE?,
            Import REACTIVE_IMPORT?, Import REACTIVE_EXPORT?, Export ACTIVE?,
            Export REACTIVE_IMPORT?, Export REACTIVE_EXPORT?, Import MPAN core,
            Import Agreed Supply Capacity (kVA), Import LLFC Code,
            Import LLFC Description, Import Supplier Contract,
            Import Supplier Account, Import Mandatory kWh,
            Latest Import Supplier Bill Date, Export MPAN core,
            Export Agreed Supply Capacity (kVA), Export LLFC Code,
            Export LLFC Description, Export Supplier Contract,
            Export Supplier Account, Export Mandatory kWh,
            Latest Export Supplier Bill Date\n"""

        NORMAL_READ_TYPES = ('N', 'C', 'N3')
        year_start = date + HH - relativedelta(years=1)

        eras = sess.query(Era).filter(
            Era.start_date < date,
            or_(Era.finish_date == null(), Era.finish_date >= date)).order_by(
            Era.supply_id)

        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)

            eras = eras.filter(Era.supply_id == supply.id)

        for era in eras:
            site_codes = ''
            site_names = ''
            for site_era in era.site_eras:
                if site_era.is_physical:
                    physical_site = site_era.site
                else:
                    site = site_era.site
                    site_codes = site_codes + site.code + ', '
                    site_names = site_names + site.name + ', '
            site_codes = site_codes[:-2]
            site_names = site_names[:-2]
            supply = era.supply
            if era.imp_mpan_core is None:
                voltage_level_code = era.exp_llfc.voltage_level.code
            else:
                voltage_level_code = era.imp_llfc.voltage_level.code

            if supply.generator_type is None:
                generator_type = ''
            else:
                generator_type = supply.generator_type.code

            metering_type = era.make_meter_category()

            if metering_type == 'nhh':
                latest_prev_normal_read = sess.query(RegisterRead). \
                    join(Bill).join(RegisterRead.previous_type).filter(
                        ReadType.code.in_(NORMAL_READ_TYPES),
                        RegisterRead.previous_date <= date,
                        Bill.supply_id == supply.id).order_by(
                        RegisterRead.previous_date.desc()).first()

                latest_pres_normal_read = sess.query(RegisterRead) \
                    .join(Bill).join(RegisterRead.present_type).filter(
                        ReadType.code.in_(NORMAL_READ_TYPES),
                        RegisterRead.present_date <= date,
                        Bill.supply == supply).order_by(
                        RegisterRead.present_date.desc()).first()

                if latest_prev_normal_read is None and \
                        latest_pres_normal_read is None:
                    latest_normal_read_date = None
                    latest_normal_read_type = None
                elif latest_pres_normal_read is not None and \
                        latest_prev_normal_read is None:
                    latest_normal_read_date = \
                        latest_pres_normal_read.present_date
                    latest_normal_read_type = \
                        latest_pres_normal_read.present_type.code
                elif latest_pres_normal_read is None and \
                        latest_prev_normal_read is not None:
                    latest_normal_read_date = \
                        latest_prev_normal_read.previous_date
                    latest_normal_read_type = \
                        latest_prev_normal_read.previous_type.code
                elif latest_pres_normal_read.present_date > \
                        latest_prev_normal_read.previous_date:
                    latest_normal_read_date = \
                        latest_pres_normal_read.present_date
                    latest_normal_read_type = \
                        latest_pres_normal_read.present_type.code
                else:
                    latest_normal_read_date = \
                        latest_prev_normal_read.previous_date
                    latest_normal_read_type = \
                        latest_prev_normal_read.previous_type.code
                if latest_normal_read_date is not None:
                    latest_normal_read_date = \
                        hh_format(latest_normal_read_date)

            else:
                latest_normal_read_date = metering_type
                latest_normal_read_type = None

            mop_contract = era.mop_contract
            if mop_contract is None:
                mop_contract_name = ''
                mop_account = ''
                latest_mop_bill_date = 'No MOP'
            else:
                mop_contract_name = mop_contract.name
                mop_account = era.mop_account
                latest_mop_bill_date = sess.query(Bill.finish_date) \
                    .join(Batch).filter(
                        Bill.start_date <= date, Bill.supply == supply,
                        Batch.contract == mop_contract).order_by(
                        Bill.finish_date.desc()).first()

                if latest_mop_bill_date is not None:
                    latest_mop_bill_date = hh_format(latest_mop_bill_date[0])

            hhdc_contract = era.hhdc_contract
            if hhdc_contract is None:
                hhdc_contract_name = ''
                hhdc_account = ''
                latest_hhdc_bill_date = 'No HHDC'
            else:
                hhdc_contract_name = hhdc_contract.name
                hhdc_account = era.hhdc_account
                latest_hhdc_bill_date = sess.query(Bill.finish_date) \
                    .join(Batch).filter(
                        Bill.start_date <= date, Bill.supply == supply,
                        Batch.contract == hhdc_contract).order_by(
                        Bill.finish_date.desc()).first()

                if latest_hhdc_bill_date is not None:
                    latest_hhdc_bill_date = hh_format(latest_hhdc_bill_date[0])

            channel_values = []
            for imp_related in [True, False]:
                for channel_type in utils.CHANNEL_TYPES:
                    if era.find_channel(
                            sess, imp_related, channel_type) is None:
                        channel_values.append('false')
                    else:
                        channel_values.append('true')

            imp_avg_months = None
            exp_avg_months = None
            for is_import in [True, False]:
                if is_import and era.imp_mpan_core is None:
                    continue
                if not is_import and era.exp_mpan_core is None:
                    continue

                if metering_type == 'nhh':
                    continue

                month_mds = tuple(
                    md[0] for md in sess.execute("""

    select max(hh_datum.value) as md
    from hh_datum join channel on (hh_datum.channel_id = channel.id)
        join era on (channel.era_id = era.id)
    where era.supply_id = :supply_id and hh_datum.start_date >= :year_start
        and hh_datum.start_date <= :year_finish
        and channel.channel_type = 'ACTIVE'
        and channel.imp_related = :is_import
    group by extract(month from (hh_datum.start_date at time zone 'utc'))
    order by md desc
    limit 3

    """, params={
                    'supply_id': supply.id, 'year_start': year_start,
                    'year_finish': date,
                    'is_import': is_import}))

                avg_months = sum(month_mds)
                if len(month_mds) > 0:
                    avg_months /= len(month_mds)
                    if is_import:
                        imp_avg_months = avg_months
                    else:
                        exp_avg_months = avg_months

            if imp_avg_months > 100 or exp_avg_months > 100:
                mandatory_hh = 'yes'
            else:
                mandatory_hh = 'no'

            imp_latest_supplier_bill_date = None
            exp_latest_supplier_bill_date = None
            for is_import in [True, False]:
                if is_import:
                    if era.imp_mpan_core is None:
                        continue
                    else:
                        supplier_contract = era.imp_supplier_contract
                if not is_import:
                    if era.exp_mpan_core is None:
                        continue
                    else:
                        supplier_contract = era.exp_supplier_contract

                if metering_type == 'hh':
                    latest_supplier_bill_date = sess.query(Bill.finish_date) \
                        .join(Batch).filter(
                            Bill.start_date <= date, Bill.supply == supply,
                            Batch.contract == supplier_contract).order_by(
                            Bill.finish_date.desc()).first()
                    if latest_supplier_bill_date is not None:
                        latest_supplier_bill_date = \
                            latest_supplier_bill_date[0]
                else:
                    latest_prev_read = sess.query(RegisterRead) \
                        .join(Bill).filter(
                            RegisterRead.previous_date <= date,
                            Bill.supply == supply).order_by(
                            RegisterRead.previous_date.desc()).first()

                    latest_pres_read = sess.query(RegisterRead).join(Bill) \
                        .filter(
                            RegisterRead.present_date <= date,
                            Bill.supply == supply).order_by(
                            RegisterRead.present_date.desc()).first()

                    if latest_prev_read is None and latest_pres_read is None:
                        latest_read = None
                    elif latest_pres_read is not None and \
                            latest_prev_read is None:
                        latest_read = latest_pres_read
                    elif latest_pres_read is None and \
                            latest_prev_read is not None:
                        latest_read = latest_prev_read
                    elif latest_pres_read.present_date > \
                            latest_prev_read.previous_date:
                        latest_read = latest_pres_read
                    else:
                        latest_read = latest_prev_read

                    if latest_read is None:
                        latest_supplier_bill_date = None
                    else:
                        latest_supplier_bill_date = \
                            latest_read.bill.finish_date

                if latest_supplier_bill_date is not None:
                    latest_supplier_bill_date = hh_format(
                        latest_supplier_bill_date)

                    if is_import:
                        imp_latest_supplier_bill_date = \
                            latest_supplier_bill_date
                    else:
                        exp_latest_supplier_bill_date = \
                            latest_supplier_bill_date

            meter_installation_date = sess.query(func.min(Era.start_date)) \
                .filter(
                    Era.supply_id == era.supply_id,
                    Era.msn == era.msn).one()[0]

            if era.ssc is None:
                ssc_code = num_registers = None
            else:
                ssc_code = era.ssc.code
                num_registers = sess.query(MeasurementRequirement).filter(
                    MeasurementRequirement.ssc == era.ssc).count()

            yield ','.join(
                ('"' + ('' if value is None else str(value)) + '"')
                for value in [
                    hh_format(date), physical_site.code, physical_site.name,
                    site_codes, site_names, supply.id, supply.source.code,
                    generator_type, supply.dno_contract.name,
                    voltage_level_code, metering_type, mandatory_hh,
                    era.pc.code, era.mtc.code, era.cop.code, ssc_code,
                    num_registers, mop_contract_name, mop_account,
                    hhdc_contract_name, hhdc_account, era.msn,
                    hh_format(meter_installation_date),
                    latest_normal_read_date, latest_normal_read_type,
                    latest_hhdc_bill_date,
                    latest_mop_bill_date] + channel_values + [
                    era.imp_mpan_core, era.imp_sc,
                    None if era.imp_llfc is None else era.imp_llfc.code,
                    None if era.imp_llfc is None else era.imp_llfc.description,
                    None if era.imp_supplier_contract is None else
                    era.imp_supplier_contract.name,
                    era.imp_supplier_account, imp_avg_months,
                    imp_latest_supplier_bill_date] + [
                    era.exp_mpan_core, era.exp_sc,
                    None if era.exp_llfc is None else era.exp_llfc.code,
                    None if era.exp_llfc is None else era.exp_llfc.description,
                    None if era.exp_supplier_contract is None else
                    era.exp_supplier_contract.name,
                    era.exp_supplier_account, exp_avg_months,
                    exp_latest_supplier_bill_date]) + '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name="supplies_snapshot.csv")
