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

    if inv.hasParameter('supply_id'):
        supply_id = inv.getLong('supply_id')
        supplies = sess.query(Supply).from_statement("select * from supply where id = :supply_id").params(supply_id=supply_id)
        file_name = "supplies_hh_data_" + str(supply_id) + "_" + finish_date.strftime('%Y%m%d%M%H') + ".csv"
        inv.getResponse().setContentType('text/csv')
        inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="' + file_name + '"')
        pw = inv.getResponse().getWriter()
        zout = None
    else:
        supplies = sess.query(Supply).from_statement("select distinct supply.* from supply, era where era.supply_id = supply.id and (era.finish_date is null or era.finish_date >= :start_date) and era.start_date <= :finish_date").params(start_date=start_date, finish_date=finish_date)
        file_name = "supplies_hh_data_" + finish_date.strftime('%Y%m%d%M%H') + ".zip"
        inv.getResponse().setContentType('application/zip')
        inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="' + file_name + '"')
        sout = inv.getResponse().getOutputStream()
        zout = ZipOutputStream(sout)
        pw = PrintWriter(OutputStreamWriter(zout, 'UTF-8'))

    for supply in supplies:
        era = supply.find_era_at(sess, finish_date)
        if era is None or era.imp_mpan_core is None:
            mpan_core_str = "NA"
        else:
            mpan_core_str = era.imp_mpan_core
        if zout is not None:
            zout.putNextEntry(ZipEntry(mpan_core_str + '_' + str(supply.id) + '.csv'))
        pw.print("MPAN Core,Date,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48")
        current_date = start_date
        hh_data = iter(sess.query(HhDatum).join(Channel).join(Era).filter(Era.supply_id==supply.id, HhDatum.start_date>=start_date, HhDatum.start_date<=finish_date, Channel.imp_related==imp_related, Channel.channel_type==channel_type).order_by(HhDatum.start_date))

        try:
            datum = hh_data.next()
        except StopIteration:
            datum = None

        while not current_date > finish_date:
            if current_date.hour == 0 and current_date.minute == 0:
                pw.print("\r\n" + mpan_core_str + "," + current_date.strftime('%Y-%m-%d'))
            pw.print(",")

            if datum is not None and datum.start_date == current_date:
                pw.print(str(datum.value))
                try:
                    datum = hh_data.next()
                except StopIteration:
                    datum = None
            current_date += HH
        pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()