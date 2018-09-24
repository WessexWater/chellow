from collections import OrderedDict, defaultdict
from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql.expression import null, true
import traceback
from chellow.models import (
    Batch, Bill, Session, Era, Site, SiteEra, MarketRole, Contract, Mtc, Llfc,
    RegisterRead, Supply)
import chellow.computer
import chellow.dloads
import sys
import os
import threading
from werkzeug.exceptions import BadRequest
from chellow.utils import (
    HH, hh_format, hh_min, hh_max, req_int, csv_make_val, to_utc, req_date,
    hh_range)
from chellow.views import chellow_redirect
from flask import request, g
import csv
from itertools import combinations
from decimal import Decimal
from zish import loads, ZishLocationException


def add_gap(caches, gaps, elem, start_date, finish_date, is_virtual, gbp):
    try:
        elgap = gaps[elem]
    except KeyError:
        elgap = gaps[elem] = {}

    hhs = hh_range(caches, start_date, finish_date)
    hhgbp = 0 if gbp is None else gbp / len(hhs)

    for hh_start in hhs:
        try:
            hhgap = elgap[hh_start]
        except KeyError:
            hhgap = elgap[hh_start] = {
                'has_covered': False,
                'has_virtual': False,
                'gbp': 0}

        if is_virtual:
            hhgap['has_virtual'] = True
            hhgap['gbp'] = hhgbp
        else:
            hhgap['has_covered'] = True


def find_elements(bill):
    try:
        keys = [k for k in loads(bill.breakdown).keys() if k.endswith('-gbp')]
        return set(k[:-4] for k in keys)
    except ZishLocationException as e:
        raise BadRequest(
            "Can't parse the breakdown for bill id " + str(bill.id) +
            " attached to batch id " + str(bill.batch.id) + ": " + str(e))


