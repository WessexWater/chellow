from collections import defaultdict
from itertools import chain

from chellow.models import (
    Batch, Bill, Channel, Contract, Era, MeasurementRequirement, Party,
    RegisterRead, Site, SiteEra, Supply, Tpr
)

from sqlalchemy import (
    false, true
)
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest


def get_era_bundles(sess, supply):
    era_bundles = []
    eras = sess.query(Era).filter(Era.supply == supply).order_by(
        Era.start_date.desc()).options(
            joinedload(Era.pc), joinedload(Era.imp_supplier_contract),
            joinedload(Era.exp_supplier_contract),
            joinedload(Era.ssc), joinedload(Era.mtc),
            joinedload(Era.mop_contract), joinedload(Era.dc_contract),
            joinedload(Era.imp_llfc), joinedload(Era.exp_llfc),
            joinedload(Era.supply).joinedload(Supply.dno)).all()
    for era in eras:
        imp_mpan_core = era.imp_mpan_core
        exp_mpan_core = era.exp_mpan_core
        physical_site = sess.query(Site).join(SiteEra).filter(
            SiteEra.is_physical == true(), SiteEra.era == era).one()
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
            'dc_bills': {'bill_dicts': []}, 'mop_bills': {'bill_dicts': []}}
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
            Bill.reference.desc()).options(
            joinedload(Bill.batch).joinedload(Batch.contract).
            joinedload(Contract.party).joinedload(Party.market_role),
            joinedload(Bill.bill_type))
        if era.finish_date is not None and era != eras[0]:
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

            elif bill_role_code in ('C', 'D'):
                bill_group_name = 'dc_bills'
            elif bill_role_code == 'M':
                bill_group_name = 'mop_bills'
            else:
                raise BadRequest(
                    f"Bill group name not found for bill_contract_id "
                    f"{bill_contract.id}.")

            bill_group = era_bundle[bill_group_name]
            rows_high = 1
            bill_dict = {'bill': bill}
            bill_group['bill_dicts'].append(bill_dict)

            if bill_group_name == 'imp_bills' and era.pc.code != '00':
                inner_tpr_map = dict((code, []) for code in inner_header_codes)
                outer_tpr_map = defaultdict(list)

                for read, tpr in sess.query(
                        RegisterRead, Tpr).join(Tpr).filter(
                        RegisterRead.bill == bill).order_by(
                        Tpr.id, RegisterRead.present_date.desc()).options(
                        joinedload(RegisterRead.previous_type),
                        joinedload(RegisterRead.present_type),
                        joinedload(RegisterRead.tpr)):
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
                'imp_bills', 'exp_bills', 'dc_bills', 'mop_bills'):
            b_dicts = list(reversed(era_bundle[bill_group_name]['bill_dicts']))
            for i, b_dict in enumerate(b_dicts):
                if i < (len(b_dicts) - 1):
                    bill = b_dict['bill']
                    next_b_dict = b_dicts[i+1]
                    next_bill = next_b_dict['bill']
                    if (
                            bill.start_date, bill.finish_date, bill.kwh,
                            bill.net, bill.vat) == (
                            next_bill.start_date, next_bill.finish_date,
                            -1 * next_bill.kwh, -1 * next_bill.net,
                            next_bill.vat) and not (
                            (
                                bill.kwh, bill.net, bill.vat) == (0, 0, 0)
                            ) and 'collapsible' not in b_dict:
                        b_dict['collapsible'] = True
                        next_b_dict['first_collapsible'] = True
                        next_b_dict['collapsible'] = True
                        b_dict['collapse_id'] = next_b_dict['collapse_id'] = \
                            bill.id
    return era_bundles
