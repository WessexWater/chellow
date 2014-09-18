from net.sf.chellow.monad import Monad
from javax.xml.parsers import DocumentBuilderFactory
from org.w3c.dom import Node
from org.apache.http.protocol import HTTP
from org.apache.http.client.entity import UrlEncodedFormEntity
from org.apache.http.util import EntityUtils
from org.apache.http import HttpHost
from org.apache.http.conn.params import ConnRoutePNames
from org.apache.http.impl.client import DefaultHttpClient
from org.apache.http.message import BasicNameValuePair
from org.apache.http.client.methods import HttpGet, HttpPost
from com.Ostermiller.util import CSVParser
import sys
import types
import collections
import pytz
import threading
import datetime
import traceback
from dateutil.relativedelta import relativedelta

Monad.getUtils()['impt'](globals(), 'db', 'utils')

Contract = db.Contract

def identity_func(x):
    return x

def hh(supply_source):
    rate_sets = supply_source.supplier_rate_sets

    try:
        cache = supply_source.caches['system_price']
    except KeyError:
        cache = {}
        supply_source.caches['system_price'] = cache

    for hh in supply_source.hh_data:
        try:
            prices = cache[hh['start-date']]
        except KeyError:
            bmreports_contract = Contract.get_non_core_by_name(supply_source.sess, 'system_price_bmreports')
            elexon_contract = Contract.get_non_core_by_name(supply_source.sess, 'system_price_elexon')
            prices = {}
            date_str = hh['start-date'].strftime("%d %H:%M Z")
            for pref in ['ssp', 'sbp']:
                transform_func = identity_func
                rate = supply_source.hh_rate(elexon_contract.id, hh['start-date'], pref + 's')
                if isinstance(rate, dict):
                    rate = transform_func(rate)
                    prices[pref + '-gbp-per-kwh'] = float(rate[date_str]) / 1000 
                else:
                    rate = supply_source.hh_rate(bmreports_contract.id, hh['start-date'], pref + 's')
                    dt = hh['start-date']
                    while isinstance(rate, types.FunctionType):
                        transform_func = rate
                        dt += relativedelta(years=1)
                        rate = supply_source.hh_rate(bmreports_contract.id, dt, pref + 's')

                    if isinstance(rate, dict):
                        rate = transform_func(rate)
                        prices[pref + '-gbp-per-kwh'] = float(rate[date_str]) / 1000 
                    else:
                        raise UserException("Type returned by " + pref + "s at " + hh_format(dt) + " must be function or dictionary.")
            cache[hh['start-date']] = prices

        hh.update(prices)
        hh['ssp-gbp'] = hh['nbp-kwh'] * hh['ssp-gbp-per-kwh'] 
        hh['sbp-gbp'] = hh['nbp-kwh'] * hh['sbp-gbp-per-kwh']
        rate_sets['ssp-rate'].add(hh['ssp-gbp-per-kwh'])
        rate_sets['sbp-rate'].add(hh['sbp-gbp-per-kwh'])