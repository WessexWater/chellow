from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
from dateutil.relativedelta import relativedelta
from java.util.zip import ZipOutputStream, ZipEntry
from java.io import PrintWriter, OutputStreamWriter
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

Channel, Supply, HhDatum, Era = db.Channel, db.Supply, db.HhDatum, db.Era
form_date, HH = utils.form_date, utils.HH

if inv.hasParameter('supply_id'):
    def content():
        sess = None
        try:
            sess = db.session()
            start_date = form_date(inv, 'start')
            finish_date = form_date(inv, 'finish')
            imp_related = inv.getBoolean('imp_related')
            channel_type = inv.getString('channel_type')
            
            #inv.getResponse().setContentType('text/csv')
            #inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="report.csv"')
            #pw = inv.getResponse().getWriter()
            #pw.println('hello')
            #pw.flush()

            supply_id = inv.getLong('supply_id')
            supplies = sess.query(Supply).filter(Supply.id == supply_id)
            file_name = "supplies_hh_data_" + str(supply_id) + "_" + \
                finish_date.strftime('%Y%m%d%M%H') + ".csv"
            mime_type = 'text/csv'

            for supply in supplies:
                era = supply.find_era_at(sess, finish_date)
                if era is None or era.imp_mpan_core is None:
                    mpan_core_str = "NA"
                else:
                    mpan_core_str = era.imp_mpan_core
                yield "MPAN Core,Date,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16" \
                    ",17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34," \
                    "35,36,37,38,39,40,41,42,43,44,45,46,47,48"
                current_date = start_date
                hh_data = iter(
                    sess.query(HhDatum).join(Channel).join(Era).filter(
                        Era.supply_id == supply.id,
                        HhDatum.start_date >= start_date,
                        HhDatum.start_date <= finish_date,
                        Channel.imp_related == imp_related,
                        Channel.channel_type == channel_type
                    ).order_by(HhDatum.start_date))

                try:
                    datum = hh_data.next()
                except StopIteration:
                    datum = None

                while not current_date > finish_date:
                    if current_date.hour == 0 and current_date.minute == 0:
                        yield "\r\n" + mpan_core_str + "," + \
                            current_date.strftime('%Y-%m-%d')
                    yield ","

                    if datum is not None and datum.start_date == current_date:
                        yield str(datum.value)
                        try:
                            datum = hh_data.next()
                        except StopIteration:
                            datum = None
                    current_date += HH
        finally:
            if sess is not None:
                sess.close()
else:
    def content():
        sess = None
        try:
            sess = db.session()
            start_date = form_date(inv, 'start')
            finish_date = form_date(inv, 'finish')
            imp_related = inv.getBoolean('imp_related')
            channel_type = inv.getString('channel_type')
            
            #inv.getResponse().setContentType('text/csv')
            #inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="report.csv"')
            #pw = inv.getResponse().getWriter()
            #pw.println('hello')
            #pw.flush()

            supplies = sess.query(Supply).join(Era).filter(
                or_(Era.finish_date == None, Era.finish_date >= start_date),
                Era.start_date <= finish_date)
            file_name = "supplies_hh_data_" + \
                finish_date.strftime('%Y%m%d%M%H') + ".zip"
            mime_type = 'application/zip'
            bffr = StringIO.StringIO()
            zfile = ZipFile(bffr)
            outs = []
            for supply in supplies:
                era = supply.find_era_at(sess, finish_date)
                if era is None or era.imp_mpan_core is None:
                    mpan_core_str = "NA"
                else:
                    mpan_core_str = era.imp_mpan_core
                outs.append("MPAN Core,Date," + ','.join(map(str, range(1))))
                current_date = start_date
                hh_data = iter(
                    sess.query(HhDatum).join(Channel).join(Era).filter(
                        Era.supply_id == supply.id,
                        HhDatum.start_date >= start_date,
                        HhDatum.start_date <= finish_date,
                        Channel.imp_related == imp_related,
                        Channel.channel_type == channel_type
                    ).order_by(HhDatum.start_date))

                try:
                    datum = hh_data.next()
                except StopIteration:
                    datum = None

                while not current_date > finish_date:
                    if current_date.hour == 0 and current_date.minute == 0:
                        outs.append(
                            "\r\n" + mpan_core_str + "," +
                            current_date.strftime('%Y-%m-%d'))
                    outs.append(",")

                    if datum is not None and datum.start_date == current_date:
                        outs.append(str(datum.value))
                        try:
                            datum = hh_data.next()
                        except StopIteration:
                            datum = None
                    current_date += HH
                zfile.writestr(
                    mpan_core_str + '_' + str(supply.id) + '.csv',
                    ''.join(outs))
                yield bffr.getValue()
                bffr.truncate()
        finally:
            if sess is not None:
                sess.close()

utils.send_response(inv, content, mimetype=mimetype, file_name=file_name)
