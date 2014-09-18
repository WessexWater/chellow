from net.sf.chellow.monad import Monad, Hiber, UserException
import datetime
import pytz
from dateutil.relativedelta import relativedelta

Monad.getUtils()['imprt'](globals(), {
        'db': ['HhDatum', 'Site', 'Supply', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH', 'form_date'],
        'templater': ['render']})

months = inv.getInteger('months')
finish_year = inv.getInteger('finish_year')
finish_month = inv.getInteger('finish_month')

finish_date = datetime.datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) + relativedelta(months=1) - HH
start_date = finish_date + HH - relativedelta(months=months)

file_name = "site_hh_data_" + start_date.strftime("%Y%m%d%H%M") + ".csv"

inv.getResponse().setContentType("text/csv")
inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="' + file_name + '"')
pw = inv.getResponse().getWriter()

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        site_id = inv.getLong('site_id')
        site = Site.get_by_id(sess, site_id)
        type = inv.getString('type')
        pw.print(','.join(('Site Code', 'Type', 'Date') + tuple(map(str, range(1, 49)))))
        for group in site.groups(sess, start_date, finish_date, True):
            for hh in group.hh_data(sess):
              start_date = hh['start_date']
              if start_date.hour == 0 and start_date.minute == 0:
                pw.print('\r\n' + ','.join((site.code, type, start_date.strftime("%Y-%m-%d"))))
                pw.flush()
              pw.print("," + str(hh[type]))
    pw.close()
finally:
    sess.close()