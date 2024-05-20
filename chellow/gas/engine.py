from collections import defaultdict
from datetime import timedelta
from itertools import combinations, count
from math import log10
from types import MappingProxyType

from dateutil.relativedelta import relativedelta

from sqlalchemy import Float, cast, or_, select
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from zish import dumps, loads

import chellow.bank_holidays
from chellow.e.computer import hh_rate
from chellow.models import (
    BillType,
    Contract,
    GBill,
    GContract,
    GEra,
    GRateScript,
    GReadType,
    GRegisterRead,
)
from chellow.utils import (
    HH,
    PropDict,
    hh_after,
    hh_before,
    hh_max,
    hh_min,
    hh_range,
    to_ct,
    utc_datetime,
    utc_datetime_now,
)


def get_times(sess, caches, start_date, finish_date, forecast_date):
    times_cache = get_g_engine_cache(caches, "times")
    try:
        s_cache = times_cache[start_date]
    except KeyError:
        s_cache = times_cache[start_date] = {}

    try:
        f_cache = s_cache[finish_date]
    except KeyError:
        f_cache = s_cache[finish_date] = {}

    try:
        return f_cache[forecast_date]
    except KeyError:
        if start_date > finish_date:
            raise BadRequest("The start date is after the finish date.")
        times_dict = defaultdict(int)
        dt = finish_date
        years_back = 0
        while dt > forecast_date:
            dt -= relativedelta(years=1)
            years_back += 1

        times_dict["history-finish"] = dt
        times_dict["history-start"] = dt - (finish_date - start_date)

        times_dict["years-back"] = years_back

        f_cache[forecast_date] = times_dict
        return times_dict


def get_g_engine_cache(caches, name):
    try:
        return caches["g_engine"][name]
    except KeyError:
        caches["g_engine"] = defaultdict(dict)
        return caches["g_engine"][name]


def g_contract_func(caches, contract, func_name):
    try:
        ns = caches["g_engine"]["funcs"][contract.id]
    except KeyError:
        try:
            contr_func_cache = caches["g_engine"]["funcs"]
        except KeyError:
            contr_func_cache = get_g_engine_cache(caches, "funcs")

        try:
            ns = contr_func_cache[contract.id]
        except KeyError:
            ns = {"db_id": contract.id, "properties": contract.make_properties()}
            exec(contract.charge_script, ns)
            contr_func_cache[contract.id] = ns

    return ns.get(func_name, None)


def forecast_date():
    now = utc_datetime_now()
    return utc_datetime(now.year, now.month, 1)


def get_data_sources(ds, start_date, finish_date, forecast_date=None):
    if forecast_date is None:
        forecast_date = ds.forecast_date

    if (
        ds.start_date == start_date
        and ds.finish_date == finish_date
        and forecast_date == ds.forecast_date
    ):
        yield ds
    else:
        for g_era in ds.sess.query(GEra).filter(
            GEra.g_supply == ds.g_supply,
            GEra.start_date <= finish_date,
            or_(GEra.finish_date == null(), GEra.finish_date >= start_date),
        ):
            chunk_start = hh_max(g_era.start_date, start_date)
            chunk_finish = hh_min(g_era.finish_date, finish_date)

            ds = GDataSource(
                ds.sess,
                chunk_start,
                chunk_finish,
                forecast_date,
                g_era,
                ds.caches,
                ds.g_bill,
            )
            yield ds


