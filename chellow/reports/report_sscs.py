import sys
import threading
import traceback


from flask import g, redirect, request

import odio

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.models import MeasurementRequirement, Session, Ssc, Tpr, User
from chellow.utils import req_bool


def write_spreadsheet(
    fl,
    compressed,
    ssc_rows,
    mr_rows,
    tpr_rows,
):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, "1.2", compressed=compressed) as f:
        f.append_table("SSCs", ssc_rows)
        f.append_table("MRs", mr_rows)
        f.append_table("TPRs", tpr_rows)


def content(
    user_id,
    compression,
):
    sess = rf = None
    ssc_rows = [
        [
            "ssc_code",
            "ssc_description",
            "is_import",
            "valid_from",
            "valid_to",
        ]
    ]
    mr_rows = [["ssc_code", "tpr_code"]]
    tpr_rows = [["tpr_code", "is_teleswitch", "is_gmt"]]
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)

            rf = open_file("sscs.ods", user, "wb")

            for ssc in sess.scalars(select(Ssc).order_by(Ssc.code)):
                ssc_rows.append(
                    (
                        ssc.code,
                        ssc.description,
                        ssc.is_import,
                        ssc.valid_from,
                        ssc.valid_to,
                    )
                )
            for mr in sess.scalars(
                select(MeasurementRequirement)
                .join(Ssc)
                .join(Tpr)
                .order_by(Ssc.code, Tpr.code)
                .options(
                    joinedload(MeasurementRequirement.ssc),
                    joinedload(MeasurementRequirement.tpr),
                )
            ):
                mr_rows.append((mr.ssc.code, mr.tpr.code))
            for tpr in sess.scalars(select(Tpr).order_by(Tpr.code)):
                tpr_rows.append((tpr.code, tpr.is_teleswitch, tpr.is_gmt))

            write_spreadsheet(
                rf,
                compression,
                ssc_rows,
                mr_rows,
                tpr_rows,
            )
    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        ssc_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, ssc_rows, mr_rows, tpr_rows)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        ssc_rows.append(["Problem " + msg])
        if rf is None:
            msg = traceback.format_exc()
            ef = open_file("error.txt", None, "w")
            ef.write(msg + "\n")
            ef.close()
        else:
            write_spreadsheet(rf, compression, ssc_rows, mr_rows, tpr_rows)
    finally:
        if rf is not None:
            rf.close()


def do_get(sess):
    compression = req_bool("compression") if "compression" in request.values else True

    user = g.user

    args = (user.id, compression)
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
