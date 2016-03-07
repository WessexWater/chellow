from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
import pytz
from sqlalchemy import func
from sqlalchemy.sql.expression import true
import chellow.computer
from chellow.utils import hh_format, HH
from werkzeug.exceptions import BadRequest
from chellow.models import HhDatum, Channel, Era


BANDS = ['red', 'amber', 'green']

KEYS = dict(
    (
        band, {
            'kwh': 'duos-' + band + '-kwh',
            'tariff-rate': band + '-gbp-per-kwh',
            'bill-rate': 'duos-' + band + '-rate',
            'gbp': 'duos-' + band + '-gbp'}) for band in BANDS)

VL_LOOKUP = {
    'HV': {True: 'hv', False: 'hv'},
    'LV': {True: 'lv-sub', False: 'lv-net'}}


def datum_beginning_22(ds, hh):
    bill = ds.supplier_bill

    tariff = ds.hh_rate(
        ds.dno_contract.id, hh['start-date'], 'tariffs')[ds.llfc_code]
    lafs = ds.hh_rate(
        ds.dno_contract.id, hh['start-date'],
        'lafs')[VL_LOOKUP[ds.voltage_level_code][ds.is_substation]]

    if ds.is_import:
        try:
            day_rate = tariff['day-gbp-per-kwh']
        except KeyError:
            raise BadRequest(
                "For the DNO " + ds.dno_contract.name +
                " and the rate script at date " +
                hh_format(hh['start-date']) +
                " and the rate 'tariffs' with the LLFC code " + ds.llfc_code +
                " the key 'day-gbp-per-kwh' can't be found.")
        night_rate = tariff['night-gbp-per-kwh']
        if 6 < hh['ct-decimal-hour'] <= 23:
            bill['duos-day-kwh'] += hh['msp-kwh']
            bill['duos-day-gbp'] += hh['msp-kwh'] * day_rate
        else:
            bill['duos-night-kwh'] += hh['msp-kwh']
            bill['duos-night-gbp'] += hh['msp-kwh'] * night_rate

    if 23 < hh['ct-decimal-hour'] <= 6:
        slot_name = 'night'
    elif hh['ct-day-of-week'] < 5 and (
            hh['ct-month'] > 10 or hh['ct-month'] < 3):
        if 15.5 < hh['ct-decimal-hour'] < 18:
            slot_name = 'winter-weekday-peak'
        elif 6 < hh['ct-decimal-hour'] < 15:
            slot_name = 'winter-weekday-day'
        else:
            slot_name = 'other'
    else:
        slot_name = 'other'
    hh['laf'] = lafs[slot_name]
    hh['gsp-kwh'] = hh['laf'] * hh['msp-kwh']
    hh['gsp-kw'] = hh['gsp-kwh'] * 2


def hh_time_beginning_22(ds, hh):
    bill = ds.supplier_bill
    if hh['utc-is-month-end']:
        tariff = ds.hh_rate(
            ds.dno_contract.id, hh['start-date'], 'tariffs')[ds.llfc_code]
        reactive_rate = tariff['reactive-gbp-per-kvarh']
        bill['duos-reactive-rate'] = reactive_rate

        days_in_month = hh['utc-day']

        if not ds.is_displaced:
            md_kva = max(
                (datum['msp-kw'] ** 2 + datum['imp-msp-kvar'] ** 2) **
                0.5 for datum in ds.hh_data)

            bill['duos-availability-kva'] = ds.sc
            bill['duos-excess-availability-kva'] = max(md_kva - ds.sc, 0)
            for prefix in ['', 'excess-']:
                tariff_key = prefix + 'gbp-per-kva-per-day'
                if tariff_key in tariff:
                    rate_key = 'duos-' + prefix + 'availability-rate'
                    bill[rate_key] = tariff[tariff_key]
                    bill['duos-' + prefix + 'availability-days'] = \
                        days_in_month
                    bill['duos-' + prefix + 'availability-gbp'] = \
                        bill[rate_key] * \
                        bill['duos-' + prefix + 'availability-kva'] * \
                        bill['duos-' + prefix + 'availability-days']

        month_imp_kvarh = sum(h['imp-msp-kvarh'] for h in ds.hh_data)
        month_kwh = sum(h['msp-kwh'] for h in ds.hh_data)

        if month_kwh is None:
            month_kwh = 0

        bill['duos-reactive-gbp'] += max(0, month_imp_kvarh - month_kwh / 2) \
            * reactive_rate