def datum_range(sess, caches, years_back, start_date, finish_date):
    try:
        return caches["g_engine"]["datum"][years_back][start_date][finish_date]
    except KeyError:
        try:
            g_engine_cache = caches["g_engine"]
        except KeyError:
            g_engine_cache = caches["g_engine"] = {}

        try:
            d_cache_datum = g_engine_cache["datum"]
        except KeyError:
            d_cache_datum = g_engine_cache["datum"] = {}

        try:
            d_cache_years = d_cache_datum[years_back]
        except KeyError:
            d_cache_years = d_cache_datum[years_back] = {}

        try:
            d_cache = d_cache_years[start_date]
        except KeyError:
            d_cache = d_cache_years[start_date] = {}

        datum_list = []
        bank_holidays_id = Contract.get_non_core_by_name(sess, "bank_holidays").id
        for dt in hh_range(caches, start_date, finish_date):
            hist_date = dt - relativedelta(years=years_back)
            ct_dt = to_ct(dt)

            utc_is_month_end = (dt + HH).day == 1 and dt.day != 1
            ct_is_month_end = (ct_dt + HH).day == 1 and ct_dt.day != 1

            utc_decimal_hour = dt.hour + dt.minute / 60
            ct_decimal_hour = ct_dt.hour + ct_dt.minute / 60

            bhs = hh_rate(sess, caches, bank_holidays_id, dt)["bank_holidays"]

            bank_holidays = [b[5:] for b in bhs]
            utc_is_bank_holiday = dt.strftime("%m-%d") in bank_holidays
            ct_is_bank_holiday = ct_dt.strftime("%m-%d") in bank_holidays

            datum_list.append(
                MappingProxyType(
                    {
                        "hist_start": hist_date,
                        "start_date": dt,
                        "ct_day": ct_dt.day,
                        "utc_month": dt.month,
                        "utc_day": dt.day,
                        "utc_decimal_hour": utc_decimal_hour,
                        "utc_year": dt.year,
                        "utc_hour": dt.hour,
                        "utc_minute": dt.minute,
                        "ct_year": ct_dt.year,
                        "ct_month": ct_dt.month,
                        "ct_decimal_hour": ct_decimal_hour,
                        "ct_day_of_week": ct_dt.weekday(),
                        "utc_day_of_week": dt.weekday(),
                        "utc_is_bank_holiday": utc_is_bank_holiday,
                        "ct_is_bank_holiday": ct_is_bank_holiday,
                        "utc_is_month_end": utc_is_month_end,
                        "ct_is_month_end": ct_is_month_end,
                        "status": "X",
                        "kwh": 0,
                        "hist_kwh": 0,
                        "unit_code": "M3",
                        "unit_factor": 1,
                        "units_consumed": 0,
                        "correction_factor": 1,
                        "aq": 0,
                        "soq": 0,
                        "calorific_value": 0,
                        "avg_cv": 0,
                    }
                )
            )
        datum_tuple = tuple(datum_list)
        d_cache[finish_date] = datum_tuple
        return datum_tuple


ACTUAL_READ_TYPES = ["A", "C", "S"]
CORRECTION_FACTOR = 1.02264


def g_industry_rates(sess, caches, g_contract_id_or_name, date):
    return g_rates(sess, caches, g_contract_id_or_name, date, True)


def g_supplier_rates(sess, caches, g_contract_id_or_name, date):
    return g_rates(sess, caches, g_contract_id_or_name, date, False)


