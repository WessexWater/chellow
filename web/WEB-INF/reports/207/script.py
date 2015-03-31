import traceback
from net.sf.chellow.monad import Monad
import pytz
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, func, Float, cast
from sqlalchemy.sql.expression import null, true
import math
import utils
import db

Monad.getUtils()['impt'](globals(), 'utils', 'db')
HH, totalseconds, hh_after = utils.HH, utils.totalseconds, utils.hh_after
hh_format = utils.hh_format
Supply, RegisterRead, Bill = db.Supply, db.RegisterRead, db.Bill
BillType, Era, Site, SiteEra = db.BillType, db.Era, db.Site, db.SiteEra
HhDatum, Channel, Source = db.HhDatum, db.Channel, db.Source
ReadType = db.ReadType
inv, template = globals()['inv'], globals()['template']

year = inv.getInteger('year')
if inv.hasParameter('supply_id'):
    supply_id = inv.getLong('supply_id')
else:
    supply_id = None


def content():
    sess = None
    try:
        sess = db.session()

        ACTUAL_READ_TYPES = ['N', 'N3', 'C', 'X', 'CP']
        yield ','.join(
            (
                'Chellow Supply Id', 'MPAN Core', 'Site Id', 'Site Name',
                'From', 'To', 'NHH Breakdown', 'Actual HH Normal Days',
                'Actual AMR Normal Days', 'Actual NHH Normal Days',
                'Actual Unmetered Normal Days', 'Max HH Normal Days',
                'Max AMR Normal Days', 'Max NHH Normal Days',
                'Max Unmetered Normal Days', 'Total Actual Normal Days',
                'Total Max Normal Days', 'Data Type', 'HH kWh', 'AMR kWh',
                'NHH kWh', 'Unmetered kwh', 'HH Filled kWh', 'AMR Filled kWh',
                'Total kWh', 'Note')) + '\n'

        year_start = datetime.datetime(year, 4, 1, tzinfo=pytz.utc)
        year_finish = year_start + relativedelta(years=1) - HH

        supplies = sess.query(Supply).join(Era).join(Source).filter(
            Source.code.in_(('net', 'gen-net')), Era.imp_mpan_core != null(),
            Era.start_date <= year_finish, or_(
                Era.finish_date == null(),
                Era.finish_date >= year_start)).distinct().order_by(Supply.id)
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            supplies = supplies.filter(Supply.id == supply.id)

        meter_types = ['hh', 'amr', 'nhh', 'unmetered']

        for supply in supplies:
            total_kwh = dict([(mtype, 0) for mtype in meter_types])
            filled_kwh = dict([(mtype, 0) for mtype in ('hh', 'amr')])
            normal_days = dict([(mtype, 0) for mtype in meter_types])
            max_normal_days = dict([(mtype, 0) for mtype in meter_types])

            breakdown = ''

            for era in sess.query(Era).filter(
                    Era.supply_id == supply.id, Era.start_date <= year_finish,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= year_start)):
                yield ' '

                meter_type = era.make_meter_category()

                era_start = era.start_date
                period_start = era_start \
                    if era_start > year_start else year_start

                era_finish = era.finish_date
                if hh_after(era_finish, year_finish):
                    period_finish = year_finish
                else:
                    period_finish = era_finish

                max_normal_days[meter_type] += float(
                    totalseconds(period_finish - period_start) + 60 * 30) / \
                    (60 * 60 * 24)

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
                            Bill.supply_id == supply.id,
                            RegisterRead.present_date < period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.present_date.desc()))
                    prior_prev_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType)
                        .join(RegisterRead.previous_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply_id == supply.id,
                            RegisterRead.previous_date < period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.previous_date.desc()))
                    next_pres_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType)
                        .join(RegisterRead.present_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply_id == supply.id,
                            RegisterRead.present_date >= period_start,
                            BillType.code != 'W').order_by(
                            RegisterRead.present_date))
                    next_prev_reads = iter(
                        sess.query(RegisterRead).join(Bill).join(BillType).
                        join(RegisterRead.previous_type).filter(
                            RegisterRead.units == 0,
                            ReadType.code.in_(ACTUAL_READ_TYPES),
                            Bill.supply_id == supply.id,
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
                                    pres_read = pres_reads.next()
                                except StopIteration:
                                    break

                                pres_date = pres_read.present_date
                                pres_msn = pres_read.msn
                                read_key = '_'.join([str(pres_date), pres_msn])
                                if read_key in read_keys:
                                    continue

                                pres_bill = sess.query(Bill). \
                                    join(RegisterRead).join(BillType).filter(
                                        Bill.supply_id == supply.id,
                                        Bill.finish_date >=
                                        pres_read.present_date,
                                        Bill.start_date <=
                                        pres_read.present_date,
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
                                        RegisterRead.bill_id == pres_bill.id,
                                        RegisterRead.present_date == pres_date,
                                        RegisterRead.msn == pres_msn))

                                prime_pres_read = {
                                    'date': pres_date, 'reads': reads,
                                    'msn': pres_msn}
                                read_keys[read_key] = None

                            while prime_prev_read is None:
                                try:
                                    prev_read = prev_reads.next()
                                except StopIteration:
                                    break

                                prev_date = prev_read.previous_date
                                prev_msn = prev_read.msn
                                read_key = '_'.join([str(prev_date), prev_msn])
                                if read_key in read_keys:
                                    continue

                                prev_bill = sess.query(Bill).join(BillType). \
                                    filter(
                                        Bill.supply_id == supply.id,
                                        Bill.finish_date >=
                                        prev_read.bill.start_date,
                                        Bill.start_date <=
                                        prev_read.bill.start_date,
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
                                    if prime_prev_read['date'] == \
                                            prime_pres_read['date'] or \
                                            prime_pres_read['date'] < \
                                            prime_prev_read['date']:
                                        read_list.append(prime_pres_read)
                                        prime_pres_read = None
                                    else:
                                        read_list.append(prime_prev_read)
                                        prime_prev_read = None
                                else:
                                    if prime_prev_read['date'] == \
                                            prime_pres_read['date'] or \
                                            prime_prev_read['date'] > \
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

                                if aft_read['msn'] == fore_read['msn']:
                                    pair_start_date = aft_read['date'] + HH
                                    pair_finish_date = fore_read['date']

                                    num_hh = float(
                                        totalseconds(
                                            pair_finish_date + HH -
                                            pair_start_date)) / (30 * 60)

                                    tprs = {}
                                    for tpr_code, initial_val in \
                                            aft_read['reads'].iteritems():
                                        if tpr_code in fore_read['reads']:
                                            end_val = fore_read['reads'][
                                                tpr_code]
                                        else:
                                            continue

                                        kwh = end_val - initial_val

                                        if kwh < 0:
                                            digits = int(
                                                math.log10(initial_val)) + 1
                                            kwh = 10 ** digits + kwh

                                        tprs[tpr_code] = float(kwh) / num_hh

                                    pairs.append(
                                        {
                                            'start-date': pair_start_date,
                                            'finish-date': pair_finish_date,
                                            'tprs': tprs})

                                    if len(pairs) > 0 and \
                                            (not is_forwards or (
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
                                if pair_start > period_start:
                                    block_start = pair_start
                                else:
                                    block_start = period_start

                                if pair_finish < period_finish:
                                    block_finish = pair_finish
                                else:
                                    block_finish = period_finish

                                if block_start <= block_finish:
                                    normal_days[meter_type] += float(
                                        totalseconds(
                                            block_finish - block_start) +
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
                        pair_hhs = float(
                            totalseconds(
                                pair['finish-date'] - pair['start-date']) +
                            30 * 60) / (60 * 30)
                        pair['pair_hhs'] = pair_hhs
                        for tpr_code, pair_kwh in pair['tprs'].iteritems():
                            total_kwh[meter_type] += pair_kwh * pair_hhs

                    breakdown += 'pairs - \n' + str(pairs)

                elif meter_type in ('hh', 'amr'):
                    period_kwhs = list(
                        v[0] for v in sess.query(cast(HhDatum.value, Float)).
                        join(Channel).filter(
                            Channel.imp_related == true(),
                            Channel.channel_type == 'ACTIVE',
                            Channel.era == era,
                            HhDatum.start_date >= period_start,
                            HhDatum.start_date <= period_finish))
                    year_kwhs = list(
                        v[0] for v in sess.query(cast(HhDatum.value, Float)).
                        join(Channel).filter(
                            Channel.imp_related == true(),
                            Channel.channel_type == 'ACTIVE',
                            Channel.era == era,
                            HhDatum.start_date >= year_start,
                            HhDatum.start_date <= year_finish))
                    yield ' '

                    period_sum_kwhs = sum(period_kwhs)
                    year_sum_kwhs = sum(year_kwhs)
                    period_len_kwhs = len(period_kwhs)
                    year_len_kwhs = len(year_kwhs)
                    total_kwh[meter_type] += period_sum_kwhs
                    period_hhs = totalseconds(
                        period_finish + HH - period_start) / (60 * 30)
                    if year_len_kwhs > 0:
                        filled_kwh[meter_type] += float(year_sum_kwhs) / \
                            year_len_kwhs * (period_hhs - period_len_kwhs)
                    normal_days[meter_type] += float(
                        sess.query(func.count(HhDatum.value)).join(Channel).
                        filter(
                            Channel.imp_related == true(),
                            Channel.channel_type == 'ACTIVE',
                            Channel.era == era,
                            HhDatum.start_date >= period_start,
                            HhDatum.start_date <= period_finish,
                            HhDatum.status == 'A').one()[0]) / 48
                elif meter_type == 'unmetered':
                    bills = sess.query(Bill).filter(
                        Bill.supply_id == supply.id,
                        Bill.finish_date >= period_start,
                        Bill.start_date <= period_finish)
                    for bill in bills:
                        total_kwh[meter_type] += float(bill.kwh)
                    normal_days[meter_type] += float(
                        totalseconds(
                            period_finish - period_start) +
                        60 * 30) / (60 * 60 * 24)

            # for full year 183
            total_normal_days = sum(normal_days.values())
            total_max_normal_days = sum(max_normal_days.values())
            is_normal = float(
                total_normal_days) / total_max_normal_days >= float(183) / 365

            yield ','.join('"' + str(val) + '"' for val in [
                supply.id, mpan_core, site.code, site.name,
                hh_format(year_start), hh_format(year_finish),
                breakdown] + [normal_days[type] for type in meter_types] + [
                max_normal_days[type] for type in meter_types] + [
                total_normal_days, total_max_normal_days,
                "Actual" if is_normal else "Estimated"] +
                [total_kwh[type] for type in meter_types] +
                [filled_kwh[type] for type in ('hh', 'amr')] +
                [sum(total_kwh.values()) + sum(filled_kwh.values()), '']) + \
                '\n'

            # avoid a long running transaction
            sess.rollback()
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='input.csv')
