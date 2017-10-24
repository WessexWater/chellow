from datetime import datetime as Datetime
import datetime
import pytz
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
import traceback
from chellow.models import Snag, Site, Session
from chellow.views import chellow_redirect
import chellow.dloads
import csv
from flask import g
import threading
import sys
import os
from chellow.utils import hh_format


def content(user):
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'site_snags.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                'Chellow Id', 'Site Code', 'Site Name', 'Snag Description',
                'Start Date', 'Finish Date', 'Days Since Snag Finished',
                'Duration Of Snag (Days)', 'Is Ignored?'))

        now = Datetime.now(pytz.utc)

        for snag in sess.query(Snag).join(Site).filter(
                Snag.site != null()).order_by(
                Site.code, Snag.description, Snag.start_date,
                Snag.id).options(joinedload(Snag.site)):
            snag_start = snag.start_date
            snag_finish = snag.finish_date
            if snag_finish is None:
                duration = now - snag_start
                age_of_snag = datetime.timedelta(0)
            else:
                duration = snag_finish - snag_start
                age_of_snag = now - snag_finish

            writer.writerow(
                (
                    str(snag.id), snag.site.code, snag.site.name,
                    snag.description, hh_format(snag_start),
                    hh_format(snag_finish),
                    str(age_of_snag.days + age_of_snag.seconds / (3600 * 24)),
                    str(duration.days + duration.seconds / (3600 * 24)),
                    str(snag.is_ignored)))
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    args = (g.user,)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
