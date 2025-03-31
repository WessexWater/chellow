import atexit
import threading
import traceback
from collections import deque
from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

import requests

from werkzeug.exceptions import BadRequest

from zish import loads

from chellow.models import Contract, RateScript, Session
from chellow.utils import (
    HH,
    c_months_u,
    ct_datetime,
    hh_format,
    to_ct,
    to_utc,
    utc_datetime_now,
)


def hh(data_source, provider="APXMIDP"):
    try:
        cache = data_source.caches["bmarketidx"]
    except KeyError:
        cache = data_source.caches["bmarketidx"] = {}

    for hh in data_source.hh_data:
        try:
            hh["bmarketidx-rate"] = cache[hh["start-date"]][provider]
        except KeyError:
            h_start = hh["start-date"]
            rates = data_source.non_core_rate("bmarketidx", h_start)["rates"]

            try:
                idxs = cache[h_start]
            except KeyError:
                idxs = cache[h_start] = {}

            try:
                rate = rates[h_start]
            except KeyError:
                try:
                    rate = sorted(rates.items())[-1][1]
                except KeyError:
                    raise BadRequest(
                        f"For the bmarketidx rate script at "
                        f"{hh_format(h_start)} the rate cannot be found."
                    )

            try:
                idx = rate[provider]
            except KeyError:
                try:
                    idx = sorted(rate.items())[0][1]
                except KeyError:
                    raise BadRequest(
                        f"For the bmarketidx rate script at "
                        f"{hh_format(h_start)} a rate cannot be found for the "
                        f"provider {provider}."
                    )

            hh["bmarketidx-rate"] = idxs[provider] = float(idx)


bmarketidx_importer = None


class BmarketidxImporter(threading.Thread):
    def __init__(self):
        super().__init__(name="Bmarketidx Importer")
        self.lock = threading.RLock()
        self.messages = deque(maxlen=1000)
        self.stopped = threading.Event()
        self.going = threading.Event()

    def stop(self):
        self.stopped.set()
        self.going.set()
        self.join()

    def go(self):
        self.going.set()

    def is_locked(self):
        if self.lock.acquire(False):
            self.lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        )

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                self.global_alert = contract = None
                with Session() as sess:
                    try:
                        self.log("Starting to check bmarketidx.")
                        contract = Contract.get_non_core_by_name(sess, "bmarketidx")
                        latest_rs = (
                            sess.query(RateScript)
                            .filter(RateScript.contract_id == contract.id)
                            .order_by(RateScript.start_date.desc())
                            .first()
                        )
                        start_ct = to_ct(latest_rs.start_date)

                        months = list(
                            c_months_u(
                                start_year=start_ct.year,
                                start_month=start_ct.month,
                                months=2,
                            )
                        )
                        month_start, month_finish = months[1]

                        now = utc_datetime_now()
                        if now > month_finish:
                            _process_month(
                                self.log,
                                sess,
                                contract,
                                latest_rs,
                                month_start,
                                month_finish,
                            )

                    except BaseException:
                        self.log(f"Outer problem {traceback.format_exc()}")
                        sess.rollback()
                        if contract is None:
                            self.global_alert = (
                                "There's a problem with the bmarketidx automatic "
                                "importer."
                            )
                        else:
                            self.global_alert = (
                                f"There's a problem with the <a "
                                f"href='/non_core_contracts/{contract.id}/"
                                f"auto_importer'>bmarketidx automatic "
                                f"importer</a>."
                            )
                    finally:
                        self.lock.release()
                        self.log("Finished checking bmarketidx rates.")

            self.going.wait(2 * 60 * 60)
            self.going.clear()


def _process_month(log_f, sess, contract, latest_rs, month_start, month_finish):
    latest_rs_id = latest_rs.id
    log_f(
        f"Checking to see if data is available from {hh_format(month_start)} "
        f"to {hh_format(month_finish)} on BMRS."
    )
    rates = {}
    month_finish_ct = to_ct(month_finish)
    base_url = "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index"
    for d in range(month_finish_ct.day):
        day_from_ct = ct_datetime(month_finish_ct.year, month_finish_ct.month, d + 1)
        day_to_ct = day_from_ct + relativedelta(days=1)
        params = {
            "from": f'{day_from_ct.strftime("%Y-%m-%d")}T00:00Z',
            "to": f'{day_to_ct.strftime("%Y-%m-%d")}T00:00Z',
            "settlementPeriodFrom": "1",
            "settlementPeriodTo": "1",
        }
        sess.rollback()
        q_str = "&".join(f"{k}={v}" for k, v in params.items())
        log_f(f"Attempting to download {base_url}?{q_str}")
        r = requests.get(base_url, params=params, timeout=60, verify=False)
        res = r.json()
        for h in res["data"]:
            # {
            #   "startTime":"2022-06-01T23:00:00Z",
            #   "dataProvider":"N2EXMIDP",
            #   "settlementDate":"2022-06-02",
            #   "settlementPeriod":1,
            #   "price":0.00,
            #   "volume":0.000
            # },
            settlement_date = Datetime.strptime(h["settlementDate"], "%Y-%m-%d")
            if settlement_date.month == month_finish_ct.month:
                dt = to_utc(settlement_date + (int(h["settlementPeriod"]) - 1) * HH)
                try:
                    rate = rates[dt]
                except KeyError:
                    rate = rates[dt] = {}
                rate[h["dataProvider"]] = Decimal(h["price"]) / Decimal(1000)

    if month_finish in rates:
        log_f("The whole month's data is there.")
        script = {"rates": rates}
        rs = RateScript.get_by_id(sess, latest_rs_id)
        contract.update_rate_script(
            sess, rs, rs.start_date, month_finish, loads(rs.script)
        )
        contract.insert_rate_script(sess, month_start, script)
        sess.commit()
        log_f(f"Added a new rate script starting at {hh_format(month_start)}.")
    else:
        msg = "There isn't a whole month there yet."
        if len(rates) > 0:
            msg += " The last date is {sorted(rates.keys())[-1]}"
        log_f(msg)


def get_importer():
    return bmarketidx_importer


def startup():
    global bmarketidx_importer
    bmarketidx_importer = BmarketidxImporter()
    bmarketidx_importer.start()


@atexit.register
def shutdown():
    if bmarketidx_importer is not None:
        bmarketidx_importer.stop()
