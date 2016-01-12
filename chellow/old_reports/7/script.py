from net.sf.chellow.monad import Monad
from dateutil.relativedelta import relativedelta
import collections
from sqlalchemy.sql.expression import true, false
from datetime import datetime
import utils
import db
import templater
from itertools import chain
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')


UserException = utils.UserException
Supply, Era, Site, SiteEra = db.Supply, db.Era, db.Site, db.SiteEra
Channel, Bill, Contract, Tpr = db.Channel, db.Bill, db.Contract, db.Tpr
MeasurementRequirement, Report = db.MeasurementRequirement, db.Report
RegisterRead = db.RegisterRead
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
rate_scripts = None
debug = ''
try:
    sess = db.session()
    era_bundles = []
    supply_id = inv.getLong('supply_id')
    if supply_id is None:
        supply_id = inv.getLong('supply-id')
    supply = Supply.get_by_id(sess, supply_id)
    eras = sess.query(Era).filter(Era.supply == supply).order_by(
        Era.start_date.desc()).all()
    for era in eras:
        imp_mpan_core = era.imp_mpan_core
        exp_mpan_core = era.exp_mpan_core
        physical_site = sess.query(Site).join(SiteEra).filter(
            SiteEra.is_physical == true(), SiteEra.era_id == era.id).one()
        other_sites = sess.query(Site).join(SiteEra).filter(
            SiteEra.is_physical != true(), SiteEra.era == era).all()
        imp_channels = sess.query(Channel).filter(
            Channel.era == era, Channel.imp_related == true()).order_by(
            Channel.channel_type).all()
        exp_channels = sess.query(Channel).filter(
            Channel.era == era, Channel.imp_related == false()).order_by(
            Channel.channel_type).all()
        era_bundle = {
            'era': era, 'physical_site': physical_site,
            'other_sites': other_sites, 'imp_channels': imp_channels,
            'exp_channels': exp_channels, 'imp_bills': {'bill_dicts': []},
            'exp_bills': {'bill_dicts': []},
            'hhdc_bills': {'bill_dicts': []}, 'mop_bills': {'bill_dicts': []}}
        era_bundles.append(era_bundle)

        if imp_mpan_core is not None:
            era_bundle['imp_shared_supplier_accounts'] = \
                sess.query(Supply).distinct().join(Era).filter(
                    Supply.id != supply.id,
                    Era.imp_supplier_account == era.imp_supplier_account,
                    Era.imp_supplier_contract == era.imp_supplier_contract) \
                .all()
        if exp_mpan_core is not None:
            era_bundle['exp_shared_supplier_accounts'] = \
                sess.query(Supply).join(Era).filter(
                    Era.supply != supply,
                    Era.exp_supplier_account == era.exp_supplier_account,
                    Era.exp_supplier_contract == era.exp_supplier_contract) \
                .all()
        if era.pc.code != '00':
            inner_headers = [
                tpr for tpr in sess.query(Tpr).join(MeasurementRequirement)
                .filter(
                    MeasurementRequirement.ssc == era.ssc).order_by(Tpr.code)]
            if era.pc.code in ['05', '06', '07', '08']:
                inner_headers.append(None)
            era_bundle['imp_bills']['inner_headers'] = inner_headers
            inner_header_codes = [
                tpr.code if tpr is not None else 'md' for tpr in inner_headers]

        bills = sess.query(Bill).filter(Bill.supply == supply).order_by(
            Bill.start_date.desc(), Bill.issue_date.desc(),
            Bill.reference.desc())
        if era.finish_date is not None:
            bills = bills.filter(Bill.start_date <= era.finish_date)
        if era != eras[-1]:
            bills = bills.filter(Bill.start_date >= era.start_date)

        num_outer_cols = 0
        for bill in bills:
            bill_contract = bill.batch.contract
            bill_role_code = bill_contract.party.market_role.code
            if bill_role_code == 'X':
                if exp_mpan_core is not None and \
                        bill_contract == era.exp_supplier_contract:
                    bill_group_name = 'exp_bills'
                else:
                    bill_group_name = 'imp_bills'

            elif bill_role_code == 'C':
                bill_group_name = 'hhdc_bills'
            elif bill_role_code == 'M':
                bill_group_name = 'mop_bills'
            else:
                raise UserException("""bill group name not found for
                    bill_contract_id """ + str(bill_contract.id))

            bill_group = era_bundle[bill_group_name]
            rows_high = 1
            bill_dict = {'bill': bill}
            bill_group['bill_dicts'].append(bill_dict)

            if bill_group_name == 'imp_bills' and era.pc.code != '00':
                inner_tpr_map = dict((code, []) for code in inner_header_codes)
                outer_tpr_map = collections.defaultdict(list)

                for read, tpr in sess.query(
                        RegisterRead, Tpr).join(Tpr).filter(
                        RegisterRead.bill == bill).order_by(
                        Tpr.id, RegisterRead.present_date.desc()):
                    tpr_code = 'md' if tpr is None else tpr.code
                    try:
                        inner_tpr_map[tpr_code].append(read)
                    except KeyError:
                        outer_tpr_map[tpr_code].append(read)

                rows_high = max(
                    chain(
                        map(
                            len, chain(
                                inner_tpr_map.values(),
                                outer_tpr_map.values())),
                        [rows_high]))

                read_rows = []
                bill_dict['read_rows'] = read_rows

                for i in range(rows_high):
                    inner_reads = []
                    row_dict = {'inner_reads': inner_reads, 'outer_reads': []}
                    read_rows.append(row_dict)
                    for tpr_code in inner_header_codes:
                        try:
                            inner_reads.append(inner_tpr_map[tpr_code][i])
                        except IndexError:
                            row_dict['inner_reads'].append(None)

                    for tpr_code, read_list in outer_tpr_map.items():
                        try:
                            row_dict['outer_reads'].append(read_list[i])
                        except IndexError:
                            row_dict['outer_reads'].append(None)

                num_outer_cols = max(num_outer_cols, len(outer_tpr_map))

                bill_dict['rows_high'] = rows_high

        era_bundle['imp_bills']['num_outer_cols'] = num_outer_cols
        era_bundle['exp_bills']['num_outer_cols'] = 0

        for bill_group_name in (
                'imp_bills', 'exp_bills', 'hhdc_bills', 'mop_bills'):
            b_dicts = list(reversed(era_bundle[bill_group_name]['bill_dicts']))
            for i, b_dict in enumerate(b_dicts):
                if i < (len(b_dicts) - 1):
                    bill = b_dict['bill']
                    next_b_dict = b_dicts[i+1]
                    next_bill = next_b_dict['bill']
                    if (
                            bill.start_date, bill.finish_date, bill.kwh,
                            bill.net) == (
                            next_bill.start_date, next_bill.finish_date,
                            -1 * next_bill.kwh, -1 * next_bill.net) and \
                            'collapsible' not in b_dict:
                        b_dict['collapsible'] = True
                        next_b_dict['first_collapsible'] = True
                        next_b_dict['collapsible'] = True
                        b_dict['collapse_id'] = next_b_dict['collapse_id'] = \
                            bill.id

    RELATIVE_YEAR = relativedelta(years=1)

    now = datetime.utcnow()
    triad_year = (now - RELATIVE_YEAR).year if now.month < 3 else now.year
    this_month_start = datetime(now.year, now.month, 1)
    last_month_start = this_month_start - relativedelta(months=1)
    last_month_finish = this_month_start - relativedelta(minutes=30)

    batch_reports = []
    config_contract = Contract.get_non_core_by_name(sess, 'configuration')
    properties = config_contract.make_properties()
    if 'supply_reports' in properties:
        for report_id in properties['supply_reports']:
            batch_reports.append(Report.get_by_id(sess, report_id))

    truncated_note = None
    is_truncated = False
    note = None
    if len(supply.note.strip()) == 0:
        note_str = "{'notes': []}"
    else:
        note_str = supply.note

    supply_note = eval(note_str)
    notes = supply_note['notes']
    if len(notes) > 0:
        note = notes[0]
        lines = note['body'].splitlines()
        if len(lines) > 0:
            trunc_line = lines[0][:50]
            if len(lines) > 1 or len(lines[0]) > len(trunc_line):
                is_truncated = True
                truncated_note = trunc_line

    templater.render(
        inv, template, {
            'triad_year': triad_year, 'now': now,
            'last_month_start': last_month_start,
            'last_month_finish': last_month_finish,
            'era_bundles': era_bundles, 'supply': supply,
            'system_properties': properties, 'is_truncated': is_truncated,
            'truncated_note': truncated_note, 'note': note,
            'this_month_start': this_month_start,
            'batch_reports': batch_reports, 'debug': debug})

except UserException as e:
    sess.rollback()
    render(inv, template, {'messages': [str(e)]})
finally:
    if sess is not None:
        sess.close()