def g_rates(sess, caches, g_contract_id_or_name, date, is_industry):
    try:
        return caches["g_engine"]["rates"][g_contract_id_or_name][date]
    except KeyError:
        try:
            ccache = caches["g_engine"]
        except KeyError:
            ccache = caches["g_engine"] = {}

        try:
            rss_cache = ccache["rates"]
        except KeyError:
            rss_cache = ccache["rates"] = {}

        try:
            i_cache = rss_cache[is_industry]
        except KeyError:
            i_cache = rss_cache[is_industry] = {}

        try:
            cont_cache = i_cache[g_contract_id_or_name]
        except KeyError:
            cont_cache = i_cache[g_contract_id_or_name] = {}

        try:
            return cont_cache[date]
        except KeyError:
            if isinstance(g_contract_id_or_name, int):
                if is_industry:
                    g_contract = GContract.get_industry_by_id(
                        sess, g_contract_id_or_name
                    )
                else:
                    g_contract = GContract.get_supplier_by_id(
                        sess, g_contract_id_or_name
                    )
            elif isinstance(g_contract_id_or_name, str):
                if is_industry:
                    g_contract = GContract.get_industry_by_name(
                        sess, g_contract_id_or_name
                    )
                else:
                    g_contract = GContract.get_supplier_by_name(
                        sess, g_contract_id_or_name
                    )
            else:
                raise BadRequest("g_contract_id_or_name must be an int or str")

            month_after = date + relativedelta(months=1) + relativedelta(days=1)
            month_before = date - relativedelta(months=1) - relativedelta(days=1)

            rs = sess.execute(
                select(GRateScript).where(
                    GRateScript.g_contract == g_contract,
                    GRateScript.start_date <= date,
                    or_(
                        GRateScript.finish_date == null(),
                        GRateScript.finish_date >= date,
                    ),
                )
            ).scalar_one_or_none()

            if rs is None:
                rs = (
                    sess.execute(
                        select(GRateScript)
                        .where(GRateScript.g_contract == g_contract)
                        .order_by(GRateScript.start_date.desc())
                    )
                    .scalars()
                    .first()
                )
                if date < rs.start_date:
                    cstart = month_before
                    cfinish = min(month_after, rs.start_date - HH)
                else:
                    cstart = max(rs.finish_date + HH, month_before)
                    cfinish = month_after
            else:
                cstart = max(rs.start_date, month_before)
                if rs.finish_date is None:
                    cfinish = month_after
                else:
                    cfinish = min(rs.finish_date, month_after)

            prefix = "industry" if g_contract.is_industry else "supplier"

            vals = PropDict(
                f"the rate script {chellow.utils.url_root}/g/{prefix}_rate_scripts/"
                f"{rs.id} ",
                loads(rs.script),
                [],
            )
            for dt in hh_range(caches, cstart, cfinish):
                if dt not in cont_cache:
                    cont_cache[dt] = vals

            return vals


def _read_generator(sess, g_supply, start, is_forwards, is_prev):
    if is_prev:
        r_typ = GRegisterRead.prev_type
        r_dt = GRegisterRead.prev_date
    else:
        r_typ = GRegisterRead.pres_type
        r_dt = GRegisterRead.pres_date

    q = (
        sess.query(GRegisterRead)
        .join(GBill)
        .join(BillType)
        .join(r_typ)
        .filter(
            GReadType.code.in_(ACTUAL_READ_TYPES),
            GBill.g_supply == g_supply,
            BillType.code != "W",
        )
    )

    if is_forwards:
        q = q.filter(r_dt >= start).order_by(r_dt, GRegisterRead.id)
    else:
        q = q.filter(r_dt < start).order_by(r_dt.desc(), GRegisterRead.id)

    for offset in count():
        r = q.offset(offset).first()
        if r is None:
            break

        if is_prev:
            dt = r.prev_date
            vl = r.prev_value
        else:
            dt = r.pres_date
            vl = r.pres_value

        g_bill = (
            sess.query(GBill)
            .join(BillType)
            .filter(
                GBill.g_supply == g_supply,
                GBill.g_reads.any(),
                GBill.finish_date >= r.g_bill.start_date,
                GBill.start_date <= r.g_bill.finish_date,
                BillType.code != "W",
            )
            .order_by(GBill.issue_date.desc(), BillType.code, GBill.reference.desc())
            .first()
        )

        if g_bill.id != r.g_bill.id:
            continue

        yield {"date": dt, "value": vl, "msn": r.msn}


