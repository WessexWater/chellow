from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, and_
import traceback
from chellow.models import RegisterRead, Bill, Supply, Era, Session
from chellow.utils import HH, hh_format, req_int, utc_datetime
from flask import request, g
import chellow.dloads
import csv
import os
from werkzeug.exceptions import BadRequest
import threading
from chellow.views import chellow_redirect


def content(year, month, months, supply_id, user):
    sess = f = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'register_reads.csv', user)
        f = open(running_name, mode='w', newline='')
        w = csv.writer(f, lineterminator='\n')
        w.writerow(
            (
                'Duration Start', 'Duration Finish', 'Supply Id',
                'Import MPAN Core', 'Export MPAN Core', 'Batch Reference',
                'Bill Id', 'Bill Reference', 'Bill Issue Date', 'Bill Type',
                'Register Read Id', 'TPR', 'Coefficient',
                'Previous Read Date', 'Previous Read Value',
                'Previous Read Type', 'Present Read Date',
                'Present Read Value', 'Present Read Type'))

        finish_date = utc_datetime(year, month, 1) + \
            relativedelta(months=1) - HH

        start_date = utc_datetime(year, month, 1) - \
            relativedelta(months=months-1)

        reads = sess.query(RegisterRead).filter(
            or_(
                and_(
                    RegisterRead.present_date >= start_date,
                    RegisterRead.present_date <= finish_date),
                and_(
                    RegisterRead.previous_date >= start_date,
                    RegisterRead.previous_date <= finish_date))) \
            .join(Bill).order_by(Bill.supply_id)

        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            reads = reads.filter(Bill.supply == supply)

        for read in reads:
            bill = read.bill
            supply = bill.supply
            batch = bill.batch

            era = supply.find_era_at(sess, bill.start_date)
            if era is None:
                eras = sess.query(Era).filter(
                    Era.supply == supply).order_by(Era.start_date).all()
                if bill.start_date < eras[0].start_date:
                    era = eras[0]
                else:
                    era = eras[-1]

            w.writerow(
                ('' if val is None else val) for val in [
                    hh_format(start_date), hh_format(finish_date), supply.id,
                    era.imp_mpan_core, era.exp_mpan_core, batch.reference,
                    bill.id, bill.reference, hh_format(bill.issue_date),
                    bill.bill_type.code, read.id,
                    'md' if read.tpr is None else read.tpr.code,
                    read.coefficient, hh_format(read.previous_date),
                    read.previous_value, read.previous_type.code,
                    hh_format(read.present_date), read.present_value,
                    read.present_type.code])

            # Avoid a long-running transaction
            sess.rollback()

    except BadRequest as e:
        w.writerow([e.description])
    except BaseException:
        msg = traceback.format_exc()
        f.write(msg)
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int('end_year')
    month = req_int('end_month')
    months = req_int('months')
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None
    args = (year, month, months, supply_id, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