def datum_beginning_20(ds, hh):
    bill = ds.supplier_bill

    tariff = None
    for k, tf in ds.hh_rate(
            ds.dno_contract.id, hh['start-date'], 'tariffs').items():
        if ds.llfc_code in [cd.strip() for cd in k.split(',')]:
            tariff = tf

    if tariff is None:
        raise BadRequest(
            "The tariff for the LLFC " + ds.llfc_code +
            " cannot be found for the DNO 20 at " +
            hh_format(hh['start-date']) + ".")

    lafs = ds.hh_rate(
        ds.dno_contract.id, hh['start-date'],
        'lafs')[ds.voltage_level_code.lower()]

    day_rate = tariff['day-gbp-per-kwh']

    if 'night-gbp-per-kwh' in tariff:
        night_rate = tariff['night-gbp-per-kwh']
        if 0 < hh['ct-decimal-hour'] <= 7:
            bill['duos-night-kwh'] += hh['msp-kwh']
            bill['duos-night-gbp'] += hh['msp-kwh'] * night_rate
        else:
            bill['duos-day-kwh'] += hh['msp-kwh']
            bill['duos-day-gbp'] += hh['msp-kwh'] * day_rate
    else:
        bill['duos-day-kwh'] += hh['msp-kwh']
        bill['duos-day-gbp'] += hh['msp-kwh'] * day_rate

    if 0 < hh['ct-decimal-hour'] <= 7:
        slot_name = 'night'
    elif hh['ct-day-of-week'] < 5 and \
            16 < hh['ct-decimal-hour'] <= 19 and \
            (hh['ct-month'] > 10 or hh['ct-month'] < 3):
        slot_name = 'peak'
    elif 7 > hh['ct-day-of-week'] > 1 and (
            7 < hh['ct-decimal-hour'] < 15 or
            18.5 < hh['ct-decimal-hour'] < 19) and \
            (hh['ct-month'] > 11 or hh['ct-month'] < 4):
        slot_name = 'winter-weekday'
    else:
        slot_name = 'other'
    hh['laf'] = lafs[slot_name]
    hh['gsp-kwh'] = hh['laf'] * hh['msp-kwh']
    hh['gsp-kw'] = hh['gsp-kwh'] * 2


def hh_time_beginning_20(ds, hh):
    bill = ds.supplier_bill
    if hh['utc-is-month-end']:
        tariff = None
        for k, tf in ds.hh_rate(
                ds.dno_contract.id, hh['start-date'], 'tariffs').items():
            if ds.llfc_code in map(str.strip, k.split(',')):
                tariff = tf
                break
        if tariff is None:
            raise BadRequest(
                "The tariff for the LLFC " + ds.llfc_code +
                " cannot be found for the DNO 20 at " +
                hh_format(hh['start-date']) + ".")
        if not ds.is_displaced:
            year_md_kva_095 = year_md_095(ds, ds.finish_date)

            bill['duos-excess-availability-kva'] = max(
                year_md_kva_095 - ds.sc, 0)
            billed_avail = max(ds.sc, year_md_kva_095)
            bill['duos-availability-kva'] = ds.sc

            for threshold, block in [
                    (15, 15), (100, 5), (250, 10), (500, 25), (1000, 50),
                    (None, 100)]:
                if threshold is None or billed_avail < threshold:
                    if billed_avail % block > 0:
                        billed_avail = (int(billed_avail / block) + 1) * block
                    break
            le_200_avail_rate = tariff['capacity-<=200-gbp-per-kva-per-month']

            bill['duos-availability-gbp'] += min(200, billed_avail) * \
                le_200_avail_rate

            if billed_avail > 200:
                gt_200_avail_rate = \
                    tariff['capacity->200-gbp-per-kva-per-month']
                bill['duos-availability-gbp'] += (billed_avail - 200) * \
                    gt_200_avail_rate

        if 'fixed-gbp-per-month' in tariff:
            bill['duos-standing-gbp'] += tariff['fixed-gbp-per-month']
        else:
            bill['duos-standing-gbp'] += tariff['fixed-gbp-per-day'] * \
                hh['utc-day']


