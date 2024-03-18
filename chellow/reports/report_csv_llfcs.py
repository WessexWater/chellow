import csv
import threading
import traceback

from flask import g

from sqlalchemy.orm import joinedload

from chellow.dloads import open_file
from chellow.models import Llfc, Session, User
from chellow.utils import hh_format
from chellow.views import chellow_redirect


def content(user_id):
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("llfcs.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(
                (
                    "Chellow Id",
                    "DNO Code",
                    "Code",
                    "Description",
                    "Voltage Level",
                    "Is Substation?",
                    "Is Import?",
                    "Valid From",
                    "Valid To",
                )
            )

            for llfc in (
                sess.query(Llfc)
                .order_by(Llfc.id)
                .options(joinedload(Llfc.dno), joinedload(Llfc.voltage_level))
            ):
                writer.writerow(
                    (
                        str(llfc.id),
                        llfc.dno.dno_code,
                        llfc.code,
                        llfc.description,
                        llfc.voltage_level.code,
                        llfc.is_substation,
                        llfc.is_import,
                        hh_format(llfc.valid_from),
                        hh_format(llfc.valid_to),
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
    return chellow_redirect("/downloads", 303)
