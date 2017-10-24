from collections import OrderedDict, defaultdict
from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql.expression import null, true
import traceback
from chellow.models import (
    Batch, Bill, Session, Era, Site, SiteEra, MarketRole, Contract,
    RegisterRead)
import chellow.computer
import chellow.dloads
import sys
import os
import threading
from werkzeug.exceptions import BadRequest
from chellow.utils import (
    HH, hh_format, hh_min, hh_max, req_int, csv_make_val, to_utc, req_date,
    loads)
from chellow.views import chellow_redirect
from flask import request, g
import csv
from itertools import combinations
from decimal import Decimal


def content(batch_id, bill_id, contract_id, start_date, finish_date, user):
    caches = {}
    tmp_file = sess = bill = None
    forecast_date = to_utc(Datetime.max)
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'bill_check.csv', user)
        tmp_file = open(running_name, mode='w', newline='')
        writer = csv.writer(tmp_file, lineterminator='\n')
        bills = sess.query(Bill).order_by(Bill.reference).options(
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
            'bill-mpan-core', 'site-code', 'site-name', 'covered-from',
            'covered-to', 'covered-bills', 'metered-kwh']
        for t in virtual_bill_titles:
            titles.append('covered-' + t)
            titles.append('virtual-' + t)
            if t.endswith('-gbp'):
                titles.append('difference-' + t)

        writer.writerow(titles)
        bill_ids = set(bill.id for bill in bills)
        while len(bill_ids) > 0:
            bill_id = list(sorted(bill_ids))[0]
            bill_ids.remove(bill_id)
            bill = Bill.get_by_id(sess, bill_id)
            problem = ''
            supply = bill.supply

            read_dict = {}
            for read in bill.reads:
                gen_start = read.present_date.replace(hour=0).replace(minute=0)
                gen_finish = gen_start + relativedelta(days=1) - HH
                msn_match = False
                read_msn = read.msn
                for read_era in supply.find_eras(sess, gen_start, gen_finish):
                    if read_msn == read_era.msn:
                        msn_match = True
                        break

                if not msn_match:
                    problem += "The MSN " + read_msn + \
                        " of the register read " + str(read.id) + \
                        " doesn't match the MSN of the era."

                for dt, typ in [
                        (read.present_date, read.present_type),
                        (read.previous_date, read.previous_type)]:
                    key = str(dt) + "-" + read.msn
                    try:
                        if typ != read_dict[key]:
                            problem += " Reads taken on " + str(dt) + \
                                " have differing read types."
                    except KeyError:
                        read_dict[key] = typ

            bill_start = bill.start_date
            bill_finish = bill.finish_date

            covered_start = bill_start
            covered_finish = bill_finish
            covered_bdown = {'sum-msp-kwh': 0, 'net-gbp': 0, 'vat-gbp': 0}
            enlarged = True

            while enlarged:
                enlarged = False
                covered_bills = OrderedDict(
                    (b.id, b) for b in sess.query(Bill).join(Batch).
                    join(Contract).join(MarketRole).
                    filter(
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
                                    a.kwh == -1 * b.kwh, a.net == -1 * b.net,
                                    a.vat == -1 * b.vat,
                                    a.gross == -1 * b.gross)):
                            to_del = (a.id, b.id)
                            break
                    if to_del is None:
                        break
                    else:
                        for k in to_del:
                            del covered_bills[k]
                for covered_bill in covered_bills.values():
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
                        if k.split('-')[-1] in ('rate', 'kva'):
                            covered_rates[k].add(str(v))
                        elif k != 'raw-lines':
                            try:
                                covered_bdown[k] += v
                            except KeyError:
                                covered_bdown[k] = v
                            except TypeError as detail:
                                raise BadRequest(
                                    "For key " + str(k) + " the value " +
                                    str(v) +
                                    " can't be added to the existing value " +
                                    str(covered_bdown[k]) + ". " + str(detail))
                    for k, v in covered_rates.items():
                        covered_bdown[k] = v.pop() if len(v) == 1 else None
                if primary_covered_bill is None or (
                        (
                            covered_bill.finish_date -
                            covered_bill.start_date) > (
                            primary_covered_bill.finish_date -
                            primary_covered_bill.start_date)):
                    primary_covered_bill = covered_bill

            virtual_bill = {}
            metered_kwh = 0
            for era in sess.query(Era).filter(
                    Era.supply == supply, Era.start_date <= covered_finish,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= covered_start),
                    or_(
                        Era.mop_contract == contract,
                        Era.hhdc_contract == contract,
                        Era.imp_supplier_contract == contract)).distinct():

                chunk_start = hh_max(covered_start, era.start_date)
                chunk_finish = hh_min(covered_finish, era.finish_date)

                data_source = chellow.computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era, True,
                    caches, primary_covered_bill)

                if data_source.measurement_type == 'hh':
                    metered_kwh += sum(
                        h['msp-kwh'] for h in data_source.hh_data)
                else:
                    ds = chellow.computer.SupplySource(
                        sess, chunk_start, chunk_finish, forecast_date, era,
                        True, caches)
                    metered_kwh += sum(h['msp-kwh'] for h in ds.hh_data)

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
                            "For key " + str(k) + " and value " + str(v) +
                            ". " + str(detail))

            era = supply.find_era_at(sess, bill_finish)
            if era is None:
                imp_mpan_core = site_code = site_name = None
                problem += "This bill finishes before or after the supply. "
            else:
                imp_mpan_core = era.imp_mpan_core
                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.is_physical == true(), SiteEra.era == era).one()
                site_code = site.code
                site_name = site.name

            values = [
                bill.batch.reference, bill.reference, bill.bill_type.code,
                bill.kwh, bill.net, bill.vat, hh_format(bill_start),
                hh_format(bill_finish), imp_mpan_core, site_code, site_name,
                hh_format(covered_start), hh_format(covered_finish), ':'.join(
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