def year_md_095(data_source, finish):
    if data_source.site is None:
        return year_md_095_supply(data_source, finish)
    else:
        return year_md_095_site(data_source, finish)


def year_md_095_supply(ds, finish):
    supply = ds.supply
    sess = ds.sess
    md_kva = 0
    month_finish = finish - relativedelta(months=11)

    while not month_finish > finish:
        month_start = month_finish - relativedelta(months=1) + HH
        month_kwh_result = sess.query(
            func.sum(HhDatum.value),
            func.max(HhDatum.value)).join(Channel).join(Era).filter(
            Era.supply == supply, HhDatum.start_date >= month_start,
            HhDatum.start_date <= month_finish,
            Channel.channel_type == 'ACTIVE',
            Channel.imp_related == true()).one()

        if month_kwh_result[0] is not None:
            month_md_kw = float(month_kwh_result[1]) * 2
            month_kwh = float(month_kwh_result[0])
            month_kvarh = sess.query(
                func.sum(HhDatum.value)).join(Channel).join(Era).filter(
                Era.supply == supply, HhDatum.start_date >= month_start,
                HhDatum.start_date <= month_finish,
                Channel.channel_type == 'REACTIVE_IMP',
                Channel.imp_related == true()).one()[0]
            if month_kvarh is None:
                pf = 0.95
            else:
                month_kvarh = float(month_kvarh)
                if month_kwh == 0 and month_kvarh == 0:
                    pf = 1
                else:
                    pf = month_kwh / (month_kwh ** 2 + month_kvarh ** 2) ** 0.5
            month_kva = month_md_kw / pf
            md_kva = max(md_kva, month_kva)
        month_finish += relativedelta(months=1)
    return md_kva


def year_md_095_site(data_source, finish, pw):
    md_kva = 0
    month_finish = finish - relativedelta(months=12)

    while not month_finish > finish:
        month_start = month_finish - relativedelta(months=1) + HH
        month_data = {'start': month_start, 'finish': month_finish}
        data_source.sum_md(month_data, pw)
        if month_data['sum-kwh'] is None:
            month_md_kw = 0
            month_kwh = 0
        else:
            month_md_kw = month_data['md-kw']
            month_kwh = month_data['sum-kwh']

        data_source.sum_md(month_data, pw, False)
        if month_data['sum-kvarh'] is not None:
            month_kvarh = month_data['sum-kvarh']

        if month_kvarh == 0:
            month_kva = month_md_kw / 0.95
        else:
            if month_kwh == 0 and month_kvarh == 0:
                pf = 1
            else:
                pf = month_kwh / (month_kwh ** 2 + month_kvarh ** 2) ** 0.5
            month_kva = month_md_kw / pf
        md_kva = max(md_kva, month_kva)
        month_finish += relativedelta(months=1)
    return md_kva, ''


