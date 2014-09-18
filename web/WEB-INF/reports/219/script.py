from net.sf.chellow.monad import Monad
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, and_

Monad.getUtils()['impt'](globals(), 'utils', 'db')

HH, hh_format = utils.HH, utils.hh_format
RegisterRead, Bill, Supply, Era = db.RegisterRead, db.Bill, db.Supply, db.Era

sess = None
try:
    sess = db.session()

    year = inv.getInteger("end_year")
    month = inv.getInteger("end_month")
    months = inv.getInteger("months")

    finish_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc) + relativedelta(months=1) - HH

    start_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc) - relativedelta(months=months-1)

    reads = sess.query(RegisterRead).filter(or_(and_(RegisterRead.present_date>=start_date, RegisterRead.present_date<=finish_date), and_(RegisterRead.previous_date>=start_date, RegisterRead.previous_date<=finish_date))).join(Bill).order_by(Bill.supply_id)

    if inv.hasParameter('supply_id'):
        supply_id = inv.getLong('supply_id')
        supply = Supply.get_by_id(sess, supply_id)
        reads = reads.filter(Bill.supply_id==supply.id)

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="reads_' + datetime.datetime.now(pytz.utc).strftime("%Y%M%d%H%m") + '.csv"')
    pw = inv.getResponse().getWriter()
    pw.println("Duration Start,Duration Finish,Supply Id,Import MPAN Core,Export MPAN Core,Batch Reference,Bill Id,Bill Reference,Bill Issue Date,Bill Type,Register Read Id,TPR,Coefficient,Previous Read Date,Previous Read Value,Previous Read Type,Present Read Date,Present Read Value,Present Read Type")
    pw.flush()

    for read in reads:
        bill = read.bill
        supply = bill.supply
        batch = bill.batch

        era = supply.find_era_at(sess, bill.start_date)
        if era is None:
            eras = sess.query(Era).filter(Era.supply_id==supply.id).order_by(Era.start_date).all()
            if bill.start_date < eras[0].start_date:
                era = eras[0]
            else:
                era = eras[-1]

        pw.println(','.join('"' + ('' if value is None else str(value)) + '"' for value in [hh_format(start_date), hh_format(finish_date), supply.id, era.imp_mpan_core, era.exp_mpan_core, batch.reference,bill.id, bill.reference, hh_format(bill.issue_date), bill.bill_type.code, read.id, 'md' if read.tpr is None else read.tpr.code, read.coefficient, hh_format(read.previous_date), read.previous_value, read.previous_type.code, hh_format(read.present_date), read.present_value, read.present_type.code]))
        pw.flush()

    pw.close()

finally:
    if sess is not None:
        sess.close()