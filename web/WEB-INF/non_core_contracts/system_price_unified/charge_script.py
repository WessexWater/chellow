from net.sf.chellow.monad import Monad
import collections
import pytz
import threading
import datetime
import traceback
import urlparse
import httplib
import db
import utils
import xlrd
Monad.getUtils()['impt'](globals(), 'db', 'utils')
Contract, RateScript = db.Contract, db.RateScript
HH, UserException, hh_format = utils.HH, utils.UserException, utils.hh_format
db_id = globals()['db_id']

ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


def key_format(dt):
    return dt.strftime("%d %H:%M")


def create_future_func(multiplier, constant):
    def transform(val):
        return {
            'run': val['run'], 'sbp': val['sbp'] * multiplier + constant,
            'ssp': val['ssp'] * multiplier + constant}

    def future_func(ns):
        new_ns = {}
        old_result = ns['gbp_per_nbp_mwh']
        last_value = old_result[sorted(old_result.keys())[-1]]
        new_ns['gbp_per_nbp_mwh'] = collections.defaultdict(
            lambda: transform(last_value), [
                (k, transform(v)) for k, v in old_result.iteritems()])
        return new_ns
    return future_func


def hh(data_source):
    ssp_rate_set = data_source.supplier_rate_sets['ssp-rate']
    sbp_rate_set = data_source.supplier_rate_sets['sbp-rate']

    try:
        system_price_cache = data_source.caches['system_price_unified']
    except KeyError:
        data_source.caches['system_price_unified'] = {}
        system_price_cache = data_source.caches['system_price_unified']

        try:
            future_funcs = data_source.caches['future_funcs']
        except KeyError:
            future_funcs = {}
            data_source.caches['future_funcs'] = future_funcs

        try:
            future_funcs[db_id]
        except KeyError:
            future_funcs[db_id] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    for h in data_source.hh_data:
        try:
            sbp, ssp = system_price_cache[h['start-date']]
        except KeyError:
            h_start = h['start-date']
            rates = data_source.hh_rate(db_id, h_start, 'gbp_per_nbp_mwh')
            try:
                rdict = rates[key_format(h_start)]
                sbp = float(rdict['sbp']) / 1000
                ssp = float(rdict['ssp']) / 1000
                system_price_cache[h_start] = (sbp, ssp)
            except KeyError:
                raise UserException(
                    "For the System Price Unified rate script at " +
                    hh_format(h_start) + " the rate cannot be found.")
            except TypeError:
                raise UserException(
                    "For the System Price Unified rate script at " +
                    hh_format(h_start) +
                    " the rate 'rates_gbp_per_mwh' has the problem: " +
                    traceback.format_exc())

        h['sbp'] = sbp
        h['sbp-gbp'] = h['nbp-kwh'] * sbp
        sbp_rate_set.add(sbp)

        h['ssp'] = ssp
        h['ssp-gbp'] = h['nbp-kwh'] * ssp
        ssp_rate_set.add(ssp)


system_price_importer = None