class GDataSource:
    def __init__(
        self, sess, start_date, finish_date, forecast_date, g_era, caches, g_bill
    ):
        self.sess = sess
        self.caches = caches
        self.forecast_date = forecast_date
        self.start_date = start_date
        self.finish_date = finish_date
        self.bill_hhs = {}
        times = get_times(sess, caches, start_date, finish_date, forecast_date)
        self.years_back = times["years-back"]
        self.history_start = times["history-start"]
        self.history_finish = times["history-finish"]

        self.problem = ""
        self.bill = defaultdict(int, {"problem": ""})
        self.hh_data = []
        self.rate_sets = defaultdict(set)

        self.g_bill = g_bill
        if self.g_bill is not None:
            self.g_bill_start = g_bill.start_date
            self.g_bill_finish = g_bill.finish_date
            self.is_last_g_bill_gen = (
                not self.g_bill_finish < self.start_date
                and not self.g_bill_finish > self.finish_date
            )

        self.g_era = g_era
        self.g_supply = g_era.g_supply
        self.mprn = self.g_supply.mprn
        self.g_exit_zone_code = self.g_supply.g_exit_zone.code
        self.g_ldz_code = self.g_supply.g_exit_zone.g_ldz.code
        self.g_dn_code = self.g_supply.g_exit_zone.g_ldz.g_dn.code
        self.account = g_era.account
        self.g_reading_frequency = g_era.g_reading_frequency
        self.g_reading_frequency_code = self.g_reading_frequency.code
        self.g_contract = g_era.g_contract

        self.consumption_info = ""

        if self.years_back == 0:
            hist_g_eras = [self.g_era]
        else:
            hist_g_eras = (
                sess.query(GEra)
                .filter(
                    GEra.g_supply == self.g_supply,
                    GEra.start_date <= self.history_finish,
                    or_(
                        GEra.finish_date == null(),
                        GEra.finish_date >= self.history_start,
                    ),
                )
                .order_by(GEra.start_date)
                .all()
            )
            if len(hist_g_eras) == 0:
                hist_g_eras = (
                    sess.query(GEra)
                    .filter(GEra.g_supply == self.g_supply)
                    .order_by(GEra.start_date)
                    .limit(1)
                    .all()
                )

        hist_map = {}

        for i, hist_g_era in enumerate(hist_g_eras):
            if self.history_start > hist_g_era.start_date:
                chunk_start = self.history_start
            else:
                if i == 0:
                    chunk_start = self.history_start
                else:
                    chunk_start = hist_g_era.start_date

            chunk_finish = hh_min(hist_g_era.finish_date, self.history_finish)
            if self.g_bill is None:
                self.consumption_info += _no_bill_kwh(
                    sess,
                    caches,
                    self.g_supply,
                    chunk_start,
                    chunk_finish,
                    hist_g_era,
                    self.g_ldz_code,
                    hist_map,
                    forecast_date,
                )
            else:
                _bill_kwh(
                    sess,
                    self.caches,
                    self.g_supply,
                    hist_g_era,
                    chunk_start,
                    chunk_finish,
                    hist_map,
                    self.g_ldz_code,
                )

        for d in datum_range(
            sess, self.caches, self.years_back, start_date, finish_date
        ):
            h = d.copy()
            hist_start = h["hist_start"]
            h.update(hist_map.get(hist_start, {}))
            h["kwh"] = (
                h["units_consumed"]
                * h["unit_factor"]
                * h["correction_factor"]
                * h["calorific_value"]
                / 3.6
            )
            h["ug_rate"] = float(
                g_rates(sess, self.caches, "ug", h["start_date"], True)[
                    "ug_gbp_per_kwh"
                ][self.g_exit_zone_code]
            )
            self.hh_data.append(h)
            self.bill_hhs[d["start_date"]] = {}

    def g_industry_rates(self, g_contract_id_or_name, date):
        return g_industry_rates(self.sess, self.caches, g_contract_id_or_name, date)

    def g_supplier_rates(self, g_contract_id_or_name, date):
        return g_supplier_rates(self.sess, self.caches, g_contract_id_or_name, date)


def _no_bill_kwh(
    sess,
    caches,
    g_supply,
    start,
    finish,
    g_era,
    g_ldz_code,
    hist_map,
    forecast_date,
):
    read_list = []
    pairs = []
    read_keys = set()

    for is_forwards in (False, True):
        prev_reads = iter(_read_generator(sess, g_supply, start, is_forwards, True))
        pres_reads = iter(_read_generator(sess, g_supply, start, is_forwards, False))
        if is_forwards:
            read_list.reverse()

        for read in _make_reads(is_forwards, prev_reads, pres_reads):
            read_key = read["date"], read["msn"]
            if read_key in read_keys:
                continue
            read_keys.add(read_key)

            read_list.append(read)
            pair = _find_pair(is_forwards, read_list)
            if pair is not None:
                pairs.append(pair)
                if not is_forwards or (is_forwards and read_list[-1]["date"] > finish):
                    break

    consumption_info = "read list - \n" + dumps(read_list) + "\n"
    hhs = _find_hhs(sess, caches, g_era, pairs, start, finish, g_ldz_code)
    _set_status(hhs, read_list, forecast_date)
    hist_map.update(hhs)
    return consumption_info + "pairs - \n" + dumps(pairs)


