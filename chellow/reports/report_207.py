import traceback
import pytz
from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, func
from sqlalchemy.sql.expression import null, true
import math
import chellow.dloads
import sys
import os
import threading
from chellow.utils import HH, hh_format, req_int, hh_min, hh_max
from chellow.models import (
    Supply, Era, Source, Site, SiteEra, Bill, RegisterRead, BillType, ReadType,
    HhDatum, Channel, Session)
from flask import request, g
from chellow.views import chellow_redirect
import csv


def content(year, supply_id, user):
    f = sess = None
    try:
        sess = Session()
        fname = ['crc', str(year), str(year + 1)]
        if supply_id is None:
            fname.append('all_supplies')
        else:
            fname.append('supply_' + str(supply_id))
        running_name, finished_name = chellow.dloads.make_names(
            '_'.join(fname) + '.csv', user)
        f = open(running_name, mode='w', newline='')
        w = csv.writer(f, lineterminator='\n')

        ACTUAL_READ_TYPES = ['N', 'N3', 'C', 'X', 'CP']
        w.writerow(
            (
                'Chellow Supply Id', 'Report Start', 'Report Finish',
                'MPAN Core', 'Site Id', 'Site Name', 'From', 'To',
                'NHH Breakdown', 'Actual HH Normal Days',
                'Actual AMR Normal Days', 'Actual NHH Normal Days',
                'Actual Unmetered Normal Days', 'Max HH Normal Days',
                'Max AMR Normal Days', 'Max NHH Normal Days',
                'Max Unmetered Normal Days', 'Total Actual Normal Days',
                'Total Max Normal Days', 'Data Type', 'HH kWh', 'AMR kWh',
                'NHH kWh', 'Unmetered kwh', 'HH Filled kWh', 'AMR Filled kWh',
                'Total kWh', 'Note'))

        year_start = Datetime(year, 4, 1, tzinfo=pytz.utc)
        year_finish = year_start + relativedelta(years=1) - HH

        supplies = sess.query(Supply).join(Era).join(Source).filter(
            Source.code.in_(('net', 'gen-net')), Era.imp_mpan_core != null(),
            Era.start_date <= year_finish, or_(
                Era.finish_date == null(),
                Era.finish_date >= year_start)).distinct().order_by(Supply.id)
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            supplies = supplies.filter(Supply.id == supply.id)

        meter_types = ('hh', 'amr', 'nhh', 'unmetered')

        for supply in supplies:
            total_kwh = dict([(mtype, 0) for mtype in meter_types])
            filled_kwh = dict([(mtype, 0) for mtype in ('hh', 'amr')])
            normal_days = dict([(mtype, 0) for mtype in meter_types])
            max_normal_days = dict([(mtype, 0) for mtype in meter_types])

            breakdown = ''
            eras = sess.query(Era).filter(
                Era.supply == supply, Era.start_date <= year_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= year_start)).order_by(
                Era.start_date).all()
            supply_from = hh_max(eras[0].start_date, year_start)
            supply_to = hh_min(eras[-1].finish_date, year_finish)

            for era in eras:

                meter_type = era.meter_category

                period_start = hh_max(era.start_date, year_start)
                period_finish = hh_min(era.finish_date, year_finish)

                max_normal_days[meter_type] += (
                    (period_finish - period_start).total_seconds() +
                    60 * 30) / (60 * 60 * 24)

                mpan_core = era.imp_mpan_core
                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.is_physical == true(),
                    SiteEra.era_id == era.id).one()

                if meter_type == 'nhh':

                    read_list = []
                    read_keys = {}
                    pairs = []

                    prior_pres_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType)
                        .join(RegisterRead.present_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply == supply,
                            RegisterRead.present_date < period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.present_date.desc()))
                    prior_prev_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType)
                        .join(RegisterRead.previous_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply == supply,
                            RegisterRead.previous_date < period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.previous_date.desc()))
                    next_pres_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType)
                        .join(RegisterRead.present_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply == supply,
                            RegisterRead.present_date >= period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.present_date))
                    next_prev_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType).
                        join(RegisterRead.previous_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply == supply,
                            RegisterRead.previous_date >= period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.previous_date))

                    for is_forwards in [False, True]:
                        if is_forwards:
                            pres_reads = next_pres_reads
                            prev_reads = next_prev_reads
                            read_list.reverse()
                        else:
                            pres_reads = prior_pres_reads
                            prev_reads = prior_prev_reads

                        prime_pres_read = None
                        prime_prev_read = None
                        while True:
                            while prime_pres_read is None:
                                try:
                                    pres_read = next(pres_reads)
                                except StopIteration:
                                    break

                                pres_date = pres_read.present_date
                                pres_msn = pres_read.msn
                                read_key = '_'.join([str(pres_date), pres_msn])
                                if read_key in read_keys:
                                    continue

                                pres_bill = sess.query(Bill).join(BillType). \
                                    filter(
                                        Bill.reads.any(),
                                        Bill.supply == supply,
                                        Bill.finish_date >=
                                        pres_read.bill.start_date,
                                        Bill.start_date <=
                                        pres_read.bill.finish_date,
                                        BillType.code != 'W').order_by(
                                        Bill.issue_date.desc(),
                                        BillType.code).first()
                                if pres_bill != pres_read.bill:
                                    continue

                                reads = dict(
                                    (
                                        read.tpr.code,
                                        float(read.present_value) *
                                        float(read.coefficient))
                                    for read in sess.query(RegisterRead).
                                    filter(
                                        RegisterRead.units == 0,
                                        RegisterRead.bill == pres_bill,
                                        RegisterRead.present_date == pres_date,
                                        RegisterRead.msn == pres_msn))

                                prime_pres_read = {
                                    'date': pres_date, 'reads': reads,
                                    'msn': pres_msn}
                                read_keys[read_key] = None
                            while prime_prev_read is None:
                                try:
                                    prev_read = next(prev_reads)
                                except StopIteration:
                                    break

                                prev_date = prev_read.previous_date
                                prev_msn = prev_read.msn
                                read_key = '_'.join([str(prev_date), prev_msn])
                                if read_key in read_keys:
                                    continue
                                prev_bill = sess.query(Bill).join(BillType). \
                                    filter(
                                        Bill.reads.any(),
                                        Bill.supply_id == supply.id,
                                        Bill.finish_date >=
                                        prev_read.bill.start_date,
                                        Bill.start_date <=
                                        prev_read.bill.finish_date,
                                        BillType.code != 'W').order_by(
                                        Bill.issue_date.desc(),
                                        BillType.code).first()
                                if prev_bill != prev_read.bill:
                                    continue

                                reads = dict(
                                    (
                                        read.tpr.code,
                                        float(read.previous_value) *
                                        float(read.coefficient))
                                    for read in sess.query(RegisterRead).
                                    filter(
                                        RegisterRead.units == 0,
                                        RegisterRead.bill_id == prev_bill.id,
                                        RegisterRead.previous_date ==
                                        prev_date,
                                        RegisterRead.msn == prev_msn))

                                prime_prev_read = {
                                    'date': prev_date, 'reads': reads,
                                    'msn': prev_msn}
                                read_keys[read_key] = None

                            if prime_pres_read is None and \
                                    prime_prev_read is None:
                                break
                            elif prime_pres_read is None:
                                read_list.append(prime_prev_read)
                                prime_prev_read = None
                            elif prime_prev_read is None:
                                read_list.append(prime_pres_read)
                                prime_pres_read = None
                            else:
                                if is_forwards:
                                    if prime_pres_read['date'] <= \
                                            prime_prev_read['date']:
                                        read_list.append(prime_pres_read)
                                        prime_pres_read = None
                                    else:
                                        read_list.append(prime_prev_read)
                                        prime_prev_read = None
                                else:
                                    if prime_prev_read['date'] >= \
                                            prime_pres_read['date']:
                                        read_list.append(prime_prev_read)
                                        prime_prev_read = None
                                    else:
                                        read_list.append(prime_pres_read)
                                        prime_pres_read = None

                            if len(read_list) > 1:
                                if is_forwards:
                                    aft_read = read_list[-2]
                                    fore_read = read_list[-1]
                                else:
                                    aft_read = read_list[-1]
                                    fore_read = read_list[-2]

                                if aft_read['msn'] == fore_read['msn'] and \
                                        set(aft_read['reads'].keys()) == \
                                        set(fore_read['reads'].keys()):
                                    pair_start_date = aft_read['date'] + HH
                                    pair_finish_date = fore_read['date']

                                    num_hh = (
                                        (
                                            pair_finish_date + HH -
                                            pair_start_date).total_seconds()
                                        ) / (30 * 60)

                                    tprs = {}
                                    for tpr_code, initial_val in \
                                            aft_read['reads'].items():
                                        end_val = fore_read['reads'][tpr_code]

                                        kwh = end_val - initial_val

                                        if kwh < 0:
                                            digits = int(
                                                math.log10(initial_val)) + 1
                                            kwh = 10 ** digits + kwh

                                        tprs[tpr_code] = kwh / num_hh

                                    pairs.append(
                                        {
                                            'start-date': pair_start_date,
                                            'finish-date': pair_finish_date,
                                            'tprs': tprs})

                                    if len(pairs) > 0 and (
                                            not is_forwards or (
                                                is_forwards and
                                                read_list[-1]['date'] >
                                                period_finish)):
                                        break

                    breakdown += 'read list - \n' + str(read_list) + "\n"
                    if len(pairs) == 0:
                        pairs.append(
                            {
                                'start-date': period_start,
                                'finish-date': period_finish,
                                'tprs': {'00001': 0}})
                    else:
                        for pair in pairs:
                            pair_start = pair['start-date']
                            pair_finish = pair['finish-date']
                            if pair_start >= year_start and \
                                    pair_finish <= year_finish:
                                block_start = hh_max(pair_start, period_start)
                                block_finish = hh_min(
                                    pair_finish, period_finish)

                                if block_start <= block_finish:
                                    normal_days[meter_type] += (
                                        (
                                            block_finish - block_start
                                        ).total_seconds() +
                                        60 * 30) / (60 * 60 * 24)

                    # smooth
                    for i in range(1, len(pairs)):
                        pairs[i - 1]['finish-date'] = pairs[i]['start-date'] \
                            - HH

                    # stretch
                    if pairs[0]['start-date'] > period_start:
                        pairs[0]['start-date'] = period_start

                    if pairs[-1]['finish-date'] < period_finish:
                        pairs[-1]['finish-date'] = period_finish

                    # chop
                    pairs = [
                        pair for pair in pairs
                        if not pair['start-date'] > period_finish and
                        not pair['finish-date'] < period_start]

                    # squash
                    if pairs[0]['start-date'] < period_start:
                        pairs[0]['start-date'] = period_start

                    if pairs[-1]['finish-date'] > period_finish:
                        pairs[-1]['finish-date'] = period_finish

                    for pair in pairs:
                        pair_hhs = (
                            (
                                pair['finish-date'] - pair['start-date']
                            ).total_seconds() + 30 * 60) / (60 * 30)
                        pair['pair_hhs'] = pair_hhs
                        for tpr_code, pair_kwh in pair['tprs'].items():
                            total_kwh[meter_type] += pair_kwh * pair_hhs

                    breakdown += 'pairs - \n' + str(pairs)

                elif meter_type in ('hh', 'amr'):
                    period_kwhs = list(
                        float(v[0]) for v in sess.query(HhDatum.value).
                        join(Channel).filter(
                            Channel.imp_related == true(),
                            Channel.channel_type == 'ACTIVE',
                            Channel.era == era,
                            HhDatum.start_date >= period_start,
                            HhDatum.start_date <= period_finish).order_by(
                                HhDatum.id))
                    year_kwhs = list(
                        float(v[0]) for v in sess.query(HhDatum.value).
                        join(Channel).join(Era).filter(
                            Channel.imp_related == true(),
                            Channel.channel_type == 'ACTIVE',
                            Era.supply == supply,
                            HhDatum.start_date >= year_start,
                            HhDatum.start_date <= year_finish).order_by(
                                HhDatum.id))

                    period_sum_kwhs = sum(period_kwhs)
                    year_sum_kwhs = sum(year_kwhs)
                    period_len_kwhs = len(period_kwhs)
                    year_len_kwhs = len(year_kwhs)
                    total_kwh[meter_type] += period_sum_kwhs
                    period_hhs = (
                        period_finish + HH - period_start
                        ).total_seconds() / (60 * 30)
                    if year_len_kwhs > 0:
                        filled_kwh[meter_type] += year_sum_kwhs / \
                            year_len_kwhs * (period_hhs - period_len_kwhs)
                    normal_days[meter_type] += sess.query(
                        func.count(HhDatum.value)).join(Channel). \
                        filter(
                            Channel.imp_related == true(),
                            Channel.channel_type == 'ACTIVE',
                            Channel.era == era,
                            HhDatum.start_date >= period_start,
                            HhDatum.start_date <= period_finish,
                            HhDatum.status == 'A').one()[0] / 48
                elif meter_type == 'unmetered':
                    year_seconds = (
                        year_finish - year_start).total_seconds() + 60 * 30
                    period_seconds = (
                        period_finish - period_start).total_seconds() + 60 * 30

                    total_kwh[meter_type] += era.imp_sc * period_seconds / \
                        year_seconds

                    normal_days[meter_type] += period_seconds / (60 * 60 * 24)

            # for full year 183
            total_normal_days = sum(normal_days.values())
            total_max_normal_days = sum(max_normal_days.values())
            is_normal = total_normal_days / total_max_normal_days >= 183 / 365

            w.writerow(
                [
                    supply.id, hh_format(year_start), hh_format(year_finish),
                    mpan_core, site.code, site.name, hh_format(supply_from),
                    hh_format(supply_to), breakdown] +
                [
                    normal_days[t] for t in meter_types] + [
                    max_normal_days[t] for t in meter_types] + [
                    total_normal_days, total_max_normal_days,
                    "Actual" if is_normal else "Estimated"] +
                [total_kwh[t] for t in meter_types] +
                [filled_kwh[t] for t in ('hh', 'amr')] +
                [sum(total_kwh.values()) + sum(filled_kwh.values()), ''])

            # avoid a long running transaction
            sess.rollback()
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        f.write("Problem " + msg)
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int('year')
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None
    user = g.user
    threading.Thread(target=content, args=(year, supply_id, user)).start()
    return chellow_redirect("/downloads", 303)
