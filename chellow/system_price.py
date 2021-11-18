import atexit
import collections
import datetime
import http.client
import threading
import traceback
import urllib.parse
from datetime import timedelta as Timedelta

from werkzeug.exceptions import BadRequest

import xlrd

from zish import loads

from chellow.models import Contract, RateScript, Session, get_non_core_contract_id
from chellow.utils import HH, hh_format, to_ct, to_utc, utc_datetime_now


ELEXON_PORTAL_SCRIPTING_KEY_KEY = "elexonportal_scripting_key"


def key_format(dt):
    return dt.strftime("%d %H:%M")


def hh(data_source):
    for h in data_source.hh_data:
        try:
            sbp, ssp = data_source.caches["system_price"][h["start-date"]]
        except KeyError:
            try:
                system_price_cache = data_source.caches["system_price"]
            except KeyError:
                system_price_cache = data_source.caches["system_price"] = {}

            db_id = get_non_core_contract_id("system_price")
            h_start = h["start-date"]
            rates = data_source.hh_rate(db_id, h_start)["gbp_per_nbp_mwh"]

            try:
                try:
                    rdict = rates[key_format(h_start)]
                except KeyError:
                    rdict = rates[key_format(h_start - Timedelta(days=3))]
                sbp = float(rdict["sbp"] / 1000)
                ssp = float(rdict["ssp"] / 1000)
                system_price_cache[h_start] = (sbp, ssp)
            except KeyError:
                raise BadRequest(
                    f"For the System Price rate script at {hh_format(h_start)} "
                    f"the rate cannot be found."
                )
            except TypeError:
                raise BadRequest(
                    f"For the System Price rate script at {hh_format(h_start)} "
                    f"the rate 'rates_gbp_per_mwh' has the problem: "
                    f"{traceback.format_exc()}"
                )

        h["sbp"] = sbp
        h["sbp-gbp"] = h["nbp-kwh"] * sbp

        h["ssp"] = ssp
        h["ssp-gbp"] = h["nbp-kwh"] * ssp


system_price_importer = None


