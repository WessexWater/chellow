import collections
from datetime import datetime as Datetime
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import traceback
import sys
import os
import threading
import csv
from chellow.models import Session, GBatch, GBill, GEra, Site, SiteGEra
import chellow.dloads
from werkzeug.exceptions import BadRequest
from chellow.utils import hh_before, csv_make_val, req_int, to_utc
import chellow.g_engine
from flask import request, g
from chellow.views import chellow_redirect
from decimal import Decimal


def content(g_batch_id, g_bill_id, user):
    forecast_date = to_utc(Datetime.max)
    report_context = {}
    sess = tmp_file = None
    try:
        sess = Session()

        running_name, finished_name = chellow.dloads.make_names(
            'g_bill_check.csv', user)
        tmp_file = open(running_name, "w")
        csv_writer = csv.writer(tmp_file)
        if g_batch_id is not None:
            g_batch = GBatch.get_by_id(sess, g_batch_id)
            g_bills = sess.query(GBill).filter(
                GBill.g_batch == g_batch).order_by(GBill.reference)
        elif g_bill_id is not None:
            g_bill = GBill.get_by_id(sess, g_bill_id)
            g_bills = sess.query(GBill).filter(GBill.id == g_bill.id)
            g_batch = g_bill.g_batch

        g_contract = g_batch.g_contract

        vbf = chellow.g_engine.g_contract_func(
            report_context, g_contract, 'virtual_bill')
        if vbf is None:
            raise BadRequest(
                'The contract ' + g_contract.name +
                " doesn't have a function virtual_bill.")

        header_titles = [
            'batch', 'bill_reference', 'bill_type', 'bill_start_date',
            'bill_finish_date', 'mprn', 'supply_name', 'site_code',
            'site_name', 'covered_start', 'covered_finish', 'covered_bill_ids']
        bill_titles = chellow.g_engine.g_contract_func(
            report_context, g_contract, 'virtual_bill_titles')()

        titles = header_titles[:]
        for title in bill_titles:
            for prefix in ('covered_', 'virtual_'):
                titles.append(prefix + title)
            if title.endswith('_gbp'):
                titles.append('difference_' + title)

        csv_writer.writerow(titles)
        for g_bill in g_bills:
            problem = ''
            g_supply = g_bill.g_supply
            read_dict = collections.defaultdict(set)
            for g_read in g_bill.g_reads:
                if not all(
                        g_read.msn == era.msn for era in g_supply.find_g_eras(
                            sess, g_read.prev_date, g_read.pres_date)):
                    problem += "The MSN " + g_read.msn + \
                        " of the register read " + str(g_read.id) + \
                        " doesn't match the MSN of all the relevant eras."

                for dt, typ in [
                        (g_read.pres_date, g_read.pres_type),
                        (g_read.prev_date, g_read.prev_type)]:
                    typ_set = read_dict[str(dt) + "-" + g_read.msn]
                    typ_set.add(typ)
                    if len(typ_set) > 1:
                            problem += " Reads taken on " + str(dt) + \
                                " have differing read types."

            g_era = g_supply.find_g_era_at(sess, g_bill.finish_date)
            if g_era is None:
                csv_writer.writerow(
                    [
                        "Extraordinary! There isn't a era for this bill!"])
                continue

            vals = {
                    'batch': g_batch.reference,
                    'bill_reference': g_bill.reference,
                    'bill_type': g_bill.bill_type.code,
                    'bill_start_date': g_bill.start_date,
                    'bill_finish_date': g_bill.finish_date,
                    'mprn': g_supply.mprn, 'covered_vat_gbp': Decimal('0.00'),
                    'covered_net_gbp': Decimal('0.00'),
                    'covered_gross_gbp': Decimal('0.00'),
                    'covered_kwh': Decimal(0),
                    'covered_start': g_bill.start_date,
                    'covered_finish': g_bill.finish_date,
                    'covered_bill_ids': []}

            covered_primary_bill = None
            enlarged = True

            while enlarged:
                enlarged = False
                for covered_bill in sess.query(GBill).filter(
                        GBill.g_supply_id == g_supply.id,
                        GBill.start_date <= vals['covered_finish'],
                        GBill.finish_date >= vals['covered_start']).order_by(
                        GBill.issue_date.desc(), GBill.start_date):

                    if covered_primary_bill is None and \
                            len(covered_bill.g_reads) > 0:
                        covered_primary_bill = covered_bill
                    if covered_bill.start_date < vals['covered_start']:
                        vals['covered_start'] = covered_bill.start_date
                        enlarged = True
                        break
                    if covered_bill.finish_date > vals['covered_finish']:
                        vals['covered_finish'] = covered_bill.finish_date
                        enlarged = True
                        break

            for covered_bill in sess.query(GBill).filter(
                    GBill.g_supply == g_supply,
                    GBill.start_date <= vals['covered_finish'],
                    GBill.finish_date >= vals['covered_start']).order_by(
                    GBill.issue_date.desc(), GBill.start_date):
                vals['covered_bill_ids'].append(covered_bill.id)
                bdown = covered_bill.make_breakdown()
                vals['covered_kwh'] += covered_bill.kwh
                vals['covered_net_gbp'] += covered_bill.net
                vals['covered_vat_gbp'] += covered_bill.vat
                vals['covered_gross_gbp'] += covered_bill.gross
                for title in bill_titles:
                    k = 'covered_' + title
                    v = bdown.get(title)

                    if v is not None:
                        if title.endswith('_rate') or title in (
                                'correction_factor', 'calorific_value',
                                'units'):
                            if k not in vals:
                                vals[k] = set()
                            vals[k].add(v)
                        else:
                            try:
                                vals[k] += v
                            except KeyError:
                                vals[k] = v
                            except TypeError:
                                raise BadRequest(
                                    "Problem with key " + str(k) +
                                    " and value " + str(v) + " for existing " +
                                    str(vals[k]))

                    if title in (
                            'correction_factor', 'calorific_value',
                            'units_code', 'units_factor'):
                        if k not in vals:
                            vals[k] = set()
                        for g_read in covered_bill.g_reads:
                            if title in ('units_code', 'units_factor'):
                                g_units = g_read.g_units
                                if title == 'units_code':
                                    v = g_units.code
                                else:
                                    v = g_units.factor
                            else:
                                v = getattr(g_read, title)
                            vals[k].add(v)

            for g_era in sess.query(GEra).filter(
                    GEra.g_supply == g_supply,
                    GEra.start_date <= vals['covered_finish'],
                    or_(
                        GEra.finish_date == null(),
                        GEra.finish_date >= vals['covered_start'])).distinct():
                site = sess.query(Site).join(SiteGEra).filter(
                    SiteGEra.is_physical == true(),
                    SiteGEra.g_era == g_era).one()

                if vals['covered_start'] > g_era.start_date:
                    chunk_start = vals['covered_start']
                else:
                    chunk_start = g_era.start_date

                if hh_before(vals['covered_finish'], g_era.finish_date):
                    chunk_finish = vals['covered_finish']
                else:
                    chunk_finish = g_era.finish_date

                data_source = chellow.g_engine.GDataSource(
                    sess, chunk_start, chunk_finish, forecast_date, g_era,
                    report_context, covered_primary_bill)

                vbf(data_source)

                for k, v in data_source.bill.items():
                    vk = 'virtual_' + k
                    try:
                        if isinstance(v, set):
                            vals[vk].update(v)
                        else:
                            vals[vk] += v
                    except KeyError:
                        vals[vk] = v
                    except TypeError as detail:
                        raise BadRequest(
                            "For key " + str(vk) + " and value " + str(v) +
                            ". " + str(detail))

            vals['supply_name'] = g_supply.name
            vals['site_code'] = site.code
            vals['site_name'] = site.name

            for k, v in vals.items():
                vals[k] = csv_make_val(v)

            for i, title in enumerate(titles):
                if title.startswith('difference_'):
                    try:
                        covered_val = float(vals[titles[i - 2]])
                        virtual_val = float(vals[titles[i - 1]])
                        vals[title] = covered_val - virtual_val
                    except KeyError:
                        vals[title] = None

            csv_writer.writerow(
                [
                    (vals.get(k) if vals.get(k) is not None else '')
                    for k in titles])

    except BadRequest as e:
        tmp_file.write("Problem: " + e.description)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        tmp_file.write("Problem " + msg)
    finally:
        try:
            if sess is not None:
                sess.close()
        except BaseException:
            tmp_file.write("\nProblem closing session.")
        finally:
            tmp_file.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    if 'g_batch_id' in request.values:
        g_batch_id = req_int('g_batch_id')
        g_bill_id = None
    elif 'g_bill_id' in request.values:
        g_bill_id = req_int('g_bill_id')
        g_batch_id = None
    else:
        raise BadRequest("The bill check needs a g_batch_id or g_bill_id.")

    threading.Thread(
        target=content, args=(g_batch_id, g_bill_id, g.user)).start()
    return chellow_redirect('/downloads', 303)
