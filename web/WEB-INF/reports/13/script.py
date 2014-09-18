from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from sqlalchemy import or_
import pytz
import datetime
from dateutil.relativedelta import relativedelta
from java.lang import System

Monad.getUtils()['imprt'](globals(), {
        'db': ['HhDatum', 'Channel', 'Snag', 'Era', 'Site', 'Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH'],
        'templater': ['render']})


sess = None
try:
    sess = session()

    site_id = inv.getLong("site_id")
    finish_year = inv.getInteger("finish_year")
    finish_month = inv.getInteger("finish_month")
    start_date = datetime.datetime(finish_year, finish_month, 1, tzinfo=pytz.utc)

    start_date -= relativedelta(months=11)

    site = Site.get_by_id(sess, site_id)

    typs = ('imp_net', 'exp_net', 'used', 'displaced', 'imp_gen', 'exp_gen')

    months = []
    month_start = start_date
    for i in range(12):
        month_finish = month_start + relativedelta(months=1) - HH
        month = dict((typ, {'md': 0, 'md_date': None, 'kwh': 0}) for typ in typs)
        month['start_date'] = month_start
        months.append(month)

        for group in site.groups(sess, month_start, month_finish, True):
            for hh in group.hh_data(sess):
                for tp in typs:
                    if hh[tp] * 2 > month[tp]['md']:
                        month[tp]['md'] = hh[tp] * 2
                        month[tp]['md_date'] = hh['start_date']
                    month[tp]['kwh'] += hh[tp]

        has_snags = sess.query(Snag).filter(Snag.site==site, Snag.start_date <= month_finish, or_(Snag.finish_date is None, Snag.finish_date > month_start)).count() > 0
        month['has_site_snags'] = has_snags

        month_start += relativedelta(months=1)


    totals = dict((typ, {'md': 0, 'md_date': None, 'kwh': 0}) for typ in typs)

    for month in months:
        for typ in typs:
            if month[typ]['md'] > totals[typ]['md']:
                totals[typ]['md'] = month[typ]['md']
                totals[typ]['md_date'] = month[typ]['md_date']
            totals[typ]['kwh'] += month[typ]['kwh']

    months.append(totals)

    render(inv, template, {'site': site, 'months': months})
finally:
    sess.close()