def _find_pair(is_forwards, read_list):
    if len(read_list) < 2:
        return

    if is_forwards:
        back, front = read_list[-2], read_list[-1]
    else:
        back, front = read_list[-1], read_list[-2]

    back_date, back_value = back["date"], back["value"]
    front_date, front_value = front["date"], front["value"]

    if back["msn"] == front["msn"]:
        units = float(front_value - back_value)
        num_hh = (front_date - back_date).total_seconds() / (30 * 60)

        # Clocked?
        if units < 0:
            digits = int(log10(back_value)) + 1
            units += 10**digits

        return {"start-date": back_date, "units": units / num_hh}


def _bill_kwh(
    sess, caches, g_supply, hist_g_era, chunk_start, chunk_finish, hist_map, g_ldz_code
):
    cf = float(hist_g_era.correction_factor)
    aq = float(hist_g_era.aq)
    soq = float(hist_g_era.soq)
    g_unit = hist_g_era.g_unit
    unit_code, unit_factor = g_unit.code, float(g_unit.factor)

    for hh_date in hh_range(caches, chunk_start, chunk_finish):
        cv, avg_cv = find_cv(sess, caches, hh_date, g_ldz_code)
        hist_map[hh_date] = {
            "unit_code": unit_code,
            "unit_factor": unit_factor,
            "correction_factor": cf,
            "aq": aq,
            "soq": soq,
            "calorific_value": cv,
            "avg_cv": avg_cv,
        }

    g_bills = dict(
        (b.id, b)
        for b in sess.query(GBill)
        .filter(
            GBill.g_supply == g_supply,
            GBill.start_date <= chunk_finish,
            GBill.finish_date >= chunk_start,
        )
        .order_by(GBill.issue_date.desc(), GBill.start_date)
    )
    while True:
        to_del = None
        for a, b in combinations(g_bills.values(), 2):
            if all(
                (
                    a.start_date == b.start_date,
                    a.finish_date == b.finish_date,
                    a.kwh == -1 * b.kwh,
                    a.net == -1 * b.net,
                    a.vat == -1 * b.vat,
                    a.gross == -1 * b.gross,
                )
            ):
                to_del = (a.id, b.id)
                break
        if to_del is None:
            break
        else:
            for k in to_del:
                del g_bills[k]

    for _, g_bill in sorted(g_bills.items()):
        units_consumed = 0
        for prev_value, pres_value in sess.query(
            cast(GRegisterRead.prev_value, Float), cast(GRegisterRead.pres_value, Float)
        ).filter(GRegisterRead.g_bill == g_bill):
            units_diff = pres_value - prev_value
            if units_diff < 0:
                total_units = 10 ** len(str(int(prev_value)))
                c_units = total_units - prev_value + pres_value
                if c_units < abs(units_diff):
                    units_diff = c_units

            units_consumed += units_diff

        bill_s = (
            g_bill.finish_date - g_bill.start_date + timedelta(minutes=30)
        ).total_seconds()
        hh_units_consumed = units_consumed / (bill_s / (60 * 30))

        block_start = hh_max(g_bill.start_date, chunk_start)
        block_finish = hh_min(g_bill.finish_date, chunk_finish)
        for hh_date in hh_range(caches, block_start, block_finish):
            hist_map[hh_date]["units_consumed"] = hh_units_consumed


