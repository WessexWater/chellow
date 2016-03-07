from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
import pytz
from chellow.utils import HH
from flask import render_template


def do_get(sess):
    now = Datetime.now(pytz.utc)
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = month_start + relativedelta(months=1) - HH
    return render_template(
        'report_57.html', month_start=month_start, month_finish=month_finish)
