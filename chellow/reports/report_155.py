from datetime import datetime as Datetime

from dateutil.relativedelta import relativedelta

from flask import render_template


def do_get(sess):
    init = Datetime.utcnow()
    init = Datetime(init.year, init.month, 1) - relativedelta(months=1)
    return render_template("report_155.html", init=init)