def datum_beginning_14(ds, hh):
    bill = ds.supplier_bill

    tariffs = ds.hh_rate(
        ds.dno_contract.id, hh['start-date'], 'tariffs')[ds.llfc_code]
    if 0 < hh['ct-decimal-hour'] <= 7:
        bill['duos-night-kwh'] += hh['msp-kwh']
        bill['duos-night-gbp'] += hh['msp-kwh'] * tariffs['night-gbp-per-kwh']
    else:
        bill['duos-day-kwh'] += hh['msp-kwh']
        bill['duos-day-gbp'] += hh['msp-kwh'] * tariffs['day-gbp-per-kwh']

    if 0 < hh['ct-decimal-hour'] <= 7:
        slot = 'night'
    elif hh['ct-day-of-week'] < 5 and hh['ct-decimal-hour'] > 15.5 and \
            hh['ct-decimal-hour'] < 19 and (
                hh['ct-month'] > 11 or hh['ct-month'] < 4):
        slot = 'winter-weekday-peak'
    elif hh['ct-day-of-week'] < 5 and (
            7 <= hh['ct-decimal-hour'] < 16 or
            18 < hh['ct-decimal-hour'] < 20) and \
            (hh['ct-month'] > 11 or hh['ct-month'] < 4):
        slot = 'winter-weekday-day'
    else:
        slot = 'other'

    hh['laf'] = ds.hh_rate(
        ds.dno_contract.id, hh['start-date'],
        'lafs')[ds.voltage_level_code.lower()][slot]
    hh['gsp-kwh'] = hh['msp-kwh'] * hh['laf']
    hh['gsp-kw'] = hh['gsp-kwh'] * 2


def hh_time_beginning_14(ds, hh):
    bill = ds.supplier_bill
    if hh['utc-decimal-hour'] == 0:
        tariff = ds.hh_rate(
            ds.dno_contract.id, hh['start-date'], 'tariffs')[ds.llfc_code]
        bill['duos-standing-gbp'] += tariff['fixed-gbp-per-day']

    if hh['utc-is-month-end']:
        availability = ds.sc
        tariff = ds.hh_rate(
            ds.dno_contract.id, hh['start-date'], 'tariffs')[ds.llfc_code]
        reactive_rate = tariff['reactive-gbp-per-kvarh']
        bill['duos-reactive-rate'] = reactive_rate
        bill['duos-reactive-gbp'] = max(
            0, sum(h['imp-msp-kvarh'] for h in ds.hh_data) -
            sum(h['msp-kwh'] for h in ds.hh_data) / 3) * reactive_rate
        if not ds.is_displaced:
            availability_rate = tariff['availability-gbp-per-kva-per-day']
            bill['duos-availability-rate'] = availability_rate
            md_kva = max(
                (
                    datum['msp-kw'] ** 2 + (
                        datum['imp-msp-kvar'] + datum['exp-msp-kvar']) ** 2) **
                0.5 for datum in ds.hh_data)

            billed_avail = max(availability, md_kva)
            bill['duos-availability-gbp'] += availability_rate * billed_avail
            bill['duos-availability-agreed-kva'] = ds.sc
            bill['duos-availability-billed-kva'] = billed_avail