def content(batch_id, bill_id, contract_id, start_date, finish_date, user):
    caches = {}
    tmp_file = sess = bill = None
    forecast_date = to_utc(Datetime.max)
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'bill_check.csv', user)
        tmp_file = open(running_name, mode='w', newline='')
        writer = csv.writer(tmp_file, lineterminator='\n')
        bills = sess.query(Bill).order_by(
            Bill.supply_id, Bill.reference).options(
            joinedload(Bill.supply),
            subqueryload(Bill.reads).joinedload(RegisterRead.present_type),
            subqueryload(Bill.reads).joinedload(RegisterRead.previous_type),
            joinedload(Bill.batch))
        if batch_id is not None:
            batch = Batch.get_by_id(sess, batch_id)
            bills = bills.filter(Bill.batch == batch)
            contract = batch.contract
        elif bill_id is not None:
            bill = Bill.get_by_id(sess, bill_id)
            bills = bills.filter(Bill.id == bill.id)
            contract = bill.batch.contract
        elif contract_id is not None:
            contract = Contract.get_by_id(sess, contract_id)
            bills = bills.join(Batch).filter(
                Batch.contract == contract, Bill.start_date <= finish_date,
                Bill.finish_date >= start_date)

        market_role_code = contract.market_role.code
        vbf = chellow.computer.contract_func(caches, contract, 'virtual_bill')
        if vbf is None:
            raise BadRequest(
                'The contract ' + contract.name +
                " doesn't have a function virtual_bill.")

        virtual_bill_titles_func = chellow.computer.contract_func(
            caches, contract, 'virtual_bill_titles')
        if virtual_bill_titles_func is None:
            raise BadRequest(
                'The contract ' + contract.name +
                " doesn't have a function virtual_bill_titles.")
        virtual_bill_titles = virtual_bill_titles_func()

        titles = [
            'batch', 'bill-reference', 'bill-type', 'bill-kwh', 'bill-net-gbp',
            'bill-vat-gbp', 'bill-start-date', 'bill-finish-date',
            'imp-mpan-core', 'exp-mpan-core', 'site-code', 'site-name',
            'covered-from', 'covered-to', 'covered-bills', 'metered-kwh']
        for t in virtual_bill_titles:
            titles.append('covered-' + t)
            titles.append('virtual-' + t)
            if t.endswith('-gbp'):
                titles.append('difference-' + t)

        writer.writerow(titles)

        bill_map = defaultdict(set, {})
        for bill in bills:
            bill_map[bill.supply.id].add(bill.id)

        for supply_id, bill_ids in bill_map.items():
            gaps = {}
            while len(bill_ids) > 0:
                bill_id = list(sorted(bill_ids))[0]
                bill_ids.remove(bill_id)
                bill = sess.query(Bill).filter(Bill.id == bill_id).options(
                    joinedload(Bill.batch),
                    joinedload(Bill.bill_type),
                    joinedload(Bill.reads),
                    joinedload(Bill.supply),
                    joinedload(Bill.reads).joinedload(
                        RegisterRead.present_type),
                    joinedload(Bill.reads).joinedload(
                        RegisterRead.previous_type)).one()
                virtual_bill = {'problem': ''}
                supply = bill.supply

                read_dict = {}
                for read in bill.reads:
                    gen_start = read.present_date.replace(hour=0).replace(
                        minute=0)
                    gen_finish = gen_start + relativedelta(days=1) - HH
                    msn_match = False
                    read_msn = read.msn
                    for read_era in supply.find_eras(
                            sess, gen_start, gen_finish):
                        if read_msn == read_era.msn:
                            msn_match = True
                            break

                    if not msn_match:
                        virtual_bill['problem'] += "The MSN " + read_msn + \
                            " of the register read " + str(read.id) + \
                            " doesn't match the MSN of the era."

                    for dt, typ in [
                            (read.present_date, read.present_type),
                            (read.previous_date, read.previous_type)]:
                        key = str(dt) + "-" + read.msn
                        try:
                            if typ != read_dict[key]:
                                virtual_bill['problem'] += " Reads taken " + \
                                    "on " + str(dt) + \
                                    " have differing read types."
                        except KeyError:
                            read_dict[key] = typ

                bill_start = bill.start_date
                bill_finish = bill.finish_date

                covered_start = bill_start
                covered_finish = bill_finish
                covered_bdown = {'sum-msp-kwh': 0, 'net-gbp': 0, 'vat-gbp': 0}

                vb_elems = set()
                enlarged = True

                while enlarged:
                    enlarged = False
                    covered_elems = find_elements(bill)
                    covered_bills = OrderedDict(
                        (b.id, b) for b in sess.query(Bill).join(Batch).
                        join(Contract).join(MarketRole).filter(
                            Bill.supply == supply,
                            Bill.start_date <= covered_finish,
                            Bill.finish_date >= covered_start,
                            MarketRole.code == market_role_code).order_by(
                                Bill.start_date, Bill.issue_date))
                    while True:
                        to_del = None
                        for a, b in combinations(covered_bills.values(), 2):
                            if all(
                                    (
                                        a.start_date == b.start_date,
                                        a.finish_date == b.finish_date,
                                        a.kwh == -1 * b.kwh,
                                        a.net == -1 * b.net,
                                        a.vat == -1 * b.vat,
                                        a.gross == -1 * b.gross)):
                                to_del = (a.id, b.id)
                                break
                        if to_del is None:
                            break
                        else:
                            for k in to_del:
                                del covered_bills[k]

                    for k, covered_bill in tuple(covered_bills.items()):
                        elems = find_elements(covered_bill)
                        if elems.isdisjoint(covered_elems):
                            if k != bill.id:
                                del covered_bills[k]
                                continue
                        else:
                            covered_elems.update(elems)

                        if covered_bill.start_date < covered_start:
                            covered_start = covered_bill.start_date
                            enlarged = True
                            break

                        if covered_bill.finish_date > covered_finish:
                            covered_finish = covered_bill.finish_date
                            enlarged = True
                            break

                if bill.id not in covered_bills:
                    continue

                primary_covered_bill = None
                for covered_bill in covered_bills.values():
                    if covered_bill.id in bill_ids:
                        bill_ids.remove(covered_bill.id)
                    covered_bdown['net-gbp'] += float(covered_bill.net)
                    covered_bdown['vat-gbp'] += float(covered_bill.vat)
                    covered_bdown['sum-msp-kwh'] += float(covered_bill.kwh)
                    if len(covered_bill.breakdown) > 0:
                        covered_rates = defaultdict(set)
                        for k, v in loads(covered_bill.breakdown).items():
                            if isinstance(v, Decimal):
                                v = float(v)
                            if isinstance(v, list):
                                covered_rates[k].update(set(v))
                            elif k.split('-')[-1] in ('rate', 'kva'):
                                covered_rates[k].add(str(v))
                            elif k != 'raw-lines':
                                try:
                                    covered_bdown[k] += v
                                except KeyError:
                                    covered_bdown[k] = v
                                except TypeError as detail:
                                    raise BadRequest(
                                        "For key " + str(k) + " the value " +
                                        str(v) + " can't be added to the "
                                        "existing value " +
                                        str(covered_bdown[k]) + ". " +
                                        str(detail))
                            if k.endswith('-gbp'):
                                elem = k[:-4]
                                covered_elems.add(elem)
                                add_gap(
                                    caches, gaps, elem,
                                    covered_bill.start_date,
                                    covered_bill.finish_date, False, v)

                        for k, v in covered_rates.items():
                            covered_bdown[k] = v.pop() if len(v) == 1 else None
                    if primary_covered_bill is None or (
                            (
                                covered_bill.finish_date -
                                covered_bill.start_date) > (
                                primary_covered_bill.finish_date -
                                primary_covered_bill.start_date)):
                        primary_covered_bill = covered_bill

                metered_kwh = 0
                for era in sess.query(Era).filter(
                        Era.supply == supply, Era.start_date <= covered_finish,
                        or_(
                            Era.finish_date == null(),
                            Era.finish_date >= covered_start)
                        ).distinct().options(
                        joinedload(Era.channels),
                        joinedload(Era.cop),
                        joinedload(Era.dc_contract),
                        joinedload(Era.exp_llfc),
                        joinedload(Era.exp_llfc).joinedload(
                            Llfc.voltage_level),
                        joinedload(Era.exp_supplier_contract),
                        joinedload(Era.imp_llfc),
                        joinedload(Era.imp_llfc).joinedload(
                            Llfc.voltage_level),
                        joinedload(Era.imp_supplier_contract),
                        joinedload(Era.mop_contract),
                        joinedload(Era.mtc).joinedload(Mtc.meter_type),
                        joinedload(Era.pc),
                        joinedload(Era.supply).joinedload(Supply.dno),
                        joinedload(Era.supply).joinedload(Supply.gsp_group),
                        joinedload(Era.supply).joinedload(Supply.source)):

                    chunk_start = hh_max(covered_start, era.start_date)
                    chunk_finish = hh_min(covered_finish, era.finish_date)

                    if contract not in (
                            era.mop_contract, era.dc_contract,
                            era.imp_supplier_contract,
                            era.exp_supplier_contract):
                        virtual_bill['problem'] += ''.join(
                            (
                                "From ", hh_format(chunk_start), " to ",
                                hh_format(chunk_finish), " the contract of ",
                                "the era doesn't match the contract of the ",
                                "bill."))
                        continue

                    if contract.market_role.code == 'X':
                        polarity = contract != era.exp_supplier_contract
                    else:
                        polarity = era.imp_supplier_contract is not None
                    pairs = []
                    last_finish = chunk_start - HH
                    for hd in chellow.computer.datum_range(
                            sess, caches, 0, chunk_start, chunk_finish):
                        if hd['utc-is-month-end'] or hd['ct-is-month-end']:
                            end_date = hd['start-date']
                            pairs.append((last_finish + HH, end_date))
                            last_finish = end_date
                    if hd['start-date'] > last_finish:
                        pairs.append((last_finish + HH, hd['start-date']))

                    for ss_start, ss_finish in pairs:
                        data_source = chellow.computer.SupplySource(
                            sess, ss_start, ss_finish, forecast_date, era,
                            polarity, caches, primary_covered_bill)

                        if data_source.measurement_type == 'hh':
                            metered_kwh += sum(
                                h['msp-kwh'] for h in data_source.hh_data)
                        else:
                            ds = chellow.computer.SupplySource(
                                sess, ss_start, ss_finish, forecast_date, era,
                                polarity, caches)
                            metered_kwh += sum(
                                h['msp-kwh'] for h in ds.hh_data)

                        vbf(data_source)

                        if market_role_code == 'X':
                            vb = data_source.supplier_bill
                        elif market_role_code == 'C':
                            vb = data_source.dc_bill
                        elif market_role_code == 'M':
                            vb = data_source.mop_bill
                        else:
                            raise BadRequest("Odd market role.")

                        for k, v in vb.items():
                            try:
                                if isinstance(v, set):
                                    virtual_bill[k].update(v)
                                else:
                                    virtual_bill[k] += v
                            except KeyError:
                                virtual_bill[k] = v
                            except TypeError as detail:
                                raise BadRequest(
                                    "For key " + str(k) + " and value " +
                                    str(v) + ". " + str(detail))

                            if all(
                                    (
                                        k.endswith('-gbp'),
                                        k != 'net-gbp', v != 0)):
                                add_gap(
                                    caches, gaps, k[:-4], ss_start,
                                    ss_finish, True, v)

                        for k in virtual_bill.keys():
                            if k.endswith('-gbp'):
                                vb_elems.add(k[:-4])

                for elem in vb_elems.difference(covered_elems):
                    for k, v in tuple(virtual_bill.items()):
                        if k.startswith(elem + '-'):
                            del virtual_bill[k]

                try:
                    del virtual_bill['net-gbp']
                except KeyError:
                    pass

                virtual_bill['net-gbp'] = sum(
                    v for k, v in virtual_bill.items() if k.endswith('-gbp'))

                era = supply.find_era_at(sess, bill_finish)
                if era is None:
                    imp_mpan_core = exp_mpan_core = None
                    site_code = site_name = None
                    virtual_bill['problem'] += \
                        "This bill finishes before or after the supply. "
                else:
                    imp_mpan_core = era.imp_mpan_core
                    exp_mpan_core = era.exp_mpan_core

                    site = sess.query(Site).join(SiteEra).filter(
                        SiteEra.is_physical == true(),
                        SiteEra.era == era).one()
                    site_code = site.code
                    site_name = site.name

                values = [
                    bill.batch.reference, bill.reference, bill.bill_type.code,
                    bill.kwh, bill.net, bill.vat, hh_format(bill_start),
                    hh_format(bill_finish), imp_mpan_core, exp_mpan_core,
                    site_code, site_name, hh_format(covered_start),
                    hh_format(covered_finish), ':'.join(
                        str(i).replace(',', '') for i in covered_bills.keys()),
                    metered_kwh]

                for title in virtual_bill_titles:
                    try:
                        cov_val = covered_bdown[title]
                        values.append(cov_val)
                        del covered_bdown[title]
                    except KeyError:
                        cov_val = None
                        values.append('')

                    try:
                        virt_val = csv_make_val(virtual_bill[title])
                        values.append(virt_val)
                        del virtual_bill[title]
                    except KeyError:
                        virt_val = 0
                        values.append('')

                    if title.endswith('-gbp'):
                        if isinstance(virt_val, (int, float, Decimal)):
                            if isinstance(cov_val, (int, float, Decimal)):
                                values.append(float(cov_val) - float(virt_val))
                            else:
                                values.append(0 - float(virt_val))
                        else:
                            values.append('')

                for title in sorted(virtual_bill.keys()):
                    virt_val = csv_make_val(virtual_bill[title])
                    values += ['virtual-' + title, virt_val]
                    if title in covered_bdown:
                        values += ['covered-' + title, covered_bdown[title]]
                    else:
                        values += ['', '']

                writer.writerow(values)

                for bill in sess.query(Bill).filter(
                        Bill.supply == supply,
                        Bill.start_date <= covered_finish,
                        Bill.finish_date >= covered_start):

                    for k, v in loads(bill.breakdown).items():
                        if k.endswith('-gbp'):
                            add_gap(
                                caches, gaps, k[:-4], bill.start_date,
                                bill.finish_date, False, v)

            clumps = []
            for element, elgap in sorted(gaps.items()):
                for start_date, hhgap in sorted(elgap.items()):
                    if hhgap['has_virtual'] and not hhgap['has_covered']:

                        if len(clumps) == 0 or not all(
                                (
                                    clumps[-1]['element'] == element,
                                    clumps[-1]['finish_date'] + HH ==
                                    start_date)):
                            clumps.append(
                                {
                                    'element': element,
                                    'start_date': start_date,
                                    'finish_date': start_date,
                                    'gbp': hhgap['gbp']})
                        else:
                            clumps[-1]['finish_date'] = start_date

            for i, clump in enumerate(clumps):
                vals = dict((title, '') for title in titles)
                vals['covered-problem'] = '_'.join(
                    (
                        'missing', clump['element'], 'supplyid',
                        str(supply.id), 'from',
                        hh_format(clump['start_date'])))
                vals['imp-mpan-core'] = imp_mpan_core
                vals['exp-mpan-core'] = exp_mpan_core
                vals['batch'] = 'missing_bill'
                vals['bill-start-date'] = hh_format(clump['start_date'])
                vals['bill-finish-date'] = hh_format(clump['finish_date'])
                vals['difference-net-gbp'] = clump['gbp']
                writer.writerow(vals[title] for title in titles)

            # Avoid long-running transactions
            sess.rollback()

    except BadRequest as e:
        if bill is None:
            prefix = "Problem: "
        else:
            prefix = "Problem with bill " + str(bill.id) + ':'
        tmp_file.write(prefix + e.description)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        tmp_file.write("Problem " + msg)
    finally:
        if sess is not None:
            sess.close()
        tmp_file.close()
        os.rename(running_name, finished_name)


def do_get(sess):
    batch_id = bill_id = contract_id = start_date = finish_date = None
    if 'batch_id' in request.values:
        batch_id = req_int("batch_id")
    elif 'bill_id' in request.values:
        bill_id = req_int("bill_id")
    elif 'contract_id' in request.values:
        contract_id = req_int("contract_id")
        start_date = req_date("start_date")
        finish_date = req_date("finish_date")
    else:
        raise BadRequest(
            "The bill check needs a batch_id, a bill_id or a start_date "
            "and finish_date.")

    args = batch_id, bill_id, contract_id, start_date, finish_date, g.user
    threading.Thread(target=content, args=args).start()
    return chellow_redirect('/downloads', 303)