class SystemPriceImporter(threading.Thread):
    def __init__(self):
        super(SystemPriceImporter, self).__init__(
            name="System Price Elexon Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque()
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = 'proxy.host'
        self.PROXY_PORT_KEY = 'proxy.port'

    def stop(self):
        self.stopped.set()
        self.going.set()

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
            datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") +
            " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = db.session()
                    self.log("Starting to check System Prices.")
                    # ct_tz = pytz.timezone('Europe/London')
                    contract = Contract.get_non_core_by_name(
                        sess, 'system_price_unified')
                    contract_props = contract.make_properties()

                    if contract_props.get('enabled', False):
                        for rscript in sess.query(RateScript).filter(
                                RateScript.contract == contract).order_by(
                                RateScript.start_date.desc()):
                            ns = eval(rscript.script)
                            rates = ns['gbp_per_nbp_mwh']
                            if len(rates) == 0:
                                fill_start = rscript.start_date
                                break
                            elif rates[
                                    key_format(
                                        rscript.finish_date)]['run'] == 'DF':
                                fill_start = rscript.finish_date + HH
                                break

                        config = Contract.get_non_core_by_name(
                            sess, 'configuration')
                        config_props = config.make_properties()

                        scripting_key = config_props.get(
                                ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                        if scripting_key is None:
                            raise UserException(
                                "The property " +
                                ELEXON_PORTAL_SCRIPTING_KEY_KEY +
                                " cannot be found in the configuration "
                                "properties.")
                        url_str = contract_props['url'] + \
                            'file/download/BESTVIEWPRICES_FILE?key=' + \
                            scripting_key

                        self.log(
                            "Downloading from " + url_str +
                            " and extracting data from " +
                            hh_format(fill_start))

                        url = urlparse.urlparse(url_str)
                        if url.scheme == 'https':
                            conn = httplib.HTTPSConnection(
                                url.hostname, url.port)
                        else:
                            conn = httplib.HTTPConnection(
                                url.hostname, url.port)
                        conn.request("GET", url.path + '?' + url.query)

                        res = conn.getresponse()
                        self.log(
                            "Received " + str(res.status) + " " + res.reason)
                        data = res.read()
                        book = xlrd.open_workbook(file_contents=data)
                        sbp_sheet = book.sheet_by_index(1)
                        ssp_sheet = book.sheet_by_index(2)

                        ct_tz = pytz.timezone('Europe/London')

                        sp_months = []
                        sp_month = None
                        for row_index in range(1, sbp_sheet.nrows):
                            sbp_row = sbp_sheet.row(row_index)
                            ssp_row = ssp_sheet.row(row_index)
                            raw_date = datetime.datetime(
                                *xlrd.xldate_as_tuple(
                                    sbp_row[0].value, book.datemode))
                            hh_date_ct = ct_tz.localize(raw_date)
                            hh_date = pytz.utc.normalize(
                                hh_date_ct.astimezone(pytz.utc))
                            if hh_date >= fill_start:
                                run_code = sbp_row[1].value
                                for col_idx in range(2, 52):
                                    sbp_val = sbp_row[col_idx].value
                                    if sbp_val != '':
                                        if hh_date.day == 1 and \
                                                hh_date.hour == 0 and \
                                                hh_date.minute == 0:
                                            sp_month = {}
                                            sp_months.append(sp_month)
                                        ssp_val = ssp_row[col_idx].value
                                        sp_month[hh_date] = {
                                            'run': run_code,
                                            'sbp': sbp_val, 'ssp': ssp_val}
                                    hh_date += HH
                        self.log("Successfully extracted data.")
                        sp_months[-1]
                        last_date = sorted(sp_months[-1].keys())[-1]
                        if last_date.month == (last_date + HH).month:
                            del sp_months[-1]
                        if 'limit' in contract_props:
                            sp_months = [sp_months[0]]
                        for sp_month in sp_months:
                            sorted_keys = sorted(sp_month.keys())
                            month_start = sorted_keys[0]
                            month_finish = sorted_keys[-1]
                            db.set_read_write(sess)
                            rs = sess.query(RateScript).filter(
                                RateScript.contract == contract,
                                RateScript.start_date == month_start).first()
                            if rs is None:
                                self.log(
                                    "Adding a new rate script starting at " +
                                    hh_format(month_start) + ".")

                                latest_rs = sess.query(RateScript).filter(
                                    RateScript.contract == contract).\
                                    order_by(RateScript.start_date.desc()). \
                                    first()

                                contract.update_rate_script(
                                    sess, latest_rs, latest_rs.start_date,
                                    month_finish, latest_rs.script)
                                rs = contract.insert_rate_script(
                                    sess, month_start, '')

                            script = "{\n    'gbp_per_nbp_mwh': {\n" + \
                                ',\n'.join(
                                    "        '" + key_format(k) +
                                    "': {'run': '" + str(sp_month[k]['run']) +
                                    "', 'sbp': " + str(sp_month[k]['sbp']) +
                                    ", 'ssp': " + str(sp_month[k]['ssp']) + '}'
                                    for k in sorted(sp_month.keys())) + "}}"
                            self.log(
                                "Updating rate script starting at " +
                                hh_format(month_start) + ".")
                            contract.update_rate_script(
                                sess, rs, rs.start_date, rs.finish_date,
                                script)
                            sess.commit()
                    else:
                        self.log(
                            "The automatic importer is disabled. To "
                            "enable it, edit the contract properties to "
                            "set 'enabled' to True.")

                except:
                    self.log("Outer problem " + traceback.format_exc())
                    if sess is not None:
                        sess.rollback()
                finally:
                    try:
                        if sess is not None:
                            sess.close()
                    finally:
                        self.lock.release()
                        self.log("Finished checking System Price rates.")

            self.going.wait(24 * 60 * 60)
            self.going.clear()


def get_importer():
    return system_price_importer


def startup():
    global system_price_importer
    system_price_importer = SystemPriceImporter()
    system_price_importer.start()


def shutdown():
    if system_price_importer is not None:
        system_price_importer.stop()
        if system_price_importer.isAlive():
            raise UserException(
                "Can't shut down System Price importer, it's still running.")