def datum_2010_04_01(ds, hh):
    bill = ds.supplier_bill
    dno_cache = ds.caches['dno'][ds.dno_code]

    try:
        laf_cache = dno_cache['lafs']
    except KeyError:
        dno_cache['lafs'] = {}
        laf_cache = dno_cache['lafs']

    try:
        laf_cache_v = laf_cache[ds.voltage_level_code]
    except KeyError:
        laf_cache[ds.voltage_level_code] = {}
        laf_cache_v = laf_cache[ds.voltage_level_code]

    try:
        lafs = laf_cache_v[ds.is_substation]
    except KeyError:
        laf_cache_v[ds.is_substation] = {}
        lafs = laf_cache_v[ds.is_substation]

    try:
        laf = lafs[hh['start-date']]
    except KeyError:
        vl_key = ds.voltage_level_code.lower() + \
            ('-sub' if ds.is_substation else '-net')
        slot_name = 'other'
        if ds.dno_code == '20':
            if 0 < hh['ct-decimal-hour'] <= 7:
                slot_name = 'night'
            elif hh['ct-day-of-week'] < 5 and hh['ct-month'] in [11, 12, 1, 2]:
                if 16 <= hh['ct-decimal-hour'] < 19:
                    slot_name = 'peak'
                elif 7 < hh['ct-decimal-hour'] < 20:
                    slot_name = 'winter-weekday'
        elif ds.dno_code in ['14', '22']:
            if 23 < hh['ct-decimal-hour'] or hh['ct-decimal-hour'] <= 6:
                slot_name = 'night'
            elif hh['ct-day-of-week'] < 5 and hh['ct-month'] in [11, 12, 1, 2]:
                if 16 <= hh['ct-decimal-hour'] < 19:
                    slot_name = 'winter-weekday-peak'
                elif hh['ct-decimal-hour'] < 16:
                    slot_name = 'winter-weekday-day'
        else:
            raise BadRequest("Not recognized")

        laf = ds.hh_rate(
            ds.dno_contract.id, hh['start-date'], 'lafs')[vl_key][slot_name]
        lafs[hh['start-date']] = laf

    hh['laf'] = laf
    hh['gsp-kwh'] = laf * hh['msp-kwh']
    hh['gsp-kw'] = hh['gsp-kwh'] * 2

    tariff, band = dno_cache['tariff_bands'][ds.llfc_code][hh['start-date']]

    kvarh = max(max(hh['imp-msp-kvarh'], hh['exp-msp-kvarh']) -
                (0.95 ** -2 - 1) ** 0.5 * hh['msp-kwh'], 0)
    bill['duos-reactive-kvarh'] += kvarh
    rate = tariff['gbp-per-kvarh']
    ds.supplier_rate_sets['duos-reactive-rate'].add(rate)
    bill['duos-reactive-gbp'] += kvarh * rate

    rate = tariff[KEYS[band]['tariff-rate']]
    ds.supplier_rate_sets[KEYS[band]['bill-rate']].add(rate)
    bill[KEYS[band]['kwh']] += hh['msp-kwh']
    bill[KEYS[band]['gbp']] += rate * hh['msp-kwh']


def hh_time_2010_04_01(ds, hh):
    bill = ds.supplier_bill
    dno_cache = ds.caches['dno'][ds.dno_contract.name]
    try:
        tariff_bands_cache = dno_cache['tariff_bands']
    except KeyError:
        dno_cache['tariff_bands'] = {}
        tariff_bands_cache = dno_cache['tariff_bands']

    try:
        tariff_bands = tariff_bands_cache[ds.llfc_code]
    except KeyError:
        tariff_bands_cache[ds.llfc_code] = {}
        tariff_bands = tariff_bands_cache[ds.llfc_code]

    try:
        tariff, band = tariff_bands[hh['start-date']]
    except KeyError:
        tariff = None
        for llfcs, tf in ds.hh_rate(
                ds.dno_contract.id, hh['start-date'], 'tariffs').items():
            if ds.llfc_code in [cd.strip() for cd in llfcs.split(',')]:
                tariff = tf
                break
        if tariff is None:
            raise BadRequest(
                "For the DNO " + ds.dno_code + " and timestamp " +
                hh_format(hh['start-date']) + " the LLFC '" +
                ds.llfc_code + "' can't be found in the 'tariffs' section.")

        band = 'green'
        if ds.dno_code == '14':
            if hh['ct-day-of-week'] < 5:
                if 16 <= hh['ct-decimal-hour'] < 19:
                    band = 'red'
                elif 7 < hh['ct-decimal-hour'] < 21:
                    band = 'amber'
        elif ds.dno_code == '20':
            if hh['ct-day-of-week'] < 5:
                if 16 < hh['ct-decimal-hour'] < 19:
                    band = 'red'
                elif 9 <= hh['ct-decimal-hour'] <= 20:
                    band = 'amber'
        elif ds.dno_code == '22':
            if hh['ct-day-of-week'] > 4:
                if 16 < hh['ct-decimal-hour'] <= 19:
                    band = 'amber'
            else:
                if 17 <= hh['ct-decimal-hour'] < 19:
                    band = 'red'
                elif 7 < hh['ct-decimal-hour'] <= 21:
                    band = 'amber'
        else:
            raise BadRequest("DNO code not recognized.")
        tariff_bands[hh['start-date']] = (tariff, band)

    if hh['ct-decimal-hour'] == 23.5 and not ds.is_displaced:
        bill['duos-fixed-days'] += 1
        rate = tariff['gbp-per-mpan-per-day']
        ds.supplier_rate_sets['duos-fixed-rate'].add(rate)
        bill['duos-fixed-gbp'] += rate

        bill['duos-availability-days'] += 1
        kva = ds.sc
        ds.supplier_rate_sets['duos-availability-kva'].add(kva)
        rate = tariff['gbp-per-kva-per-day']
        ds.supplier_rate_sets['duos-availability-rate'].add(rate)
        bill['duos-availability-gbp'] += rate * kva

    if hh['ct-is-month-end'] and not ds.is_displaced:
        month_to = hh['start-date']
        month_from = month_to - relativedelta(months=1) + HH
        md_kva = 0
        days_in_month = 0
        for dsc in chellow.computer.get_data_sources(ds, month_from, month_to):
            for datum in dsc.hh_data:
                md_kva = max(
                    md_kva, (
                        datum['msp-kw'] ** 2 + max(
                            datum['imp-msp-kvar'], datum['exp-msp-kvar']) **
                        2) ** 0.5)
                if datum['utc-decimal-hour'] == 0:
                    days_in_month += 1

        excess_kva = max(md_kva - ds.sc, 0)

        if 'excess-gbp-per-kva-per-day' in tariff:
            rate = tariff['excess-gbp-per-kva-per-day']
            ds.supplier_rate_sets['duos-excess-availability-kva'].add(
                excess_kva)
            rate = tariff['excess-gbp-per-kva-per-day']
            ds.supplier_rate_sets['duos-excess-availability-rate'].add(rate)
            bill['duos-excess-availability-days'] += days_in_month
            bill['duos-excess-availability-gbp'] += rate * excess_kva * \
                days_in_month