def find_cv(sess, caches, dt, g_ldz_code):
    cvs = g_rates(sess, caches, "cv", dt, True)["cvs"][g_ldz_code]
    ct = to_ct(dt)
    try:
        cv_props = cvs[ct.day]
    except KeyError:
        cv_props = sorted(cvs.items())[-1][1]

    cv = float(cv_props["cv"])

    try:
        avg_cv = caches["g_engine"]["avg_cvs"][g_ldz_code][ct.year][ct.month]
    except KeyError:
        try:
            gec = caches["g_engine"]
        except KeyError:
            gec = caches["g_engine"] = {}

        try:
            avg_cache = gec["avg_cvs"]
        except KeyError:
            avg_cache = gec["avg_cvs"] = {}

        try:
            avg_cvs_cache = avg_cache[g_ldz_code]
        except KeyError:
            avg_cvs_cache = avg_cache[g_ldz_code] = {}

        try:
            year_cache = avg_cvs_cache[ct.year]
        except KeyError:
            year_cache = avg_cvs_cache[ct.year] = {}

        try:
            avg_cv = year_cache[ct.month]
        except KeyError:
            cv_list = [float(v["cv"]) for v in cvs.values()]
            avg_cv = year_cache[ct.month] = sum(cv_list) / len(cv_list)
    return cv, avg_cv


def _find_hhs(sess, caches, hist_g_era, pairs, chunk_start, chunk_finish, g_ldz_code):
    hhs = {}
    if len(pairs) == 0:
        pairs.append({"start-date": chunk_start, "units": 0})

    # set finish dates
    for i in range(1, len(pairs)):
        pairs[i - 1]["finish-date"] = pairs[i]["start-date"] - HH
    pairs[-1]["finish-date"] = None

    # stretch
    if hh_after(pairs[0]["start-date"], chunk_start):
        pairs[0]["start-date"] = chunk_start

    # chop
    if hh_before(pairs[0]["finish-date"], chunk_start):
        del pairs[0]
    if hh_after(pairs[-1]["start-date"], chunk_finish):
        del pairs[-1]

    # squash
    if hh_before(pairs[0]["start-date"], chunk_start):
        pairs[0]["start-date"] = chunk_start
    if hh_after(pairs[-1]["finish-date"], chunk_finish):
        pairs[-1]["finish-date"] = chunk_finish

    cf = float(hist_g_era.correction_factor)
    aq = float(hist_g_era.aq)
    soq = float(hist_g_era.soq)
    g_unit = hist_g_era.g_unit
    unit_code, unit_factor = g_unit.code, float(g_unit.factor)
    for pair in pairs:
        units = pair["units"]
        for hh_date in hh_range(caches, pair["start-date"], pair["finish-date"]):
            cv, avg_cv = find_cv(sess, caches, hh_date, g_ldz_code)

            hhs[hh_date] = {
                "unit_code": unit_code,
                "unit_factor": unit_factor,
                "units_consumed": units,
                "correction_factor": cf,
                "aq": aq,
                "soq": soq,
                "calorific_value": cv,
                "avg_cv": avg_cv,
            }
    return hhs


def _make_reads(forwards, prev_reads, pres_reads):
    prev_read = next(prev_reads, None)
    pres_read = next(pres_reads, None)
    while prev_read is not None or pres_read is not None:
        if prev_read is None:
            yield pres_read
            pres_read = next(pres_reads, None)

        elif pres_read is None:
            yield prev_read
            prev_read = next(prev_reads, None)

        else:
            if (forwards and prev_read["date"] < pres_read["date"]) or (
                not forwards and prev_read["date"] >= pres_read["date"]
            ):
                yield prev_read
                prev_read = next(prev_reads, None)
            else:
                yield pres_read
                pres_read = next(pres_reads, None)


def _set_status(hhs, read_list, forecast_date):
    THRESHOLD = 31 * 48 * 30 * 60
    rl = [r for r in read_list if r["date"] <= forecast_date]
    for k, v in hhs.items():
        try:
            periods = (abs(r["date"] - k).total_seconds() for r in rl)
            next(p for p in periods if p <= THRESHOLD)
            v["status"] = "A"
        except StopIteration:
            v["status"] = "E"
