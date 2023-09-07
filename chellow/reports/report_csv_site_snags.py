import csv
import os
import sys
import threading
import traceback
from datetime import datetime as Datetime, timedelta as Timedelta

from flask import g

import pytz

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

import chellow.dloads
from chellow.models import Session, Site, Snag
from chellow.utils import hh_format
from chellow.views import chellow_redirect


def content(user):
    f = writer = None
    try:
        with Session() as sess:
            running_name, finished_name = chellow.dloads.make_names(
                "site_snags.csv", user
            )
            f = open(running_name, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(
                (
                    "Chellow Id",
                    "Site Code",
                    "Site Name",
                    "Snag Description",
                    "Start Date",
                    "Finish Date",
                    "Days Since Snag Finished",
                    "Duration Of Snag (Days)",
                    "Is Ignored?",
                )
            )

            now = Datetime.now(pytz.utc)

            for snag in (
                sess.query(Snag)
                .join(Site)
                .filter(Snag.site != null())
                .order_by(Site.code, Snag.description, Snag.start_date, Snag.id)
                .options(joinedload(Snag.site))
            ):
                snag_start = snag.start_date
                snag_finish = snag.finish_date
                if snag_finish is None:
                    duration = now - snag_start
                    age_of_snag = Timedelta(0)
                else:
                    duration = snag_finish - snag_start
                    age_of_snag = now - snag_finish

                writer.writerow(
                    (
                        str(snag.id),
                        snag.site.code,
                        snag.site.name,
                        snag.description,
                        hh_format(snag_start),
                        hh_format(snag_finish),
                        str(age_of_snag.days + age_of_snag.seconds / (3600 * 24)),
                        str(duration.days + duration.seconds / (3600 * 24)),
                        str(snag.is_ignored),
                    )
                )
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    args = (g.user,)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