class SystemPriceImporter(threading.Thread):
    def __init__(self):
        super(SystemPriceImporter, self).__init__(name="System Price Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=1000)
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = "proxy.host"
        self.PROXY_PORT_KEY = "proxy.port"

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
                sess = book = sbp_sheet = ssp_sheet = None
                try:
                    sess = Session()
                    self.log("Starting to check System Prices.")
                    # ct_tz = pytz.timezone('Europe/London')
                    contract = Contract.get_non_core_by_name(sess, "system_price")
                    contract_props = contract.make_properties()

                    if contract_props.get("enabled", False):
                        for rscript in (
                            sess.query(RateScript)
                            .filter(RateScript.contract == contract)
                            .order_by(RateScript.start_date.desc())
                        ):
                            ns = loads(rscript.script)
                            rates = ns["gbp_per_nbp_mwh"]
                            if len(rates) == 0:
                                fill_start = rscript.start_date
                                break
                            elif rates[key_format(rscript.finish_date)]["run"] == "DF":
                                fill_start = rscript.finish_date + HH
                                break

                        config = Contract.get_non_core_by_name(sess, "configuration")
                        config_props = config.make_properties()

                        scripting_key = config_props.get(
                            ELEXON_PORTAL_SCRIPTING_KEY_KEY
                        )
                        if scripting_key is None:
                            raise BadRequest(
                                f"The property {ELEXON_PORTAL_SCRIPTING_KEY_KEY} "
                                f"cannot be found in the configuration properties."
                            )
                        url_str = (
                            contract_props["url"]
                            + "file/download/BESTVIEWPRICES_FILE?key="
                            + scripting_key
                        )

                        self.log(
                            f"Downloading from {url_str} and extracting data from "
                            f"{hh_format(fill_start)}"
                        )

                        url = urllib.parse.urlparse(url_str)
                        if url.scheme == "https":
                            conn = http.client.HTTPSConnection(url.hostname, url.port)
                        else:
                            conn = http.client.HTTPConnection(url.hostname, url.port)
                        conn.request("GET", url.path + "?" + url.query)

                        res = conn.getresponse()
                        self.log("Received " + str(res.status) + " " + res.reason)
                        data = res.read()
                        book = xlrd.open_workbook(file_contents=data)
                        sbp_sheet = book.sheet_by_index(1)
                        ssp_sheet = book.sheet_by_index(2)

                        sp_months = []
                        sp_month = None
                        for row_index in range(1, sbp_sheet.nrows):
                            sbp_row = sbp_sheet.row(row_index)
                            ssp_row = ssp_sheet.row(row_index)
                            raw_date = datetime.datetime(
                                *xlrd.xldate_as_tuple(sbp_row[0].value, book.datemode)
                            )
                            hh_date_ct = to_ct(raw_date)
                            hh_date = to_utc(hh_date_ct)
                            run_code = sbp_row[1].value
                            for col_idx in range(2, 52):
                                if hh_date >= fill_start:
                                    sbp_val = sbp_row[col_idx].value
                                    if sbp_val != "":
                                        if (
                                            hh_date.day == 1
                                            and hh_date.hour == 0
                                            and hh_date.minute == 0
                                        ):
                                            sp_month = {}
                                            sp_months.append(sp_month)
                                        ssp_val = ssp_row[col_idx].value
                                        sp_month[hh_date] = {
                                            "run": run_code,
                                            "sbp": sbp_val,
                                            "ssp": ssp_val,
                                        }
                                hh_date += HH
                        self.log("Successfully extracted data.")
                        last_date = sorted(sp_months[-1].keys())[-1]
                        if last_date.month == (last_date + HH).month:
                            del sp_months[-1]
                        if "limit" in contract_props:
                            sp_months = sp_months[0:1]
                        for sp_month in sp_months:
                            sorted_keys = sorted(sp_month.keys())
                            month_start = sorted_keys[0]
                            month_finish = sorted_keys[-1]
                            rs = (
                                sess.query(RateScript)
                                .filter(
                                    RateScript.contract == contract,
                                    RateScript.start_date == month_start,
                                )
                                .first()
                            )
                            if rs is None:
                                self.log(
                                    f"Adding a new rate script starting at "
                                    f"{hh_format(month_start)}."
                                )

                                latest_rs = (
                                    sess.query(RateScript)
                                    .filter(RateScript.contract == contract)
                                    .order_by(RateScript.start_date.desc())
                                    .first()
                                )

                                contract.update_rate_script(
                                    sess,
                                    latest_rs,
                                    latest_rs.start_date,
                                    month_finish,
                                    loads(latest_rs.script),
                                )
                                rs = contract.insert_rate_script(sess, month_start, {})
                                sess.flush()
                            script = {
                                "gbp_per_nbp_mwh": dict(
                                    (key_format(k), v) for k, v in sp_month.items()
                                )
                            }
                            self.log(
                                f"Updating rate script starting at "
                                f"{hh_format(month_start)}."
                            )
                            contract.update_rate_script(
                                sess, rs, rs.start_date, rs.finish_date, script
                            )
                            sess.commit()
                    else:
                        self.log(
                            "The automatic importer is disabled. To enable it, edit "
                            "the contract properties to set 'enabled' to True."
                        )

                except BaseException:
                    self.log(f"Outer problem {traceback.format_exc()}")
                    sess.rollback()
                finally:
                    book = sbp_sheet = ssp_sheet = None
                    self.lock.release()
                    self.log("Finished checking System Price rates.")
                    if sess is not None:
                        sess.close()

            self.going.wait(24 * 60 * 60)
            self.going.clear()


def get_importer():
    return system_price_importer


def startup():
    global system_price_importer
    system_price_importer = SystemPriceImporter()
    system_price_importer.start()


@atexit.register
def shutdown():
    if system_price_importer is not None:
        system_price_importer.stop()
