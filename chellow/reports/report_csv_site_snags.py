import csv
import threading
import traceback
from datetime import datetime as Datetime, timedelta as Timedelta

from flask import g, redirect

import pytz

from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from chellow.dloads import open_file
from chellow.models import Session, Site, Snag, User
from chellow.utils import hh_format


def content(user_id):
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("site_snags.csv", user, mode="w", newline="")
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
        print(msg)
        if writer is not None:
            writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    args = (g.user.id,)
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