CUTOFF_DATE = Datetime(2010, 4, 1, tzinfo=pytz.utc)


def duos_vb(ds):
    try:
        dno_caches = ds.caches['dno']
    except KeyError:
        ds.caches['dno'] = {}
        dno_caches = ds.caches['dno']

    try:
        dno_cache = dno_caches[ds.dno_contract.name]
    except KeyError:
        dno_caches[ds.dno_contract.name] = {}
        dno_cache = dno_caches[ds.dno_contract.name]

    try:
        time_func_cache = dno_cache['time_funcs']
    except KeyError:
        dno_cache['time_funcs'] = {}
        time_func_cache = dno_cache['time_funcs']

    for hh in ds.hh_data:
        try:
            time_func_cache[hh['start-date']](ds, hh)
        except KeyError:
            if hh['start-date'] < CUTOFF_DATE:
                if ds.dno_code == '14':
                    time_func = hh_time_beginning_14
                elif ds.dno_code == '20':
                    time_func = hh_time_beginning_20
                elif ds.dno_code == '22':
                    time_func = hh_time_beginning_22
                else:
                    raise BadRequest('Not recognized')

            else:
                time_func = hh_time_2010_04_01
            time_func_cache[hh['start-date']] = time_func
            time_func(ds, hh)

    try:
        data_func_cache = dno_cache['data_funcs']
    except KeyError:
        dno_cache['data_funcs'] = {}
        data_func_cache = dno_cache['data_funcs']

    for hh in ds.hh_data:
        try:
            data_func_cache[hh['start-date']](ds, hh)
        except KeyError:
            if hh['start-date'] < CUTOFF_DATE:
                if ds.dno_code == '14':
                    data_func = datum_beginning_14
                elif ds.dno_code == '20':
                    data_func = datum_beginning_20
                elif ds.dno_code == '22':
                    data_func = datum_beginning_22
                else:
                    raise BadRequest('Not recognized')
            else:
                data_func = datum_2010_04_01
            data_func_cache[hh['start-date']] = data_func
            data_func(ds, hh)
